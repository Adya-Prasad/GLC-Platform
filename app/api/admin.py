"""
Admin API Endpoints
Endpoints for ingestion, reports, audit logs, and external review.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import zipfile
import json
from pathlib import Path

from dbms.db import get_db, SessionLocal
from dbms.orm_models import User, LoanApplication, AuditLog, Document, IngestionJob
from dbms.schemas import AuditLogResponse, IngestionSummary, GlpReportData
from app.operations.auth import get_current_user, MockAuth, log_audit_action
from app.ai_services.config import settings
from app.utils.storage import get_loan_dir
from app.ai_services.ingestion import ingestion_service
# from app.ai_services.report import report_service

router = APIRouter(tags=["Admin"])


@router.post("/ingest/run/{loan_id}", response_model=IngestionSummary)
async def run_ingestion(
    loan_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger document ingestion and analysis for a loan application (non-blocking).

    This endpoint creates a queued IngestionJob and schedules the ingestion to run in the background
    using a fresh DB session to avoid using the request-scoped session after the request completes.
    """
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")

    # Create queued ingestion job record immediately
    job = IngestionJob(loan_id=loan_id, status="queued", started_at=None)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Schedule background task using a helper that opens its own DB session
    background_tasks.add_task(ingestion_service.start_ingestion_async, job.id)

    # Audit log entry
    log_audit_action(db, "LoanApplication", loan_id, "ingestion_queued", current_user.id, data={"job_id": job.id})

    return IngestionSummary(
        job_id=job.id,
        loan_id=loan_id,
        status=job.status,
        documents_processed=0,
        chunks_created=0,
        fields_extracted={},
        esg_score=None,
        glp_category=None,
        processing_time_seconds=0.0
    )


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
    
    # Create ZIP package inside the loan's folder
    loan_dir = get_loan_dir(loan_app.loan_id)
    
    zip_filename = f"external_review_{loan_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = loan_dir / zip_filename
    
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
        "package_url": f"/downloads/{loan_app.loan_id}/{zip_filename}",
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


@router.get("/ingest/job/{job_id}")
async def get_ingestion_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ingestion job status and details."""
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")

    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")

    return {
        "job_id": job.id,
        "loan_id": job.loan_id,
        "status": job.status,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "documents_processed": job.documents_processed,
        "chunks_created": job.chunks_created,
        "error_message": job.error_message,
        "summary": job.summary
    }


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
    docs_dir = Path("user_docs")
    if not docs_dir.exists():
        return []
    return [f.name for f in docs_dir.glob("*.md")]


@router.get("/docs/content/{filename}")
async def get_doc_content(filename: str):
    """Get content of a documentation file."""
    doc_path = Path("user_docs") / filename
    if not doc_path.exists() or not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"content": doc_path.read_text(encoding="utf-8")}


@router.get("/learn/list")
async def list_learn_files():
    """List available learning materials."""
    learn_dir = Path("user_learn")
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
    learn_path = Path("user_learn") / filename
    if not learn_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if filename.endswith(".md"):
        return {"content": learn_path.read_text(encoding="utf-8")}
    elif filename.endswith(".pdf"):
        return FileResponse(path=str(learn_path), media_type="application/pdf", filename=filename)
    else:
        return FileResponse(path=str(learn_path), filename=filename)
