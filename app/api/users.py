"""
Unified user router and endpoints replacing borrower/lender routers.
This file exposes both /borrower/* and /lender/* endpoints to keep existing client routes working,
but centralizes logic to avoid duplication.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from dbms.db import get_db
from dbms.orm_models import (
    User, Borrower, LoanApplication, ApplicationStatus, Document,
    Verification, VerificationResult
)
from dbms.schemas import (
    LoanApplicationCreate, LoanApplicationResponse, ApplicationCreateResponse,
    DocumentResponse, DocumentUploadResponse, IngestionJobResponse,
    LoanApplicationListItem, VerificationCreate, VerificationResponse, PortfolioSummary
)
from app.operations.auth import get_current_user, MockAuth, log_audit_action
from app.utils.storage import save_upload_file, get_file_size, get_file_type, save_application_json, get_standardized_filename


def get_or_default(value, default: Any = "none"):
    if value is None or value == "" or value == []:
        return default
    return value


def generate_loan_id(db: Session) -> str:
    result = db.query(LoanApplication.id).order_by(LoanApplication.id.desc()).first()
    next_num = (result[0] if result and result[0] else 0) + 1
    return f"LOAN_{next_num}"


def ensure_borrower_profile(db: Session, current_user: User, application) -> Borrower:
    borrower = db.query(Borrower).filter(Borrower.user_id == current_user.id).first()
    if not borrower:
        borrower = Borrower(
            user_id=current_user.id,
            org_name=application.org_name,
            industry=application.sector,
            country=(get_or_default(application.location).split(",")[-1].strip() if application.location and "," in application.location else get_or_default(application.location)),
            gst_number=get_or_default(application.org_gst),
            credit_score=get_or_default(application.credit_score),
            website=get_or_default(application.website)
        )
        db.add(borrower)
        db.commit()
        db.refresh(borrower)
    else:
        borrower.org_name = application.org_name
        borrower.industry = application.sector
        borrower.gst_number = get_or_default(application.org_gst, borrower.gst_number or "none")
        borrower.credit_score = get_or_default(application.credit_score, borrower.credit_score or "none")
        borrower.website = get_or_default(application.website, borrower.website or "none")
        db.commit()
    return borrower


def build_raw_application_json(application) -> Dict[str, Any]:
    """Builds the raw application JSON with a structure matching the frontend expectations."""

    def get_optional(value):
        """Returns None if value is empty, otherwise the value."""
        if value in [None, "", []]:
            return None
        return value

    # Map frontend short keys to descriptive keys from the user's template
    q_map = {
        "q_env_benefits": "1_Does_the_project_have_clear_environmental_benefits?",
        "q_data_available": "2_Is_data_available_to_measure_and_report_impact?",
        "q_regulatory_compliance": "3_Compliance_with_local_environmental_regulations?",
        "q_social_risk": "4_Any_controversy_or_negative_social_impact_risks?",
        "q_rd_low_carbon": "5_Are_you_implementing_any_research_and_development_(R&D)_for_low-carbon_technologies_or_practices?",
        "q_union_agreement": "6_Have_you_signed_a_Union_agreement?",
        "q_adopt_ghg_protocol": "7_Are_you_adapting_GHG_Protocol?",
        "q_published_climate_disclosures": "8_Has_the_organization_published_climate-related_disclosures_or_reporting?",
        "q_timebound_targets": "9_Are_there_clear,_time-bound_emissions_reduction_targets_aligned_with_climate_pathways?",
        "q_phaseout_highcarbon": "10_Does_the_company_have_plans_to_phase_out_or_avoid_new_high-carbon_infrastructure?",
        "q_long_lived_highcarbon_assets": "11_Does_the_project_involve_long-lived_high-carbon_assets_that_could_inhibit_future_decarbonisation?",
    }
    
    questionnaire = application.questionnaire_data or {}
    full_questionnaire_data = {q_map.get(k, k): v for k, v in questionnaire.items()}

    raw_json = {
        "organization_details": {
            # Keys matching frontend expectations
            "org_name": get_optional(application.org_name),
            "sector": get_optional(application.sector),
            "location": get_optional(application.location),
            "website": get_optional(application.website),
            "annual_revenue": application.annual_revenue or None,
            "shareholder_entities": application.shareholder_entities or 0,
            # Additional fields for reference
            "contact_email": get_optional(application.contact_email),
            "contact_phone": get_optional(application.contact_phone),
            "tax_id": get_optional(application.org_gst),
            "credit_score": get_optional(application.credit_score),
        },
        "project_information": {
            # Keys matching frontend expectations
            "project_name": get_optional(application.project_name),
            "project_type": get_optional(application.project_type),
            "project_location": get_optional(application.project_location),
            "planned_start_date": get_optional(str(application.planned_start_date.date()) if hasattr(application.planned_start_date, 'date') else application.planned_start_date),
            "loan_tenor": application.loan_tenor,
            "amount_requested": application.amount_requested or None,
            "currency": get_optional(application.currency),
            "use_of_proceeds": get_optional(application.use_of_proceeds),
            # Additional fields
            "project_pin_code": get_optional(application.project_pin_code),
            "reporting_frequency": get_optional(application.reporting_frequency),
            "existing_loans": "Yes" if application.has_existing_loan else "No",
            "project_description": get_optional(application.project_description),
            "shareholder_entities": application.shareholder_entities,
            "shareholders_data": getattr(application, "shareholders_data", []),
        },
        "green_qualification_and_kpis": {
            # Keys matching frontend expectations
            "scope1_tco2": application.scope1_tco2 or 0.0,
            "scope2_tco2": application.scope2_tco2 or 0.0,
            "scope3_tco2": application.scope3_tco2 or 0.0,
            "baseline_year": get_optional(application.baseline_year),
            "target_reduction": get_optional(application.target_reduction),
            "reporting_frequency": get_optional(application.reporting_frequency),
            "kpi_metrics": application.kpi_metrics or [],
            # Additional fields
            "use_of_proceeds_description": get_optional(application.use_of_proceeds),
        },
        "esg_compliance_questionnaire": full_questionnaire_data,
        "supporting_documents": {}
    }
    return raw_json


def create_application(db: Session, application, current_user: User) -> LoanApplication:
    if not current_user:
        raise HTTPException(status_code=401, detail="User must be provided")

    borrower = ensure_borrower_profile(db, current_user, application)

    scope1 = application.scope1_tco2 or 0.0
    scope2 = application.scope2_tco2 or 0.0
    scope3 = application.scope3_tco2 or 0.0
    total_co2 = scope1 + scope2 + scope3

    loan_id_str = generate_loan_id(db)

    try:
        planned_start = datetime.strptime(application.planned_start_date, "%Y-%m-%d")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid 'planned_start_date' format. Expected YYYY-MM-DD")

    raw_json = build_raw_application_json(application)

    loan_app = LoanApplication(
        loan_id=loan_id_str,
        borrower_id=borrower.id,
        project_name=application.project_name,
        sector=application.sector,
        location=get_or_default(application.location),
        project_location=get_or_default(application.project_location),
        project_type=get_or_default(application.project_type, "New Project"),
        amount_requested=application.amount_requested,
        currency=application.currency,
        use_of_proceeds=get_or_default(application.use_of_proceeds),
        project_description=get_or_default(application.project_description, get_or_default(application.use_of_proceeds)),
        annual_revenue=application.annual_revenue,
        scope1_tco2=scope1,
        scope2_tco2=scope2,
        scope3_tco2=scope3,
        total_tco2=total_co2,
        baseline_year=application.baseline_year,
        loan_tenor=application.loan_tenor,
        cloud_doc_url=get_or_default(application.cloud_doc_url),
        org_name=application.org_name,
        tax_id=application.org_gst,
        credit_score=application.credit_score,
        project_pin_code=get_or_default(application.project_pin_code),
        contact_email=get_or_default(application.contact_email),
        contact_phone=get_or_default(application.contact_phone),
        has_existing_loan=application.has_existing_loan,
        planned_start_date=planned_start,
        shareholder_entities=application.shareholder_entities or 0,
        reporting_frequency=get_or_default(application.reporting_frequency, "Annual"),
        target_reduction=get_or_default(application.target_reduction),
        kpi_metrics=application.kpi_metrics if application.kpi_metrics else [],
        consent_agreed=application.consent_agreed,
        questionnaire_data=application.questionnaire_data or {},
        raw_application_json=raw_json,
        status=ApplicationStatus.PENDING
    )

    db.add(loan_app)
    db.commit()
    db.refresh(loan_app)

    try:
        json_path = save_application_json(loan_id_str, raw_json)
        # Create a Document record for the generated application_data.json
        json_doc = Document(
            loan_id=loan_app.id,
            uploader_id=current_user.id,
            filename="application_data.json",
            filepath=json_path,
            file_type='application/json',
            doc_category='application_metadata',
            file_size=get_file_size(json_path),
            extraction_status="n/a",
        )
        db.add(json_doc)
        db.commit()
        db.refresh(json_doc)
    except Exception:
        # If this fails, don't prevent the API from returning successfully
        # but log it for debugging.
        pass

    try:
        log_audit_action(db, "LoanApplication", loan_app.id, "create", current_user.id,
                         {"loan_id": loan_id_str, "project_name": application.project_name})
    except Exception:
        pass

    return loan_app


router = APIRouter(tags=["Users"])


# Borrower endpoints (kept under same paths for backward compatibility)
@router.post("/borrower/apply", response_model=ApplicationCreateResponse, status_code=201)
async def create_loan_application(application: LoanApplicationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")

    loan_app = create_application(db, application, current_user)
    return ApplicationCreateResponse(id=loan_app.id, loan_id=loan_app.loan_id, status="Pending", message=f"Application '{loan_app.loan_id}' created")


@router.post("/borrower/{loan_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(loan_id: int, file: UploadFile = File(...), category: str = Form("general"), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")

    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")

    loan_id_str = loan_app.loan_id
    filepath = await save_upload_file(file, loan_id, loan_id_str=loan_id_str, category=category)
    standardized_name = get_standardized_filename(category, file.filename)
    
    # Initialize text extraction variables
    text_extracted = None
    extraction_status = "pending"

    document = Document(
        loan_id=loan_id,
        uploader_id=current_user.id,
        filename=standardized_name,
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

    try:
        raw = loan_app.raw_application_json or {}
        supp = raw.get('supporting_documents', {})
        supp[category] = standardized_name
        raw['supporting_documents'] = supp
        loan_app.raw_application_json = raw
        db.commit()
        db.refresh(loan_app)

        # Persist updated raw JSON to disk so files and questionnaire are reflected in application_data.json
        try:
            save_application_json(loan_id_str, loan_app.raw_application_json)
        except Exception as e:
            # Log the failure to persist JSON
            try:
                log_audit_action(db, "Document", document.id, "save_application_json_failed", current_user.id, {"error": str(e), "loan_id": loan_id_str})
            except Exception:
                pass
    except Exception as e:
        # Log update errors for easier debugging
        try:
            log_audit_action(db, "Document", document.id, "update_raw_json_failed", current_user.id, {"error": str(e), "loan_id": loan_id})
        except Exception:
            pass

    log_audit_action(db, "Document", document.id, "upload", current_user.id, {"filename": standardized_name, "loan_id": loan_id, "category": category})

    return DocumentUploadResponse(id=document.id, filename=standardized_name, text_extracted=(text_extracted[:500] if text_extracted else None), status=extraction_status, message=f"Document saved as '{standardized_name}' in {loan_id_str}/")


@router.post("/borrower/{loan_id}/submit_for_ingestion", response_model=IngestionJobResponse)
async def submit_for_ingestion(loan_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")

    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")

    loan_app.status = ApplicationStatus.UNDER_REVIEW
    db.commit()

    return IngestionJobResponse(job_id=0, loan_id=loan_id, status="queued", message="Application submitted for processing")


@router.get("/borrower/applications", response_model=List[LoanApplicationResponse])
async def get_my_applications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")

    borrower = db.query(Borrower).filter(Borrower.user_id == current_user.id).first()
    if not borrower:
        return []

    applications = db.query(LoanApplication).filter(LoanApplication.borrower_id == borrower.id).order_by(LoanApplication.created_at.desc()).all()
    for app in applications:
        app.org_name = app.org_name or borrower.org_name
        if app.planned_start_date:
            try:
                app.planned_start_date = app.planned_start_date.date().isoformat()
            except Exception:
                app.planned_start_date = None
    return applications


@router.get("/borrower/application/{loan_id}", response_model=LoanApplicationResponse)
async def get_application_details(loan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    if loan_app.planned_start_date:
        try:
            loan_app.planned_start_date = loan_app.planned_start_date.date().isoformat()
        except Exception:
            loan_app.planned_start_date = None
    return loan_app


@router.get("/borrower/{loan_id}/documents", response_model=List[DocumentResponse])
async def get_application_documents(loan_id: int, db: Session = Depends(get_db)):
    documents = db.query(Document).filter(Document.loan_id == loan_id).all()
    return documents


@router.get("/borrower/all_documents", response_model=List[DocumentResponse])
async def get_all_my_documents(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "borrower")
    documents = db.query(Document).filter(Document.uploader_id == current_user.id).order_by(Document.uploaded_at.desc()).all()
    return documents


@router.get("/borrower/document/{doc_id}/download")
async def download_document(doc_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(document.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(path=document.filepath, filename=document.filename, media_type='application/octet-stream')


@router.get("/borrower/document/{doc_id}/view")
async def view_document_content(doc_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(document.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    media_map = {'.pdf': 'application/pdf', '.json': 'application/json', '.txt': 'text/plain', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
    ext = os.path.splitext(document.filename)[1].lower()
    media_type = media_map.get(ext, 'application/octet-stream')
    return FileResponse(path=document.filepath, media_type=media_type)


# Lender endpoints (same paths as before but centralized)
@router.get("/lender/applications", response_model=List[LoanApplicationListItem])
async def list_applications(status: Optional[str] = None, sector: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    query = db.query(LoanApplication).join(Borrower)
    if status:
        try:
            status_enum = ApplicationStatus(status)
            query = query.filter(LoanApplication.status == status_enum)
        except ValueError:
            pass
    if sector:
        query = query.filter(LoanApplication.sector.ilike(f"%{sector}%"))
    applications = query.order_by(LoanApplication.created_at.desc()).all()
    result = []
    for app in applications:
        result.append(LoanApplicationListItem(
            id=app.id,
            loan_id=app.loan_id,
            project_name=app.project_name,
            borrower_name=app.borrower.user.name if app.borrower and app.borrower.user else "none",
            org_name=app.org_name or (app.borrower.org_name if app.borrower else "none"),
            sector=app.sector,
            amount_requested=app.amount_requested,
            currency=app.currency,
            status=app.status,
            esg_score=app.esg_score,
            glp_eligibility=app.glp_eligibility,
            planned_start_date=(app.planned_start_date.date().isoformat() if hasattr(app.planned_start_date, 'date') else (app.planned_start_date if isinstance(app.planned_start_date, str) else None)),
            shareholder_entities=app.shareholder_entities,
            created_at=app.created_at
        ))
    return result


@router.get("/lender/application/{loan_id}")
async def get_application_detail(loan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    borrower = loan_app.borrower
    documents = loan_app.documents
    kpis = loan_app.kpis
    verifications = loan_app.verifications
    parsed_data = loan_app.parsed_fields or {}
    extracted = parsed_data.get('extracted', {})
    parsed_fields = {
        "use_of_proceeds": loan_app.use_of_proceeds,
        "kpis": [{"kpi_name": k.kpi_name, "baseline": k.baseline_value, "spt": k.spt_target, "target_year": k.target_year} for k in kpis],
        "glp_category_guess": loan_app.glp_category,
        "dnsh": loan_app.dnsh_status.get('results', {}) if loan_app.dnsh_status else {},
        "management_of_proceeds": extracted.get('is_there_a_management_of_pro', {}).get('answer'),
        "external_review": extracted.get('does_the_report_specify_exte', {}).get('answer'),
    }
    latest_verification = verifications[-1] if verifications else None
    verification_summary = {
        "conclusion": latest_verification.result.value if latest_verification else "Pending",
        "confidence": latest_verification.confidence if latest_verification else 0,
        "evidence": latest_verification.evidence[:5] if latest_verification and latest_verification.evidence else []
    }
    dnsh_status = loan_app.dnsh_status or {}
    dnsh_results = dnsh_status.get('results', {})
    dnsh_checks = [{"criterion": k, "status": v.get('status', 'unclear'), "evidence": v.get('evidence'), "notes": v.get('notes')} for k, v in dnsh_results.items()]
    return {"loan_app": {"id": loan_app.id, "borrower_id": loan_app.borrower_id, "project_name": loan_app.project_name, "sector": loan_app.sector, "location": loan_app.location, "project_type": loan_app.project_type, "amount_requested": loan_app.amount_requested, "currency": loan_app.currency, "use_of_proceeds": loan_app.use_of_proceeds, "scope1_tco2": loan_app.scope1_tco2, "scope2_tco2": loan_app.scope2_tco2, "scope3_tco2": loan_app.scope3_tco2, "total_tco2": loan_app.total_tco2, "baseline_year": loan_app.baseline_year, "esg_score": loan_app.esg_score, "glp_eligibility": loan_app.glp_eligibility, "glp_category": loan_app.glp_category, "carbon_lockin_risk": loan_app.carbon_lockin_risk, "status": loan_app.status.value if loan_app.status else None, "created_at": loan_app.created_at.isoformat(), "updated_at": loan_app.updated_at.isoformat() if loan_app.updated_at else None}, "borrower": {"id": borrower.id if borrower else None, "org_name": borrower.org_name if borrower else None, "industry": borrower.industry if borrower else None, "country": borrower.country if borrower else None}, "documents": [{"id": d.id, "filename": d.filename, "uploaded_at": d.uploaded_at.isoformat()} for d in documents], "kpis": [{"id": k.id, "kpi_name": k.kpi_name, "baseline_value": k.baseline_value, "spt_target": k.spt_target, "target_year": k.target_year} for k in kpis], "parsed_fields": parsed_fields, "verification": verification_summary, "esg_score": loan_app.esg_score or 0, "dnsh_checks": dnsh_checks, "carbon_lockin_risk": loan_app.carbon_lockin_risk or "unknown"}


@router.get("/lender/application/{loan_id}/documents", response_model=List[DocumentResponse])
async def get_lender_application_documents(loan_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    documents = db.query(Document).filter(Document.loan_id == loan_id).all()
    return documents


@router.get("/lender/document/{doc_id}/download")
async def download_lender_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(document.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    return FileResponse(path=document.filepath, filename=document.filename, media_type='application/octet-stream')


@router.get("/lender/document/{doc_id}/view")
async def view_lender_document_content(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not os.path.exists(document.filepath):
        raise HTTPException(status_code=404, detail="File not found on server")
    media_map = {'.pdf': 'application/pdf', '.json': 'application/json', '.txt': 'text/plain', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
    ext = os.path.splitext(document.filename)[1].lower()
    media_type = media_map.get(ext, 'application/octet-stream')
    return FileResponse(path=document.filepath, media_type=media_type)


@router.post("/lender/application/{loan_id}/verify", response_model=VerificationResponse)
async def verify_application(loan_id: int, verification: VerificationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    ver = Verification(loan_id=loan_id, verifier_id=current_user.id, verifier_role=verification.verifier_role, verification_type="manual_review", result=VerificationResult(verification.result.value), notes=verification.notes, evidence=[], confidence=1.0)
    db.add(ver)
    if verification.result.value == "pass":
        loan_app.status = ApplicationStatus.APPROVED
    elif verification.result.value == "fail":
        loan_app.status = ApplicationStatus.REJECTED
    else:
        loan_app.status = ApplicationStatus.NEEDS_INFO
    db.commit()
    db.refresh(ver)
    log_audit_action(db, "LoanApplication", loan_id, "verify", current_user.id, {"result": verification.result.value, "notes": verification.notes})
    return ver


@router.get("/lender/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    applications = db.query(LoanApplication).all()
    total_apps = len(applications)
    total_financed = sum(a.amount_requested for a in applications if a.status == ApplicationStatus.APPROVED)
    total_co2 = sum((a.total_tco2 or 0) for a in applications if a.status == ApplicationStatus.APPROVED)
    green_projects = sum(1 for a in applications if a.glp_eligibility)
    pending = sum(1 for a in applications if a.status in [ApplicationStatus.PENDING, ApplicationStatus.UNDER_REVIEW])
    approved = sum(1 for a in applications if a.status == ApplicationStatus.APPROVED)
    rejected = sum(1 for a in applications if a.status == ApplicationStatus.REJECTED)
    flagged = sum(1 for a in applications if a.carbon_lockin_risk == "high")
    esg_scores = [a.esg_score for a in applications if a.esg_score is not None]
    avg_esg = sum(esg_scores) / len(esg_scores) if esg_scores else 0
    sectors = {}
    for a in applications:
        sectors[a.sector] = sectors.get(a.sector, 0) + 1
    status_breakdown = {"pending": 0, "under_review": 0, "approved": 0, "rejected": 0, "needs_info": 0}
    for a in applications:
        if a.status:
            status_breakdown[a.status.value] = status_breakdown.get(a.status.value, 0) + 1
    return PortfolioSummary(total_applications=total_apps, total_financed_amount=total_financed, total_financed_co2=total_co2, num_green_projects=green_projects, num_pending=pending, num_approved=approved, num_rejected=rejected, percent_eligible_green=(green_projects / total_apps * 100) if total_apps > 0 else 0, avg_esg_score=round(avg_esg, 1), flagged_count=flagged, sector_breakdown=sectors, status_breakdown=status_breakdown)
