"""
Document Ingestion Service
Pipeline for document processing, chunking, embedding, and analysis.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.orm_models import Document, DocChunk, LoanApplication, IngestionJob, Verification, VerificationResult, KPI
from app.services.nlp import nlp_service
from app.services.rag import rag_service
from app.services.scoring import esg_scoring_engine
from app.services.glp_rules import glp_rules_engine
from app.utils.pdf_text import extract_text_from_file
from app.utils.faiss_index import get_index
from app.core.auth import log_audit_action

logger = logging.getLogger(__name__)


class IngestionService:
    """Handles document ingestion pipeline."""
    
    def run_ingestion(self, db: Session, loan_id: int) -> Dict[str, Any]:
        """Run full ingestion pipeline for a loan application."""
        start_time = time.time()
        
        # Create ingestion job
        job = IngestionJob(loan_id=loan_id, status="running", started_at=datetime.utcnow())
        db.add(job)
        db.commit()
        
        try:
            # Get loan application
            loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
            if not loan_app:
                raise ValueError(f"Loan application {loan_id} not found")
            
            # Get documents
            documents = db.query(Document).filter(Document.loan_id == loan_id).all()
            
            # Process each document
            total_chunks = 0
            combined_text = ""
            index = get_index(loan_id)
            index.clear()  # Clear existing index
            
            for doc in documents:
                # Extract text if not already done
                if not doc.text_extracted:
                    doc.text_extracted = extract_text_from_file(doc.filepath)
                    doc.extraction_status = "completed"
                    doc.processed_at = datetime.utcnow()
                
                if doc.text_extracted:
                    combined_text += f"\n\n{doc.text_extracted}"
                    
                    # Chunk the text
                    chunks = nlp_service.chunk_text(doc.text_extracted)
                    
                    # Create embeddings
                    chunk_texts = [c['chunk_text'] for c in chunks]
                    if chunk_texts:
                        embeddings = nlp_service.embed_texts(chunk_texts)
                        
                        # Prepare metadata
                        metadata = [{
                            'document_id': doc.id,
                            'chunk_index': c['chunk_index'],
                            'chunk_text': c['chunk_text'],
                            'start_char': c['start_char'],
                            'end_char': c['end_char']
                        } for c in chunks]
                        
                        # Add to FAISS index
                        index.add_embeddings(embeddings, metadata)
                        
                        # Store chunks in database
                        for i, c in enumerate(chunks):
                            chunk = DocChunk(
                                document_id=doc.id,
                                chunk_index=c['chunk_index'],
                                chunk_text=c['chunk_text'],
                                token_count=c['token_count'],
                                start_char=c['start_char'],
                                end_char=c['end_char'],
                                embedding_blob=embeddings[i].tobytes()
                            )
                            db.add(chunk)
                        
                        total_chunks += len(chunks)
            
            db.commit()
            
            # Run extraction questions
            extracted_fields = rag_service.run_extraction_questions(loan_id)
            
            # Get project data
            project_data = {
                'org_name': loan_app.borrower.org_name if loan_app.borrower else '',
                'project_name': loan_app.project_name,
                'sector': loan_app.sector,
                'location': loan_app.location,
                'use_of_proceeds': loan_app.use_of_proceeds,
                'scope1_tco2': loan_app.scope1_tco2,
                'scope2_tco2': loan_app.scope2_tco2,
                'scope3_tco2': loan_app.scope3_tco2,
                'baseline_year': loan_app.baseline_year,
                'document_count': len(documents),
                'amount_requested': loan_app.amount_requested,
            }
            
            # Build claims from extracted fields
            claims = [{'text': v.get('answer', ''), 'type': k, 'confidence': v.get('confidence', 0)} 
                     for k, v in extracted_fields.items() if v.get('answer')]
            evidence = [e for v in extracted_fields.values() for e in v.get('evidence', [])]
            
            # Calculate ESG score
            esg_result = esg_scoring_engine.calculate_composite_score(
                project_data, claims, evidence, combined_text
            )
            
            # Assess GLP eligibility
            glp_result = glp_rules_engine.assess_glp_eligibility(project_data, combined_text)
            
            # Assess carbon lock-in
            carbon_result = glp_rules_engine.assess_carbon_lockin(project_data, combined_text)
            
            # Assess DNSH
            dnsh_results = glp_rules_engine.assess_dnsh(project_data, combined_text)
            dnsh_summary = glp_rules_engine.get_dnsh_summary(dnsh_results)
            
            # Update loan application
            loan_app.esg_score = esg_result.total_score
            loan_app.glp_eligibility = glp_result.is_eligible
            loan_app.glp_category = glp_result.category
            loan_app.carbon_lockin_risk = carbon_result.risk_level.value
            loan_app.dnsh_status = dnsh_summary
            loan_app.total_tco2 = (loan_app.scope1_tco2 or 0) + (loan_app.scope2_tco2 or 0) + (loan_app.scope3_tco2 or 0)
            loan_app.parsed_fields = {
                'extracted': extracted_fields,
                'glp_category': glp_result.category,
                'esg_breakdown': esg_result.breakdown
            }
            loan_app.status = loan_app.status  # Keep current status
            
            # Create verification record
            verification = Verification(
                loan_id=loan_id,
                verification_type="automated_analysis",
                verifier_role="system",
                claim="Automated document analysis",
                result=VerificationResult.PASS if glp_result.is_eligible else VerificationResult.UNCLEAR,
                confidence=glp_result.confidence,
                evidence=evidence[:10],
                score=esg_result.total_score
            )
            db.add(verification)
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.documents_processed = len(documents)
            job.chunks_created = total_chunks
            job.summary = {
                'esg_score': esg_result.total_score,
                'glp_eligible': glp_result.is_eligible,
                'glp_category': glp_result.category,
                'carbon_risk': carbon_result.risk_level.value,
                'fields_extracted': len(extracted_fields)
            }
            
            db.commit()
            
            # Log audit
            log_audit_action(db, "LoanApplication", loan_id, "ingestion_completed", data=job.summary)
            
            processing_time = time.time() - start_time
            
            return {
                'job_id': job.id,
                'loan_id': loan_id,
                'status': 'completed',
                'documents_processed': len(documents),
                'chunks_created': total_chunks,
                'fields_extracted': extracted_fields,
                'esg_score': esg_result.total_score,
                'glp_category': glp_result.category,
                'glp_eligible': glp_result.is_eligible,
                'processing_time_seconds': round(processing_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
            raise


ingestion_service = IngestionService()
