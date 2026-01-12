"""
Documents API - Simplified ESG Document Analysis
Uses lightweight ESG agent for document processing.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai_services.esg_agent import analyze_documents, esg_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


class ChatRequest(BaseModel):
    message: str
    loan_id: int


class ChatResponse(BaseModel):
    response: str
    confidence: float
    sources: List[dict]


@router.get("/analyze/{loan_id}")
async def analyze_loan_documents(loan_id: int):
    """
    Analyze sustainability documents for a loan application.
    Extracts ESG metrics, generates summary, and identifies key points.
    """
    try:
        logger.info(f"Starting document analysis for loan {loan_id}")
        result = analyze_documents(loan_id)
        logger.info(f"Analysis complete for loan {loan_id}")
        return result
    except Exception as e:
        logger.error(f"Analysis failed for loan {loan_id}: {e}")
        raise HTTPException(500, f"Document analysis failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_documents(request: ChatRequest):
    """
    Smart Q&A about loan documents.
    Uses keyword extraction for extraction questions, QA model for specific questions.
    """
    try:
        from app.ai_services.config import settings
        
        loan_dir = settings.UPLOAD_DIR / f"LOAN_{request.loan_id}"
        
        if not loan_dir.exists():
            return ChatResponse(
                response="No documents found for this loan.",
                confidence=0.0,
                sources=[]
            )
        
        # Only use sustainability report
        doc_files = ["sustainability_report.pdf", "sustainability_report.docx"]
        text = ""
        doc_source = ""
        
        for doc_name in doc_files:
            doc_path = loan_dir / doc_name
            if doc_path.exists():
                if doc_name.endswith('.pdf'):
                    text, _ = esg_agent._extract_text_from_pdf(str(doc_path))
                else:
                    text, _ = esg_agent._extract_text_from_docx(str(doc_path))
                doc_source = doc_name
                break
        
        if not text:
            return ChatResponse(
                response="Could not read document content.",
                confidence=0.0,
                sources=[]
            )
        
        message_lower = request.message.lower()
        
        # Keyword mappings for extraction-type questions
        extraction_keywords = {
            "financial": ["revenue", "profit", "financial", "turnover", "income", "earnings", "growth", "fiscal", "million", "billion", "sales", "operating", "assets", "capital", "investment"],
            "waste": ["waste", "recycling", "circular", "disposal", "landfill", "reuse", "reduce", "recycle", "hazardous", "e-waste", "plastic"],
            "labor": ["employee", "workforce", "staff", "labor", "workers", "training", "safety", "diversity", "inclusion", "human resources", "workplace", "occupational", "talent", "hiring"],
            "employee": ["employee", "workforce", "staff", "labor", "workers", "training", "safety", "diversity", "inclusion", "human resources", "workplace", "occupational", "talent", "hiring"],
            "renewable": ["renewable", "solar", "wind", "clean energy", "green energy", "hydro", "biomass", "energy efficiency", "carbon neutral", "net zero", "photovoltaic", "decarbonization"],
            "energy": ["renewable", "solar", "wind", "clean energy", "green energy", "hydro", "biomass", "energy efficiency", "power", "electricity", "kwh", "mwh"],
            "environment": ["environment", "pollution", "emission", "carbon", "climate", "biodiversity", "conservation", "sustainability", "eco", "green", "ghg", "co2", "greenhouse"],
            "pollution": ["pollution", "emission", "carbon", "climate", "air quality", "water quality", "contamination", "effluent", "discharge"],
            "emission": ["emission", "carbon", "co2", "greenhouse", "ghg", "scope 1", "scope 2", "scope 3", "tco2"],
            "carbon": ["carbon", "emission", "co2", "greenhouse", "ghg", "footprint", "neutral", "offset"],
            "water": ["water", "wastewater", "conservation", "effluent", "discharge", "consumption", "recycled water"],
            "sustainability": ["sustainability", "sustainable", "esg", "environmental", "social", "governance", "green", "responsible"],
        }
        
        # Check if this is an extraction-type question
        matched_keywords = []
        for trigger, keywords in extraction_keywords.items():
            if trigger in message_lower:
                matched_keywords.extend(keywords)
        
        if matched_keywords:
            # Use keyword extraction (same as LMA Framework Questions)
            extracted = esg_agent._extract_section(text, list(set(matched_keywords)), max_length=1500)
            
            if "not clearly stated" not in extracted.lower():
                return ChatResponse(
                    response=extracted,
                    confidence=0.85,
                    sources=[{"text_snippet": extracted[:300], "source": doc_source, "score": 0.85}]
                )
        
        # Fallback to QA model for specific questions
        esg_agent._ensure_models()
        context = text[:5000]  # Increased context
        
        result = esg_agent._extractor(
            question=request.message,
            context=context
        )
        
        if result['score'] > 0.15:
            return ChatResponse(
                response=result['answer'],
                confidence=float(result['score']),
                sources=[{"text_snippet": context[:200], "source": doc_source, "score": result['score']}]
            )
        
        # If QA fails, try broader keyword search from the question itself
        question_words = [w for w in message_lower.split() if len(w) > 3]
        if question_words:
            extracted = esg_agent._extract_section(text, question_words[:5], max_length=1000)
            if "not clearly stated" not in extracted.lower():
                return ChatResponse(
                    response=extracted,
                    confidence=0.6,
                    sources=[{"text_snippet": extracted[:300], "source": doc_source, "score": 0.6}]
                )
        
        return ChatResponse(
            response="I couldn't find specific information about that in the sustainability report. Try asking about financial performance, emissions, renewable energy, waste management, or employee practices.",
            confidence=0.0,
            sources=[]
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return ChatResponse(
            response=f"Error processing question: {str(e)}",
            confidence=0.0,
            sources=[]
        )


@router.get("/stats/{loan_id}")
async def get_document_stats(loan_id: int):
    """Get basic stats about loan documents."""
    from app.ai_services.config import settings
    
    loan_dir = settings.UPLOAD_DIR / f"LOAN_{loan_id}"
    
    if not loan_dir.exists():
        return {"loan_id": loan_id, "documents_found": 0, "status": "no_directory"}
    
    doc_count = 0
    docs = []
    
    for f in loan_dir.iterdir():
        if f.suffix.lower() in ['.pdf', '.docx', '.doc']:
            doc_count += 1
            docs.append(f.name)
    
    return {
        "loan_id": loan_id,
        "documents_found": doc_count,
        "documents": docs,
        "status": "ready" if doc_count > 0 else "no_documents"
    }


@router.post("/save-ai-report/{loan_id}")
async def save_ai_report(loan_id: int):
    """
    Generate and save AI Retrieval Insights as PDF.
    Saves to loan_assets/LOAN_{id}/ai_retrieval_insights.pdf
    """
    from app.ai_services.config import settings
    from dbms.db import get_db
    from dbms.orm_models import LoanApplication, Document
    from datetime import datetime
    
    try:
        # Get loan application data
        db = next(get_db())
        loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
        
        if not loan_app:
            return {"success": False, "message": "Loan application not found"}
        
        # Get AI analysis
        analysis = analyze_documents(loan_id)
        
        if not analysis or analysis.get('confidence', 0) == 0:
            return {"success": False, "message": "No AI analysis available. Please run AI Agent first."}
        
        # Generate PDF
        loan_dir = settings.UPLOAD_DIR / f"LOAN_{loan_id}"
        loan_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = loan_dir / "ai_retrieval_insights.pdf"
        
        # Build HTML content for PDF
        html_content = _build_ai_report_html(loan_app, analysis)
        
        # Generate PDF using WeasyPrint
        try:
            from weasyprint import HTML, CSS
            
            css = CSS(string='''
                @page { size: A4; margin: 1.5cm; }
                body { font-family: Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #333; }
                .header { background: linear-gradient(135deg, #4f46e5, #2563eb); color: white; padding: 20px; margin: -1.5cm -1.5cm 20px -1.5cm; }
                .header h1 { margin: 0; font-size: 24pt; }
                .header p { margin: 5px 0 0 0; opacity: 0.9; }
                .meta-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
                .meta-grid { display: flex; flex-wrap: wrap; gap: 20px; }
                .meta-item { flex: 1; min-width: 150px; }
                .meta-label { font-size: 9pt; color: #64748b; text-transform: uppercase; }
                .meta-value { font-size: 12pt; font-weight: bold; color: #1e293b; }
                .section { margin-bottom: 25px; page-break-inside: avoid; }
                .section-title { font-size: 14pt; font-weight: bold; color: #4f46e5; border-bottom: 2px solid #4f46e5; padding-bottom: 5px; margin-bottom: 15px; }
                .point-card { background: #fefce8; border-left: 4px solid #eab308; padding: 10px 15px; margin-bottom: 10px; }
                .point-critical { background: #fef2f2; border-left-color: #ef4444; }
                .point-high { background: #fffbeb; border-left-color: #f59e0b; }
                .point-medium { background: #f0fdf4; border-left-color: #22c55e; }
                .point-title { font-weight: bold; color: #1e293b; }
                .point-desc { font-size: 10pt; color: #475569; margin-top: 5px; }
                .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 8pt; font-weight: bold; }
                .badge-critical { background: #fee2e2; color: #dc2626; }
                .badge-high { background: #fef3c7; color: #d97706; }
                .badge-medium { background: #dcfce7; color: #16a34a; }
                .qa-item { background: #f1f5f9; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
                .qa-question { font-weight: bold; color: #1e293b; margin-bottom: 8px; }
                .qa-answer { color: #475569; font-size: 10pt; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }
                th { background: #f1f5f9; font-weight: bold; color: #475569; }
                .footer { margin-top: 30px; padding-top: 15px; border-top: 1px solid #e2e8f0; font-size: 9pt; color: #94a3b8; text-align: center; }
            ''')
            
            HTML(string=html_content).write_pdf(str(pdf_path), stylesheets=[css])
            logger.info(f"AI report PDF saved to {pdf_path}")
            
        except ImportError:
            # Fallback: save as HTML if WeasyPrint not available
            html_path = loan_dir / "ai_retrieval_insights.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.warning("WeasyPrint not available, saved as HTML instead")
            return {"success": True, "message": "Report saved as HTML (PDF generation requires WeasyPrint)", "path": str(html_path)}
        
        # Register document in database
        existing_doc = db.query(Document).filter(
            Document.loan_id == loan_id,
            Document.filename == "ai_retrieval_insights.pdf"
        ).first()
        
        if existing_doc:
            existing_doc.uploaded_at = datetime.utcnow()
        else:
            # Get a lender user for uploader_id
            from dbms.orm_models import User, UserRole
            lender_user = db.query(User).filter(User.role == UserRole.LENDER).first()
            uploader_id = lender_user.id if lender_user else 1
            
            new_doc = Document(
                loan_id=loan_id,
                uploader_id=uploader_id,
                filename="ai_retrieval_insights.pdf",
                filepath=str(pdf_path),
                file_type="ai_report",
                doc_category="ai_generated",
                uploaded_at=datetime.utcnow()
            )
            db.add(new_doc)
        
        db.commit()
        
        return {"success": True, "message": "AI Retrieval Insights report saved successfully", "path": str(pdf_path)}
        
    except Exception as e:
        logger.error(f"Failed to save AI report: {e}")
        return {"success": False, "message": str(e)}


def _build_ai_report_html(loan_app, analysis) -> str:
    """Build HTML content for AI report PDF."""
    from datetime import datetime
    
    # Get loan details
    project_name = loan_app.project_name or "N/A"
    org_name = loan_app.org_name or "N/A"
    loan_amount = f"${loan_app.amount_requested:,.2f}" if loan_app.amount_requested else "N/A"
    loan_id = f"LOAN_{loan_app.id}"
    
    # Essential points HTML
    essential_points_html = ""
    for point in analysis.get('essential_points', []):
        importance = point.get('importance', 'medium')
        essential_points_html += f'''
            <div class="point-card point-{importance}">
                <span class="badge badge-{importance}">{importance.upper()}</span>
                <span class="point-title">{point.get('title', '')}</span>
                <div class="point-desc">{point.get('description', '')}</div>
            </div>
        '''
    
    # Quantitative data table
    quant_rows = ""
    for q in analysis.get('quantitative_data', []):
        quant_rows += f'''
            <tr>
                <td>{q.get('metric', '')}</td>
                <td><strong>{q.get('value', '')} {q.get('unit', '')}</strong></td>
                <td>{q.get('category', '')}</td>
            </tr>
        '''
    
    quant_table = f'''
        <table>
            <thead><tr><th>Metric</th><th>Value</th><th>Category</th></tr></thead>
            <tbody>{quant_rows if quant_rows else '<tr><td colspan="3">No quantitative data extracted</td></tr>'}</tbody>
        </table>
    ''' if analysis.get('quantitative_data') else '<p>No quantitative data extracted from documents.</p>'
    
    # LMA Framework Questions
    qa_html = ""
    for question, answer in analysis.get('extraction_answers', {}).items():
        qa_html += f'''
            <div class="qa-item">
                <div class="qa-question">📋 {question}</div>
                <div class="qa-answer">{answer}</div>
            </div>
        '''
    
    # Summary
    summary = analysis.get('summary', 'No summary available.')
    confidence = analysis.get('confidence', 0) * 100
    pages = analysis.get('pages_analyzed', 0)
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><title>AI Retrieval Insights - {loan_id}</title></head>
    <body>
        <div class="header">
            <h1>🌿 GLC Platform</h1>
            <p>AI Retrieval Insights Report</p>
        </div>
        
        <div class="meta-box">
            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">Loan ID</div>
                    <div class="meta-value">{loan_id}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Project</div>
                    <div class="meta-value">{project_name}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Organization</div>
                    <div class="meta-value">{org_name}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Loan Amount</div>
                    <div class="meta-value">{loan_amount}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Analysis Confidence</div>
                    <div class="meta-value">{confidence:.0f}%</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Pages Analyzed</div>
                    <div class="meta-value">{pages}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📊 Executive Summary</div>
            <p>{summary}</p>
        </div>
        
        <div class="section">
            <div class="section-title">💡 Essential Points</div>
            {essential_points_html if essential_points_html else '<p>No essential points identified.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title">📈 Quantitative Data</div>
            {quant_table}
        </div>
        
        <div class="section">
            <div class="section-title">📋 LMA Framework Questions</div>
            {qa_html if qa_html else '<p>No extraction answers available.</p>'}
        </div>
        
        <div class="footer">
            <p>Generated by GLC Platform AI Agent | {datetime.now().strftime('%Y-%m-%d %H:%M')} | Confidence: {confidence:.0f}%</p>
            <p>This report is auto-generated from sustainability documents using AI-powered extraction.</p>
        </div>
    </body>
    </html>
    '''
    
    return html
