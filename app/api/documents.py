# app/api/documents.py

import logging
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.ai_services.config import settings
from app.ai_services.embedding import embedding_service
from app.ai_services.rag import rag_service
from app.ai_services.document_processor import document_processor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


class ChatRequest(BaseModel):
    message: str
    loan_id: int


class ChatResponse(BaseModel):
    response: str
    confidence: float
    sources: List[dict]


class QueryRequest(BaseModel):
    question: str
    loan_id: int
    doc_type: Optional[str] = None


@router.post("/process/{loan_id}")
async def process_document(
    loan_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Process and index a document for a loan application.
    """
    valid_types = [
        "sustainability_report", "annual_report", "project_description",
        "use_of_proceeds", "env_impact_assessment"
    ]
    if doc_type not in valid_types:
        raise HTTPException(400, f"Invalid doc_type. Must be one of: {valid_types}")
    
    filename = file.filename or "document"
    ext = Path(filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".doc", ".txt"]:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use PDF, DOCX, or TXT.")
    
    try:
        # Save file
        loan_dir = settings.UPLOAD_DIR / f"LOAN_{loan_id}"
        loan_dir.mkdir(exist_ok=True, parents=True)
        file_path = loan_dir / filename
        
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Process document
        processed = document_processor.process_document(str(file_path), doc_type)
        if not processed:
            raise HTTPException(500, "Failed to extract text from document")
        
        # Convert chunks to format expected by embedding service
        chunks_for_embedding = []
        for chunk in processed.chunks:
            # Create a simple object with page_content and metadata
            class ChunkWrapper:
                def __init__(self, text, metadata):
                    self.page_content = text
                    self.metadata = metadata
            
            chunks_for_embedding.append(ChunkWrapper(
                chunk.text,
                {
                    "source": chunk.source_file,
                    "doc_type": chunk.doc_type,
                    "page": chunk.page_number
                }
            ))
        
        # Index chunks
        chunks_added = embedding_service.add_chunks(chunks_for_embedding, loan_id)
        
        return {
            "success": True,
            "filename": processed.filename,
            "doc_type": doc_type,
            "pages": processed.page_count,
            "words": processed.word_count,
            "chunks_indexed": chunks_added,
            "extraction_method": processed.extraction_method
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """
    Chat interface for document Q&A.
    """
    try:
        result = rag_service.chat(request.message, request.loan_id)
        return ChatResponse(
            response=result["answer"],
            confidence=float(result["confidence"]),
            sources=result["sources"]
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(500, f"Chat failed: {str(e)}")


@router.post("/query")
async def query_documents(request: QueryRequest):
    """
    Query documents with a specific question.
    """
    try:
        response = rag_service.query(
            question=request.question,
            loan_id=request.loan_id,
            doc_type=request.doc_type
        )
        return response
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(500, f"Query failed: {str(e)}")


@router.get("/extract/{loan_id}")
async def extract_answers(loan_id: int):
    """
    Extract answers to standard LMA questions from documents.
    """
    try:
        results = rag_service.extract_all_questions(loan_id)
        return {
            "loan_id": loan_id,
            "extractions": results
        }
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        raise HTTPException(500, f"Extraction failed: {str(e)}")


@router.get("/analyze/{loan_id}")
async def analyze_documents(loan_id: int, auto_index: bool = True):
    """
    Perform document analysis - auto-indexes documents if needed.
    """
    try:
        # Check current stats
        stats = embedding_service.get_stats(loan_id)
        
        # Auto-index documents if none indexed yet
        if auto_index and stats.get('chunk_count', 0) == 0:
            indexed = await _auto_index_loan_documents(loan_id)
            if indexed > 0:
                stats = embedding_service.get_stats(loan_id)
        
        chunk_count = stats.get('chunk_count', 0)
        
        if chunk_count == 0:
            return {
                "loan_id": loan_id,
                "quantitative_data": [],
                "qualitative_data": [],
                "essential_points": [],
                "extraction_answers": {},
                "glp_coverage": {},
                "sllp_coverage": {},
                "summary": "No documents found. Please upload sustainability reports or annual reports."
            }
        
        # Get extraction results
        extractions = rag_service.extract_all_questions(loan_id)
        
        # Build extraction answers dict - only include found answers
        extraction_answers = {}
        essential_points = []
        found_count = 0
        
        for ext in extractions:
            extraction_answers[ext["question"]] = ext["answer"]
            
            if ext["found"] and ext["confidence"] > 0.3:
                found_count += 1
                # Truncate long answers for display
                desc = ext["answer"]
                if len(desc) > 150:
                    desc = desc[:147] + "..."
                
                essential_points.append({
                    "title": ext["question"].replace("?", "").replace("What is the ", "").replace("What are the ", "").title(),
                    "description": desc,
                    "importance": "high" if ext["confidence"] > 0.6 else "medium",
                    "category": "compliance"
                })
        
        # Generate summary
        if found_count > 0:
            summary = f"Analyzed {chunk_count} document chunks. Found answers to {found_count}/{len(extractions)} LMA framework questions."
        else:
            summary = f"Analyzed {chunk_count} document chunks. Could not extract clear answers - documents may not contain relevant ESG/sustainability information."
        
        return {
            "loan_id": loan_id,
            "quantitative_data": [],
            "qualitative_data": [],
            "essential_points": essential_points,
            "extraction_answers": extraction_answers,
            "glp_coverage": {},
            "sllp_coverage": {},
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


async def _auto_index_loan_documents(loan_id: int) -> int:
    """
    Auto-index sustainability_report from loan folder.
    Only uses sustainability reports for more focused AI analysis.
    Returns number of chunks indexed.
    """
    loan_dir = settings.UPLOAD_DIR / f"LOAN_{loan_id}"
    if not loan_dir.exists():
        return 0
    
    total_chunks = 0
    # Only index sustainability reports for focused analysis
    doc_mappings = {
        "sustainability_report.pdf": "sustainability_report",
        "sustainability_report.docx": "sustainability_report",
    }
    
    for filename, doc_type in doc_mappings.items():
        file_path = loan_dir / filename
        if file_path.exists():
            try:
                logger.info(f"Auto-indexing {filename} for loan {loan_id}")
                processed = document_processor.process_document(str(file_path), doc_type)
                
                if processed and processed.chunks:
                    # Convert chunks
                    chunks_for_embedding = []
                    for chunk in processed.chunks:
                        class ChunkWrapper:
                            def __init__(self, text, metadata):
                                self.page_content = text
                                self.metadata = metadata
                        
                        chunks_for_embedding.append(ChunkWrapper(
                            chunk.text,
                            {"source": chunk.source_file, "doc_type": chunk.doc_type, "page": chunk.page_number}
                        ))
                    
                    added = embedding_service.add_chunks(chunks_for_embedding, loan_id)
                    total_chunks += added
                    logger.info(f"Indexed {added} chunks from {filename}")
            except Exception as e:
                logger.error(f"Failed to index {filename}: {e}")
    
    return total_chunks


@router.post("/index/{loan_id}")
async def index_loan_documents(loan_id: int):
    """
    Manually trigger indexing of all documents in loan folder.
    """
    try:
        # Clear existing index first
        embedding_service.clear_loan(loan_id)
        
        # Index documents
        chunks_indexed = await _auto_index_loan_documents(loan_id)
        
        return {
            "success": True,
            "loan_id": loan_id,
            "chunks_indexed": chunks_indexed
        }
    except Exception as e:
        logger.error(f"Index error: {e}")
        raise HTTPException(500, f"Indexing failed: {str(e)}")


@router.get("/stats/{loan_id}")
async def get_document_stats(loan_id: int):
    """
    Get indexing statistics for a loan's documents.
    """
    try:
        return embedding_service.get_stats(loan_id)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(500, f"Stats failed: {str(e)}")


@router.delete("/clear/{loan_id}")
async def clear_loan_index(loan_id: int):
    """
    Clear all indexed documents for a loan.
    """
    try:
        removed = embedding_service.clear_loan(loan_id)
        return {
            "success": True,
            "loan_id": loan_id,
            "chunks_removed": removed
        }
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(500, f"Clear failed: {str(e)}")
