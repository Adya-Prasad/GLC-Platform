"""
Analysis API Endpoints
Provides ESG analysis, statistics, and audit data for loan applications.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from dbms.db import get_db
from dbms.orm_models import LoanApplication, Document, AuditLog, User, ApplicationStatus
from app.operations.auth import get_current_user, log_audit_action
from app.ai_services.config import (
    GLP_CATEGORIES, DNSH_CRITERIA, HIGH_RISK_SECTORS, 
    MEDIUM_RISK_SECTORS, LOW_RISK_SECTORS, settings
)
from app.ai_services.esg_framework import esg_framework_engine
from app.ai_services.scoring import esg_scoring_engine

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def get_sector_risk_level(sector: str) -> Dict[str, Any]:
    """Determine sector risk level and return risk data."""
    sector_lower = sector.lower() if sector else ""
    
    # Check high risk
    for s in HIGH_RISK_SECTORS:
        if s.lower() in sector_lower or sector_lower in s.lower():
            return {
                "level": "high",
                "score": 85,
                "color": "#ef4444",
                "label": "High Risk",
                "description": f"{sector} is classified as a high-risk sector due to significant environmental impact potential."
            }
    
    # Check medium risk
    for s in MEDIUM_RISK_SECTORS:
        if s.lower() in sector_lower or sector_lower in s.lower():
            return {
                "level": "medium",
                "score": 55,
                "color": "#f59e0b",
                "label": "Medium Risk",
                "description": f"{sector} has moderate environmental risk factors that require monitoring."
            }
    
    # Check low risk
    for s in LOW_RISK_SECTORS:
        if s.lower() in sector_lower or sector_lower in s.lower():
            return {
                "level": "low",
                "score": 20,
                "color": "#22c55e",
                "label": "Low Risk",
                "description": f"{sector} is generally considered environmentally favorable."
            }
    
    # Default to medium if not found
    return {
        "level": "medium",
        "score": 50,
        "color": "#eab308",
        "label": "Medium Risk",
        "description": f"Sector risk assessment pending for {sector}."
    }


def calculate_questionnaire_score(questionnaire_data: Dict) -> Dict[str, Any]:
    """Calculate scores from ESG questionnaire responses."""
    if not questionnaire_data:
        return {"total": 0, "breakdown": {}, "max_score": 100}
    
    scoring_map = {
        "q_env_benefits": {"high": 10, "medium": 5, "low": 0},
        "q_data_available": {"comprehensive": 10, "partial": 5, "none": 0},
        "q_regulatory_compliance": {"fully_compliant": 10, "in_progress": 5, "non_compliant": 0},
        "q_social_risk": {"none": 10, "minor": 5, "high": 0},
        "q_rd_low_carbon": {"yes": 8, "no": 0},
        "q_union_agreement": {"yes": 5, "no": 0},
        "q_adopt_ghg_protocol": {"yes": 10, "no": 0},
        "q_published_climate_disclosures": {"yes": 10, "no": 0},
        "q_timebound_targets": {"yes": 12, "no": 0},
        "q_phaseout_highcarbon": {"yes": 10, "no": 0},
        "q_long_lived_highcarbon_assets": {"no": 5, "yes": -10},
    }
    
    total = 0
    breakdown = {}
    
    for key, values in scoring_map.items():
        answer = questionnaire_data.get(key, "").lower() if questionnaire_data.get(key) else ""
        score = values.get(answer, 0)
        total += score
        breakdown[key] = {"answer": questionnaire_data.get(key), "score": score}
    
    return {"total": max(0, total), "breakdown": breakdown, "max_score": 100}


def calculate_emissions_metrics(app_data: Dict) -> Dict[str, Any]:
    """Calculate emissions-related metrics."""
    scope1 = app_data.get("scope1_tco2") or 0
    scope2 = app_data.get("scope2_tco2") or 0
    scope3 = app_data.get("scope3_tco2") or 0
    total = scope1 + scope2 + scope3
    
    # Calculate percentages
    percentages = {
        "scope1": round((scope1 / total * 100) if total > 0 else 0, 1),
        "scope2": round((scope2 / total * 100) if total > 0 else 0, 1),
        "scope3": round((scope3 / total * 100) if total > 0 else 0, 1),
    }
    
    # Intensity calculation (per million currency)
    amount = app_data.get("amount_requested") or 1
    intensity = round(total / (amount / 1000000), 2) if amount > 0 else 0
    
    return {
        "scope1": scope1,
        "scope2": scope2,
        "scope3": scope3,
        "total": total,
        "percentages": percentages,
        "intensity_per_million": intensity,
        "baseline_year": app_data.get("baseline_year"),
        "target_reduction": app_data.get("target_reduction"),
    }


@router.get("/loan/{loan_id}/full")
async def get_full_analysis(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive analysis data for a loan application."""
    
    # Get loan application
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Get documents
    documents = db.query(Document).filter(Document.loan_id == loan_id).all()
    
    # Get audit logs
    audit_logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "LoanApplication",
        AuditLog.entity_id == loan_id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    # Load application_data.json if exists
    raw_json = loan_app.raw_application_json or {}
    
    # Build project data for analysis
    project_data = {
        "org_name": loan_app.org_name,
        "project_name": loan_app.project_name,
        "sector": loan_app.sector,
        "location": loan_app.location,
        "project_location": loan_app.project_location,
        "use_of_proceeds": loan_app.use_of_proceeds,
        "project_description": loan_app.project_description,
        "scope1_tco2": loan_app.scope1_tco2,
        "scope2_tco2": loan_app.scope2_tco2,
        "scope3_tco2": loan_app.scope3_tco2,
        "baseline_year": loan_app.baseline_year,
        "amount_requested": loan_app.amount_requested,
        "target_reduction": loan_app.target_reduction,
    }
    
    # Run GLP analysis
    uop_result = esg_framework_engine.validate_use_of_proceeds(
        loan_app.use_of_proceeds or "",
        loan_app.sector or "",
        loan_app.project_type or "New"
    )
    
    # Run DNSH assessment
    dnsh_results = esg_framework_engine.assess_dnsh(project_data, "")
    dnsh_summary = esg_framework_engine.get_dnsh_summary(dnsh_results)
    
    # Run carbon lock-in assessment
    carbon_result = esg_framework_engine.assess_carbon_lockin(project_data, "")
    
    # Get sector risk
    sector_risk = get_sector_risk_level(loan_app.sector)
    
    # Calculate questionnaire score
    questionnaire_score = calculate_questionnaire_score(loan_app.questionnaire_data)
    
    # Calculate emissions metrics
    emissions = calculate_emissions_metrics(project_data)
    
    # Build response
    return {
        "loan_id": loan_app.id,
        "loan_id_str": loan_app.loan_id,
        
        # Header info
        "header": {
            "project_name": loan_app.project_name,
            "org_name": loan_app.org_name,
            "status": loan_app.status.value if loan_app.status else "pending",
            "amount_requested": loan_app.amount_requested,
            "currency": loan_app.currency,
            "shareholder_entities": loan_app.shareholder_entities or 0,
            "sector": loan_app.sector,
            "created_at": loan_app.created_at.isoformat() if loan_app.created_at else None,
        },
        
        # General Info tab data
        "general_info": {
            "organization": raw_json.get("organization_details", {}),
            "project": raw_json.get("project_information", {}),
            "green_kpis": raw_json.get("green_qualification_and_kpis", {}),
            "questionnaire": raw_json.get("esg_compliance_questionnaire", {}),
            "documents": raw_json.get("supporting_documents", {}),
        },
        
        # ESG Analysis tab data
        "esg_analysis": {
            "esg_score": loan_app.esg_score,
            "glp_eligibility": loan_app.glp_eligibility,
            "glp_category": loan_app.glp_category or uop_result.get("glp_category"),
            "glp_confidence": uop_result.get("confidence", 0),
            "green_indicators": uop_result.get("green_indicators", []),
            "red_flags": uop_result.get("red_flags", []),
            "use_of_proceeds_valid": uop_result.get("is_valid", False),
            "dnsh_summary": dnsh_summary,
            "carbon_lockin": {
                "risk_level": carbon_result.risk_level.value,
                "indicators_found": carbon_result.indicators_found,
                "assessment": carbon_result.assessment,
                "recommendation": carbon_result.recommendation,
            },
            "sector_risk": sector_risk,
            "questionnaire_score": questionnaire_score,
        },
        
        # Statistics tab data
        "statistics": {
            "emissions": emissions,
            "financial": {
                "amount_requested": loan_app.amount_requested,
                "currency": loan_app.currency,
                "loan_tenor": loan_app.loan_tenor,
                "annual_revenue": loan_app.annual_revenue,
            },
            "kpi_metrics": loan_app.kpi_metrics or [],
            "reporting_frequency": loan_app.reporting_frequency,
            "benchmarks": {
                "sector_avg_esg": 65,  # Placeholder - would come from sector data
                "portfolio_avg_esg": 72,  # Placeholder
                "glp_threshold": 60,
            },
        },
        
        # Documents
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "category": doc.doc_category,
                "file_type": doc.file_type,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "extraction_status": doc.extraction_status,
            }
            for doc in documents
        ],
        
        # Audit trail
        "audit_logs": [
            {
                "id": log.id,
                "action": log.action,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "user_id": log.user_id,
                "data": log.data,
            }
            for log in audit_logs
        ],
    }


@router.post("/loan/{loan_id}/status")
async def update_loan_status(
    loan_id: int,
    status: str = Query(..., description="New status: pending, under_review, approved, rejected"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update loan application status."""
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Validate status
    valid_statuses = ["pending", "under_review", "approved", "rejected"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    old_status = loan_app.status.value if loan_app.status else "unknown"
    loan_app.status = ApplicationStatus(status)
    
    # Log the change
    user_id = current_user.id if current_user else None
    log_audit_action(
        db, "LoanApplication", loan_id, "status_change", user_id,
        {"old_status": old_status, "new_status": status}
    )
    
    db.commit()
    
    return {"success": True, "loan_id": loan_id, "new_status": status}


@router.get("/loan/{loan_id}/application-json")
async def get_application_json(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get raw application JSON data."""
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    # Try to load from file first
    loan_id_str = loan_app.loan_id
    json_path = settings.UPLOAD_DIR / loan_id_str / "application_data.json"
    
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fall back to database
    return loan_app.raw_application_json or {}
