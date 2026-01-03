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


@router.post("/ingest/run/{loan_app_id}", response_model=IngestionSummary)
async def run_ingestion(
    loan_app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger document ingestion and analysis for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    try:
        result = ingestion_service.run_ingestion(db, loan_app_id)
        return IngestionSummary(
            job_id=result['job_id'],
            loan_app_id=loan_app_id,
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


@router.get("/report/application/{loan_app_id}")
async def get_report(
    loan_app_id: int,
    format: str = Query("json", description="Output format: json or pdf"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate GLP investor report for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    try:
        report_data = report_service.generate_report(db, loan_app_id, format)
        
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


@router.post("/external_review/{loan_app_id}/request")
async def request_external_review(
    loan_app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate external review package (ZIP with documents and analysis)."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Generate report
    report_data = report_service.generate_report(db, loan_app_id, "json")
    
    # Create ZIP package
    package_dir = settings.REPORTS_DIR / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)
    
    zip_filename = f"external_review_{loan_app_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = package_dir / zip_filename
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Add report JSON
        zipf.writestr("report.json", json.dumps(report_data, indent=2, default=str))
        
        # Add documents
        documents = db.query(Document).filter(Document.loan_app_id == loan_app_id).all()
        for doc in documents:
            if Path(doc.filepath).exists():
                zipf.write(doc.filepath, f"documents/{doc.filename}")
        
        # Add audit logs
        logs = db.query(AuditLog).filter(
            AuditLog.entity_type == "LoanApplication",
            AuditLog.entity_id == loan_app_id
        ).all()
        log_data = [{"action": l.action, "timestamp": l.timestamp.isoformat(), "data": l.data} for l in logs]
        zipf.writestr("audit_log.json", json.dumps(log_data, indent=2))
    
    return {
        "loan_app_id": loan_app_id,
        "package_url": f"/downloads/{zip_filename}",
        "generated_at": datetime.utcnow().isoformat(),
        "contents": ["report.json", f"{len(documents)} documents", "audit_log.json"]
    }


@router.get("/audit/{loan_app_id}", response_model=List[AuditLogResponse])
async def get_audit_logs(
    loan_app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "LoanApplication",
        AuditLog.entity_id == loan_app_id
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
