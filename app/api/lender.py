"""
Lender API Endpoints
Endpoints for lenders to review applications, verify, and manage portfolio.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.models.db import get_db
from app.models.orm_models import (
    User, LoanApplication, ApplicationStatus, Borrower, 
    Document, KPI, Verification, VerificationResult
)
from app.models.schemas import (
    LoanApplicationListItem, ApplicationDetailResponse, PortfolioSummary,
    VerificationCreate, VerificationResponse, ParsedFields, VerificationSummary,
    BorrowerResponse, DocumentResponse, KPIResponse, DNSHCheck
)
from app.core.auth import get_current_user, MockAuth, log_audit_action
from app.services.ingestion import ingestion_service

router = APIRouter(prefix="/lender", tags=["Lender"])


@router.get("/applications", response_model=List[LoanApplicationListItem])
async def list_applications(
    status: Optional[str] = Query(None, description="Filter by status"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all loan applications with optional filters."""
    
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
            project_name=app.project_name,
            borrower_name=app.borrower.user.name if app.borrower and app.borrower.user else "N/A",
            org_name=app.borrower.org_name if app.borrower else "N/A",
            sector=app.sector,
            amount_requested=app.amount_requested,
            currency=app.currency,
            status=app.status,
            esg_score=app.esg_score,
            glp_eligibility=app.glp_eligibility,
            created_at=app.created_at
        ))
    
    return result


@router.get("/application/{loan_app_id}")
async def get_application_detail(
    loan_app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed view of a loan application with parsed fields and analysis."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    borrower = loan_app.borrower
    documents = loan_app.documents
    kpis = loan_app.kpis
    verifications = loan_app.verifications
    
    # Build parsed fields from stored data
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
    
    # Build verification summary
    latest_verification = verifications[-1] if verifications else None
    verification_summary = {
        "conclusion": latest_verification.result.value if latest_verification else "Pending",
        "confidence": latest_verification.confidence if latest_verification else 0,
        "evidence": latest_verification.evidence[:5] if latest_verification and latest_verification.evidence else []
    }
    
    # Build DNSH checks
    dnsh_status = loan_app.dnsh_status or {}
    dnsh_results = dnsh_status.get('results', {})
    dnsh_checks = [
        {"criterion": k, "status": v.get('status', 'unclear'), "evidence": v.get('evidence'), "notes": v.get('notes')}
        for k, v in dnsh_results.items()
    ]
    
    return {
        "loan_app": {
            "id": loan_app.id,
            "borrower_id": loan_app.borrower_id,
            "project_name": loan_app.project_name,
            "sector": loan_app.sector,
            "location": loan_app.location,
            "project_type": loan_app.project_type,
            "amount_requested": loan_app.amount_requested,
            "currency": loan_app.currency,
            "use_of_proceeds": loan_app.use_of_proceeds,
            "scope1_tco2": loan_app.scope1_tco2,
            "scope2_tco2": loan_app.scope2_tco2,
            "scope3_tco2": loan_app.scope3_tco2,
            "total_tco2": loan_app.total_tco2,
            "baseline_year": loan_app.baseline_year,
            "esg_score": loan_app.esg_score,
            "glp_eligibility": loan_app.glp_eligibility,
            "glp_category": loan_app.glp_category,
            "carbon_lockin_risk": loan_app.carbon_lockin_risk,
            "status": loan_app.status.value if loan_app.status else None,
            "created_at": loan_app.created_at.isoformat(),
            "updated_at": loan_app.updated_at.isoformat() if loan_app.updated_at else None,
        },
        "borrower": {
            "id": borrower.id if borrower else None,
            "org_name": borrower.org_name if borrower else None,
            "industry": borrower.industry if borrower else None,
            "country": borrower.country if borrower else None,
        },
        "documents": [{"id": d.id, "filename": d.filename, "uploaded_at": d.uploaded_at.isoformat()} for d in documents],
        "kpis": [{"id": k.id, "kpi_name": k.kpi_name, "baseline_value": k.baseline_value, "spt_target": k.spt_target, "target_year": k.target_year} for k in kpis],
        "parsed_fields": parsed_fields,
        "verification": verification_summary,
        "esg_score": loan_app.esg_score or 0,
        "dnsh_checks": dnsh_checks,
        "carbon_lockin_risk": loan_app.carbon_lockin_risk or "unknown",
    }


@router.post("/application/{loan_app_id}/verify", response_model=VerificationResponse)
async def verify_application(
    loan_app_id: int,
    verification: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit verification decision for a loan application."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_app_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Create verification record
    ver = Verification(
        loan_app_id=loan_app_id,
        verifier_id=current_user.id,
        verifier_role=verification.verifier_role,
        verification_type="manual_review",
        result=VerificationResult(verification.result.value),
        notes=verification.notes,
        evidence=[],
        confidence=1.0
    )
    
    db.add(ver)
    
    # Update application status based on result
    if verification.result.value == "pass":
        loan_app.status = ApplicationStatus.APPROVED
    elif verification.result.value == "fail":
        loan_app.status = ApplicationStatus.REJECTED
    else:
        loan_app.status = ApplicationStatus.NEEDS_INFO
    
    db.commit()
    db.refresh(ver)
    
    log_audit_action(db, "LoanApplication", loan_app_id, "verify", current_user.id,
                    {"result": verification.result.value, "notes": verification.notes})
    
    return ver


@router.get("/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get aggregated portfolio metrics."""
    
    if not current_user:
        current_user = MockAuth.quick_login(db, "lender")
    
    # Aggregate metrics
    applications = db.query(LoanApplication).all()
    
    total_apps = len(applications)
    total_financed = sum(a.amount_requested for a in applications if a.status == ApplicationStatus.APPROVED)
    total_co2 = sum((a.total_tco2 or 0) for a in applications if a.status == ApplicationStatus.APPROVED)
    green_projects = sum(1 for a in applications if a.glp_eligibility)
    pending = sum(1 for a in applications if a.status in [ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW])
    approved = sum(1 for a in applications if a.status == ApplicationStatus.APPROVED)
    rejected = sum(1 for a in applications if a.status == ApplicationStatus.REJECTED)
    flagged = sum(1 for a in applications if a.carbon_lockin_risk == "high")
    
    esg_scores = [a.esg_score for a in applications if a.esg_score is not None]
    avg_esg = sum(esg_scores) / len(esg_scores) if esg_scores else 0
    
    # Sector breakdown
    sectors = {}
    for a in applications:
        sectors[a.sector] = sectors.get(a.sector, 0) + 1
    
    # Status breakdown
    status_breakdown = {"submitted": 0, "under_review": 0, "approved": 0, "rejected": 0, "needs_info": 0}
    for a in applications:
        if a.status:
            status_breakdown[a.status.value] = status_breakdown.get(a.status.value, 0) + 1
    
    return PortfolioSummary(
        total_applications=total_apps,
        total_financed_amount=total_financed,
        total_financed_co2=total_co2,
        num_green_projects=green_projects,
        num_pending=pending,
        num_approved=approved,
        num_rejected=rejected,
        percent_eligible_green=(green_projects / total_apps * 100) if total_apps > 0 else 0,
        avg_esg_score=round(avg_esg, 1),
        flagged_count=flagged,
        sector_breakdown=sectors,
        status_breakdown=status_breakdown
    )
