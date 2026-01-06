"""
Admin API Endpoints
Endpoints for ingestion, reports, audit logs, and external review.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import zipfile
import json
from pathlib import Path

from app.models.db import get_db
from app.models.orm_models import User, LoanApplication, AuditLog, Document
from app.models.schemas import AuditLogResponse, IngestionSummary, GlpReportData
from app.core.auth import get_current_user, MockAuth
from app.core.config import settings
from app.services.ingestion import ingestion_service
from app.services.report import report_service

router = APIRouter(tags=["Admin"])


@router.post("/ingest/run/{loan_id}", response_model=IngestionSummary)
async def run_ingestion(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger document ingestion and analysis for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    try:
        result = ingestion_service.run_ingestion(db, loan_id)
        return IngestionSummary(
            job_id=result['job_id'],
            loan_id=loan_id,
            status=result['status'],
            documents_processed=result['documents_processed'],
            chunks_created=result['chunks_created'],
            fields_extracted=result['fields_extracted'],
            esg_score=result['esg_score'],
            glp_category=result['glp_category'],
            processing_time_seconds=result['processing_time_seconds']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/application/{loan_id}")
async def get_report(
    loan_id: int,
    format: str = Query("json", description="Output format: json or pdf"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate GLP investor report for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    try:
        report_data = report_service.generate_report(db, loan_id, format)
        
        if format == "pdf" and "pdf_url" in report_data:
            pdf_path = Path(report_data["pdf_url"])
            if pdf_path.exists():
                return FileResponse(
                    path=str(pdf_path),
                    filename=pdf_path.name,
                    media_type="application/pdf"
                )
        
        return report_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/external_review/{loan_id}/request")
async def request_external_review(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate external review package (ZIP with documents and analysis)."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Generate report
    report_data = report_service.generate_report(db, loan_id, "json")
    
    # Create ZIP package
    package_dir = settings.REPORTS_DIR / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    zip_filename = f"external_review_{loan_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = package_dir / zip_filename
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add report JSON
        zipf.writestr("report.json", json.dumps(report_data, indent=2, default=str))
        
        # Add documents
        documents = db.query(Document).filter(Document.loan_id == loan_id).all()
        for doc in documents:
            if Path(doc.filepath).exists():
                zipf.write(doc.filepath, f"documents/{doc.filename}")
        
        # Add audit logs
        logs = db.query(AuditLog).filter(
            AuditLog.entity_type == "LoanApplication",
            AuditLog.entity_id == loan_id
        ).all()
        log_data = [{"action": l.action, "timestamp": l.timestamp.isoformat(), "data": l.data} for l in logs]
        zipf.writestr("audit_log.json", json.dumps(log_data, indent=2))
    
    return {
        "loan_id": loan_id,
        "package_url": f"/downloads/{zip_filename}",
        "generated_at": datetime.utcnow().isoformat(),
        "contents": ["report.json", f"{len(documents)} documents", "audit_log.json"]
    }


@router.get("/audit/{loan_id}", response_model=List[AuditLogResponse])
async def get_audit_logs(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "LoanApplication",
        AuditLog.entity_id == loan_id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return logs


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_all_audit_logs(
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all audit logs."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return logs


# ==================== Docs & Learn Endpoints ====================

@router.get("/docs/list")
async def list_docs():
    """List available documentation files."""
    docs_dir = Path("user-docs")
    if not docs_dir.exists():
        return []
    return [f.name for f in docs_dir.glob("*.md")]


@router.get("/docs/content/{filename}")
async def get_doc_content(filename: str):
    """Get content of a documentation file."""
    doc_path = Path("user-docs") / filename
    if not doc_path.exists() or not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"content": doc_path.read_text(encoding="utf-8")}


@router.get("/learn/list")
async def list_learn_files():
    """List available learning materials."""
    learn_dir = Path("user-learn")
    if not learn_dir.exists():
        return []
    files = []
    for f in learn_dir.glob("*"):
        if f.is_file():
            files.append({
                "name": f.name,
                "type": "pdf" if f.suffix.lower() == ".pdf" else "md" if f.suffix.lower() == ".md" else "file",
                "size": f.stat().st_size
            })
    return files


@router.get("/learn/content/{filename}")
async def get_learn_content(filename: str):
    """Get the file or content for learning."""
    learn_path = Path("user-learn") / filename
    if not learn_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if filename.endswith(".md"):
        return {"content": learn_path.read_text(encoding="utf-8")}
    elif filename.endswith(".pdf"):
        return FileResponse(path=str(learn_path), media_type="application/pdf", filename=filename)
    else:
        return FileResponse(path=str(learn_path), filename=filename)
