"""
Borrower API Endpoints
Endpoints for borrower loan applications and document management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.models.db import get_db
from app.models.orm_models import User, UserRole, Borrower, LoanApplication, ApplicationStatus, Document
from app.models.schemas import (
    LoanApplicationCreate, LoanApplicationResponse, ApplicationCreateResponse,
    DocumentResponse, DocumentUploadResponse, IngestionJobResponse
)
from app.core.auth import get_current_user, MockAuth, log_audit_action
from app.utils.storage import save_upload_file, get_file_size, get_file_type
from app.utils.pdf_text import extract_text_from_file
from app.services.ingestion import ingestion_service

router = APIRouter(prefix="/borrower", tags=["Borrower"])


@router.post("/apply", response_model=ApplicationCreateResponse, status_code=201)
async def create_loan_application(
    application: LoanApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new loan application for a green project."""
    
    # Create or get user if not authenticated
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    # Create or get borrower profile
    borrower = db.query(Borrower).filter(Borrower.user_id == current_user.id).first()
    if not borrower:
        borrower = Borrower(
            user_id=current_user.id,
            org_name=application.org_name,
            industry=application.sector,
            country=application.location.split(",")[-1].strip() if "," in application.location else application.location
        )
        db.add(borrower)
        db.commit()
        db.refresh(borrower)
    
    # Calculate total CO2
    total_co2 = (application.scope1_tco2 or 0) + (application.scope2_tco2 or 0) + (application.scope3_tco2 or 0)
    
    # Create loan application
    loan_app = LoanApplication(
        borrower_id=borrower.id,
        project_name=application.project_name,
        sector=application.sector,
        location=application.location,
        project_type=application.project_type,
        amount_requested=application.amount_requested,
        currency=application.currency,
        use_of_proceeds=application.use_of_proceeds,
        scope1_tco2=application.scope1_tco2,
        scope2_tco2=application.scope2_tco2,
        scope3_tco2=application.scope3_tco2,
        total_tco2=total_co2,
        baseline_year=application.baseline_year,
        additional_info=application.additional_info,
        status=ApplicationStatus.SUBMITTED
    )
    
    db.add(loan_app)
    db.commit()
    db.refresh(loan_app)
    
    # Log audit
    log_audit_action(db, "LoanApplication", loan_app.id, "create", current_user.id, 
                    {"project_name": application.project_name})
    
    return ApplicationCreateResponse(
        id=loan_app.id,
        status="submitted",
        message=f"Application for '{application.project_name}' submitted successfully"
    )


@router.post("/{loan_app_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    loan_app_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a supporting document for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    # Verify loan application exists
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Save file
    filepath = await save_upload_file(file, loan_app_id)
    
    # Quick text extraction
    text_extracted = None
    try:
        text_extracted = extract_text_from_file(filepath)
        extraction_status = "completed" if text_extracted else "failed"
    except Exception:
        extraction_status = "pending"
    
    # Create document record
    document = Document(
        loan_app_id=loan_app_id,
        uploader_id=current_user.id,
        filename=file.filename,
        filepath=filepath,
        file_type=get_file_type(file.filename),
        file_size=get_file_size(filepath),
        text_extracted=text_extracted,
        extraction_status=extraction_status,
        processed_at=datetime.utcnow() if text_extracted else None
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    log_audit_action(db, "Document", document.id, "upload", current_user.id,
                    {"filename": file.filename, "loan_app_id": loan_app_id})
    
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        text_extracted=text_extracted[:500] if text_extracted else None,
        status=extraction_status,
        message=f"Document '{file.filename}' uploaded successfully"
    )


@router.post("/{loan_app_id}/submit_for_ingestion", response_model=IngestionJobResponse)
async def submit_for_ingestion(
    loan_app_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit application for document ingestion and analysis."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Update status
    loan_app.status = ApplicationStatus.UNDER_REVIEW
    db.commit()
    
    # Note: For demo, we'll do sync processing. In production, use background_tasks
    # background_tasks.add_task(ingestion_service.run_ingestion, db, loan_app_id)
    
    return IngestionJobResponse(
        job_id=0,
        loan_app_id=loan_app_id,
        status="queued",
        message="Application submitted for processing. Use /ingest/run endpoint to trigger analysis."
    )


@router.get("/applications", response_model=List[LoanApplicationResponse])
async def get_my_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all loan applications for current borrower."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    borrower = db.query(Borrower).filter(Borrower.user_id == current_user.id).first()
    if not borrower:
        return []
    
    applications = db.query(LoanApplication).filter(
        LoanApplication.borrower_id == borrower.id
    ).order_by(LoanApplication.created_at.desc()).all()
    
    return applications


@router.get("/application/{loan_app_id}", response_model=LoanApplicationResponse)
async def get_application_details(
    loan_app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific loan application."""
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return loan_app


@router.get("/{loan_app_id}/documents", response_model=List[DocumentResponse])
async def get_application_documents(
    loan_app_id: int,
    db: Session = Depends(get_db)
):
    """Get all documents for a loan application."""
    
    documents = db.query(Document).filter(Document.loan_app_id == loan_app_id).all()
    return documents
