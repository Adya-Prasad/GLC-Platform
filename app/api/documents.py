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
    Uses smart extraction for meaningful responses.
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
        
        # Get clean sentences from document
        sentences = esg_agent._get_clean_sentences(text)
        
        # Keyword mappings for extraction-type questions
        keyword_map = {
            "financial": ["revenue", "profit", "financial performance", "turnover", "income", "earnings", "growth"],
            "waste": ["waste management", "recycling", "waste reduction", "circular economy", "disposal"],
            "labor": ["employee", "workforce", "training", "safety", "diversity", "workplace"],
            "employee": ["employee", "workforce", "training", "safety", "diversity", "workplace"],
            "renewable": ["renewable energy", "solar", "wind", "clean energy", "green energy"],
            "energy": ["renewable energy", "solar", "wind", "energy efficiency", "power"],
            "environment": ["environmental", "pollution", "emission", "climate", "biodiversity"],
            "emission": ["emission", "carbon", "co2", "greenhouse", "ghg", "scope"],
            "carbon": ["carbon", "emission", "co2", "greenhouse", "climate action"],
            "sustainability": ["sustainability", "sustainable", "esg", "environmental"],
        }
        
        # Find matching keywords
        matched_keywords = []
        for trigger, keywords in keyword_map.items():
            if trigger in message_lower:
                matched_keywords.extend(keywords)
        
        # If no specific keywords matched, use words from the question
        if not matched_keywords:
            matched_keywords = [w for w in message_lower.split() if len(w) > 4][:5]
        
        if matched_keywords:
            response = esg_agent._extract_meaningful_content(sentences, matched_keywords, max_sentences=3)
            
            if "not found" not in response.lower():
                return ChatResponse(
                    response=response,
                    confidence=0.8,
                    sources=[{"text_snippet": response[:200], "source": doc_source, "score": 0.8}]
                )
        
        # Fallback to QA model
        esg_agent._ensure_models()
        context = esg_agent._clean_text(text)[:4000]
        
        result = esg_agent._extractor(
            question=request.message,
            context=context
        )
        
        if result['score'] > 0.2:
            return ChatResponse(
                response=result['answer'],
                confidence=float(result['score']),
                sources=[{"text_snippet": context[:200], "source": doc_source, "score": result['score']}]
            )
        
        return ChatResponse(
            response="I couldn't find specific information about that in the sustainability report. Try asking about emissions, renewable energy, sustainability targets, or employee practices.",
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
        
        # Generate PDF using ReportLab (no system dependencies)
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, 
                                   rightMargin=1.5*cm, leftMargin=1.5*cm,
                                   topMargin=1.5*cm, bottomMargin=1.5*cm)
            
            # Styles
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='Title2', fontSize=20, textColor=colors.HexColor('#367a23'), 
                                     spaceAfter=12, fontName='Helvetica-Bold'))
            styles.add(ParagraphStyle(name='Subtitle', fontSize=12, textColor=colors.HexColor('#64748b'),
                                     spaceAfter=20))
            styles.add(ParagraphStyle(name='SectionTitle', fontSize=14, textColor=colors.HexColor('#367a23'),
                                     fontName='Helvetica-Bold', spaceAfter=10, spaceBefore=15))
            styles.add(ParagraphStyle(name='BodyText2', fontSize=10, textColor=colors.HexColor('#374151'),
                                     spaceAfter=8, leading=14))
            styles.add(ParagraphStyle(name='Question', fontSize=11, textColor=colors.HexColor('#367a23'),
                                     fontName='Helvetica-Bold', spaceAfter=6))
            styles.add(ParagraphStyle(name='Answer', fontSize=10, textColor=colors.HexColor('#475569'),
                                     spaceAfter=12, leading=14, leftIndent=10))
            styles.add(ParagraphStyle(name='Footer', fontSize=8, textColor=colors.HexColor('#94a3b8'),
                                     alignment=TA_CENTER))
            
            # Build content
            story = []
            
            # Header
            story.append(Paragraph("🌿 GLC Platform", styles['Title2']))
            story.append(Paragraph("AI Retrieval Insights Report", styles['Subtitle']))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#367a23')))
            story.append(Spacer(1, 0.3*inch))
            
            # Metadata table
            project_name = loan_app.project_name or "N/A"
            org_name = loan_app.org_name or "N/A"
            loan_amount = f"${loan_app.amount_requested:,.2f}" if loan_app.amount_requested else "N/A"
            loan_id_str = f"LOAN_{loan_app.id}"
            confidence = f"{analysis.get('confidence', 0) * 100:.0f}%"
            pages = str(analysis.get('pages_analyzed', 0))
            
            meta_data = [
                ['Loan ID', loan_id_str, 'Project', project_name],
                ['Organization', org_name, 'Loan Amount', loan_amount],
                ['Confidence', confidence, 'Pages Analyzed', pages],
            ]
            meta_table = Table(meta_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
            meta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
                ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f1f5f9')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('PADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Executive Summary
            if analysis.get('summary'):
                story.append(Paragraph("📄 Executive Summary", styles['SectionTitle']))
                story.append(Paragraph(analysis['summary'], styles['BodyText2']))
                story.append(Spacer(1, 0.2*inch))
            
            # Essential Points
            if analysis.get('essential_points'):
                story.append(Paragraph("💡 Key Findings", styles['SectionTitle']))
                for point in analysis['essential_points']:
                    importance = point.get('importance', 'medium').upper()
                    title = point.get('title', '')
                    desc = point.get('description', '')
                    story.append(Paragraph(f"<b>[{importance}] {title}</b>", styles['BodyText2']))
                    story.append(Paragraph(desc, styles['Answer']))
                story.append(Spacer(1, 0.2*inch))
            
            # Quantitative Data
            if analysis.get('quantitative_data'):
                story.append(Paragraph("📊 Extracted Metrics", styles['SectionTitle']))
                quant_data = [['Metric', 'Value', 'Category']]
                for q in analysis['quantitative_data']:
                    quant_data.append([q.get('metric', ''), f"{q.get('value', '')} {q.get('unit', '')}", q.get('category', '')])
                quant_table = Table(quant_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
                quant_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ffe3')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0d7811')),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('PADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ]))
                story.append(quant_table)
                story.append(Spacer(1, 0.2*inch))
            
            # LMA Framework Questions
            if analysis.get('extraction_answers'):
                story.append(Paragraph("📋 LMA Framework Analysis", styles['SectionTitle']))
                for question, answer in analysis['extraction_answers'].items():
                    story.append(Paragraph(f"❓ {question}", styles['Question']))
                    story.append(Paragraph(answer, styles['Answer']))
                story.append(Spacer(1, 0.2*inch))
            
            # Footer
            story.append(Spacer(1, 0.3*inch))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"Generated by GLC Platform AI Agent | {datetime.now().strftime('%Y-%m-%d %H:%M')} | Confidence: {confidence}", styles['Footer']))
            
            # Build PDF
            doc.build(story)
            logger.info(f"AI report PDF saved to {pdf_path}")
            
        except ImportError as e:
            logger.error(f"ReportLab not available: {e}")
            # Fallback: save as HTML
            html_content = _build_ai_report_html(loan_app, analysis)
            html_path = loan_dir / "ai_retrieval_insights.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return {"success": True, "message": "Report saved as HTML (install reportlab for PDF)", "path": str(html_path)}
        
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
