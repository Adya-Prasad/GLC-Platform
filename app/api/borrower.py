"""
Borrower API Endpoints
Endpoints for borrower loan applications and document management.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from app.models.db import get_db
from app.models.orm_models import User, UserRole, Borrower, LoanApplication, ApplicationStatus, Document
from app.models.schemas import (
    LoanApplicationCreate, LoanApplicationResponse, ApplicationCreateResponse,
    DocumentResponse, DocumentUploadResponse, IngestionJobResponse
)
from app.core.auth import get_current_user, MockAuth, log_audit_action
from app.utils.storage import save_upload_file, get_file_size, get_file_type, save_application_json, get_standardized_filename
from app.utils.pdf_text import extract_text_from_file
from app.services.ingestion import ingestion_service

router = APIRouter(prefix="/borrower", tags=["Borrower"])


def get_or_default(value, default="N/A"):
    """Return value if truthy, otherwise return default."""
    if value is None or value == "" or value == []:
        return default
    return value


def generate_loan_id(db: Session) -> str:
    """Generate next loan_id in format LOAN_1, LOAN_2, etc."""
    # Get the max numeric ID from existing loan_ids
    result = db.query(func.max(LoanApplication.id)).scalar()
    next_num = (result or 0) + 1
    return f"LOAN_{next_num}"


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
            country=get_or_default(application.location, "N/A").split(",")[-1].strip() if application.location and "," in application.location else get_or_default(application.location, "N/A"),
            gst_number=get_or_default(application.org_gst, "N/A"),
            credit_score=get_or_default(application.credit_score, "N/A"),
            website=get_or_default(application.website, "N/A")
        )
        db.add(borrower)
        db.commit()
        db.refresh(borrower)
    else:
        # Update borrower profile with latest info
        borrower.org_name = application.org_name
        borrower.industry = application.sector
        borrower.gst_number = get_or_default(application.org_gst, borrower.gst_number or "N/A")
        borrower.credit_score = get_or_default(application.credit_score, borrower.credit_score or "N/A")
        borrower.website = get_or_default(application.website, borrower.website or "N/A")
        db.commit()
    
    # Calculate total CO2
    scope1 = application.scope1_tco2 or 0.0
    scope2 = application.scope2_tco2 or 0.0
    scope3 = application.scope3_tco2 or 0.0
    total_co2 = scope1 + scope2 + scope3
    
    # Generate loan_id
    loan_id_str = generate_loan_id(db)
    
    # Parse planned start date
    planned_start = None
    if application.planned_start_date:
        try:
            planned_start = datetime.strptime(application.planned_start_date, "%Y-%m-%d")
        except ValueError:
            pass  # Keep as None if parsing fails
    
    # Build raw application JSON for storage (matching frontend structure)
    raw_json = {
        "organization": {
            "org_name": application.org_name,
            "contact_email": get_or_default(application.contact_email, "N/A"),
            "contact_phone": get_or_default(application.contact_phone, "N/A"),
            "gst_tax_id": get_or_default(application.org_gst, "N/A"),
            "credit_score": get_or_default(application.credit_score, "N/A"),
            "headquarters_location": get_or_default(application.location, "N/A"),
            "website": get_or_default(application.website, "N/A")
        },
        "project_info": {
            "project_title": application.project_name,
            "project_sector": application.sector,
            "project_location": get_or_default(application.project_location, "N/A"),
            "project_pin_zip_code": get_or_default(application.project_pin_code, "N/A"),
            "project_type": get_or_default(application.project_type, "New Project"),
            "reporting_frequency": get_or_default(application.reporting_frequency, "Annual"),
            "existing_loans": "Yes" if application.has_existing_loan else "No",
            "planned_start_date": get_or_default(application.planned_start_date, "N/A"),
            "amount_requested": application.amount_requested,
            "currency": application.currency,
            "project_description": get_or_default(application.project_description, get_or_default(application.use_of_proceeds, "N/A"))
        },
        "green_kpis": {
            "detailed_description_of_proceeds_usage": get_or_default(application.use_of_proceeds, "N/A"),
            "scope1_emissions": scope1,
            "scope2_emissions": scope2,
            "scope3_emissions": scope3,
            "installed_capacity_mw": get_or_default(application.installed_capacity, "N/A"),
            "target_reduction_percent": get_or_default(application.target_reduction, "N/A"),
            "baseline_year": application.baseline_year or "N/A",
            "selected_kpis": application.kpi_metrics if application.kpi_metrics else []
        },
        "esg_compliance_questionnaire": application.questionnaire_data or {}
    }
    
    # Create loan application
    loan_app = LoanApplication(
        loan_id=loan_id_str,
        borrower_id=borrower.id,
        project_name=application.project_name,
        sector=application.sector,
        location=get_or_default(application.location, "N/A"),
        project_location=get_or_default(application.project_location, "N/A"),
        project_type=get_or_default(application.project_type, "New Project"),
        amount_requested=application.amount_requested,
        currency=application.currency,
        use_of_proceeds=get_or_default(application.use_of_proceeds, "N/A"),
        project_description=get_or_default(application.project_description, get_or_default(application.use_of_proceeds, "N/A")),
        scope1_tco2=scope1,
        scope2_tco2=scope2,
        scope3_tco2=scope3,
        total_tco2=total_co2,
        baseline_year=application.baseline_year,
        additional_info=get_or_default(application.additional_info, "N/A"),
        cloud_doc_url=get_or_default(application.cloud_doc_url, "N/A"),
        
        # Organization snapshot
        org_name=application.org_name,
        
        # Contact info
        project_pin_code=get_or_default(application.project_pin_code, "N/A"),
        contact_email=get_or_default(application.contact_email, "N/A"),
        contact_phone=get_or_default(application.contact_phone, "N/A"),
        has_existing_loan=application.has_existing_loan,
        
        # Timeline
        planned_start_date=planned_start,
        
        # Project details
        reporting_frequency=get_or_default(application.reporting_frequency, "Annual"),
        installed_capacity=get_or_default(application.installed_capacity, "N/A"),
        target_reduction=get_or_default(application.target_reduction, "N/A"),
        kpi_metrics=application.kpi_metrics if application.kpi_metrics else [],
        
        # Compliance
        consent_agreed=application.consent_agreed,
        questionnaire_data=application.questionnaire_data or {},
        
        # Raw JSON storage
        raw_application_json=raw_json,
        
        status=ApplicationStatus.PENDING
    )
    
    db.add(loan_app)
    db.commit()
    db.refresh(loan_app)
    
    # Save raw application JSON to loan_docs folder
    try:
        save_application_json(loan_id_str, raw_json)
    except Exception as e:
        # Log but don't fail the application creation
        print(f"Warning: Could not save application JSON: {e}")
    
    # Log audit
    log_audit_action(db, "LoanApplication", loan_app.id, "create", current_user.id, 
                    {"loan_id": loan_id_str, "project_name": application.project_name})
    
    return ApplicationCreateResponse(
        id=loan_app.id,
        loan_id=loan_id_str,
        status="Pending",
        message=f"Application '{loan_id_str}' for '{application.project_name}' created successfully"
    )


@router.post("/{loan_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    loan_id: int,
    file: UploadFile = File(...),
    category: str = Form("general"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a supporting document for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    # Verify loan application exists and get loan_id string
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    loan_id_str = loan_app.loan_id  # e.g., LOAN_1
    
    # Save file with standardized naming
    filepath = await save_upload_file(
        file, 
        loan_id, 
        loan_id_str=loan_id_str,
        category=category
    )
    
    # Get standardized filename for display
    standardized_name = get_standardized_filename(category, file.filename)
    
    # Quick text extraction
    text_extracted = None
    try:
        text_extracted = extract_text_from_file(filepath)
        extraction_status = "completed" if text_extracted else "failed"
    except Exception:
        extraction_status = "pending"
    
    # Create document record
    document = Document(
        loan_id=loan_id,
        uploader_id=current_user.id,
        filename=standardized_name,  # Use standardized name
        filepath=filepath,
        file_type=get_file_type(file.filename),
        doc_category=category,
        file_size=get_file_size(filepath),
        text_extracted=text_extracted,
        extraction_status=extraction_status,
        processed_at=datetime.utcnow() if text_extracted else None
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    log_audit_action(db, "Document", document.id, "upload", current_user.id,
                    {"filename": standardized_name, "original_filename": file.filename, 
                     "loan_id": loan_id, "loan_id_str": loan_id_str, "category": category})
    
    return DocumentUploadResponse(
        id=document.id,
        filename=standardized_name,
        text_extracted=text_extracted[:500] if text_extracted else None,
        status=extraction_status,
        message=f"Document saved as '{standardized_name}' in {loan_id_str}/"
    )


@router.post("/{loan_id}/submit_for_ingestion", response_model=IngestionJobResponse)
async def submit_for_ingestion(
    loan_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit application for document ingestion and analysis."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Update status
    loan_app.status = ApplicationStatus.UNDER_REVIEW
    db.commit()
    
    # Note: For demo, we'll do sync processing. In production, use background_tasks
    # background_tasks.add_task(ingestion_service.run_ingestion, db, loan_id)
    
    return IngestionJobResponse(
        job_id=0,
        loan_id=loan_id,
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
    
    # Manually populate org_name for the schema
    for app in applications:
        app.org_name = app.org_name or borrower.org_name
        
    return applications


@router.get("/application/{loan_id}", response_model=LoanApplicationResponse)
async def get_application_details(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific loan application."""
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return loan_app


@router.get("/{loan_id}/documents", response_model=List[DocumentResponse])
async def get_application_documents(
    loan_id: int,
    db: Session = Depends(get_db)
):
    """Get all documents for a loan application."""
    
    documents = db.query(Document).filter(Document.loan_id == loan_id).all()
    return documents
@router.get("/all_documents", response_model=List[DocumentResponse])
async def get_all_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents uploaded by current user across all applications."""
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    
    documents = db.query(Document).filter(Document.uploader_id == current_user.id).order_by(Document.uploaded_at.desc()).all()
    return documents

@router.get("/document/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """Download a document file."""
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from fastapi.responses import FileResponse
    import os
    
    if not os.path.exists(document.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
        
    return FileResponse(
        path=document.filepath, 
        filename=document.filename,
        media_type='application/octet-stream'
    )

@router.get("/document/{doc_id}/view")
async def view_document_content(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """View document content (for preview)."""
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    from fastapi.responses import FileResponse
    import os
    
    if not os.path.exists(document.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Map file types to media types for browser preview
    media_map = {
        '.pdf': 'application/pdf',
        '.json': 'application/json',
        '.txt': 'text/plain',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg'
    }
    
    ext = os.path.splitext(document.filename)[1].lower()
    media_type = media_map.get(ext, 'application/octet-stream')
    
    return FileResponse(path=document.filepath, media_type=media_type)
