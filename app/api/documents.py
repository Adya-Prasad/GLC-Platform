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
