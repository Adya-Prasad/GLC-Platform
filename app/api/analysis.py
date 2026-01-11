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
    MEDIUM_RISK_SECTORS, LOW_RISK_SECTORS, settings,
    GLP_CORE_COMPONENTS, SLLP_CORE_COMPONENTS, SBTI_THRESHOLDS
)
from app.ai_services.esg_framework import esg_framework_engine
from app.ai_services.scoring import esg_scoring_engine
from app.ai_services.metrics import calculate_all_metrics

router = APIRouter(prefix="/analysis", tags=["Analysis"])


def assess_glp_compliance(loan_app, uop_result, dnsh_summary) -> Dict[str, Any]:
    """
    Assess compliance with LMA Green Loan Principles four core components.
    Returns detailed compliance status for each component.
    """
    compliance = {
        "overall_compliant": False,
        "score": 0,
        "max_score": 4,
        "components": {}
    }
    
    # 1. Use of Proceeds
    uop_compliant = uop_result.get("is_valid", False)
    compliance["components"]["use_of_proceeds"] = {
        "name": "Use of Proceeds",
        "compliant": uop_compliant,
        "details": uop_result.get("assessment", ""),
        "category": uop_result.get("glp_category", "Unknown"),
        "confidence": uop_result.get("confidence", 0)
    }
    if uop_compliant:
        compliance["score"] += 1
    
    # 2. Project Evaluation and Selection
    has_objectives = bool(loan_app.use_of_proceeds and loan_app.project_description)
    has_risk_mgmt = bool(loan_app.questionnaire_data)
    eval_compliant = has_objectives and has_risk_mgmt
    compliance["components"]["project_evaluation"] = {
        "name": "Project Evaluation & Selection",
        "compliant": eval_compliant,
        "details": "Environmental objectives communicated" if has_objectives else "Missing project objectives",
        "has_objectives": has_objectives,
        "has_risk_management": has_risk_mgmt
    }
    if eval_compliant:
        compliance["score"] += 1
    
    # 3. Management of Proceeds
    # For this demo, we assume proceeds are tracked if loan is created
    mgmt_compliant = True
    compliance["components"]["management_of_proceeds"] = {
        "name": "Management of Proceeds",
        "compliant": mgmt_compliant,
        "details": "Proceeds tracking established via platform",
        "tracking_method": "Dedicated loan account tracking"
    }
    if mgmt_compliant:
        compliance["score"] += 1
    
    # 4. Reporting
    has_reporting = bool(loan_app.reporting_frequency)
    has_kpis = bool(loan_app.kpi_metrics and len(loan_app.kpi_metrics) > 0)
    has_baseline = bool(loan_app.baseline_year)
    reporting_compliant = has_reporting and (has_kpis or has_baseline)
    compliance["components"]["reporting"] = {
        "name": "Reporting",
        "compliant": reporting_compliant,
        "details": f"Reporting frequency: {loan_app.reporting_frequency or 'Not specified'}",
        "has_reporting_commitment": has_reporting,
        "has_kpis": has_kpis,
        "has_baseline": has_baseline
    }
    if reporting_compliant:
        compliance["score"] += 1
    
    # Overall compliance
    compliance["overall_compliant"] = compliance["score"] >= 3  # At least 3 of 4 components
    compliance["percentage"] = round((compliance["score"] / compliance["max_score"]) * 100)
    
    return compliance


def assess_sll_compliance(loan_app) -> Dict[str, Any]:
    """
    Assess compliance with LMA Sustainability-Linked Loan Principles.
    """
    compliance = {
        "applicable": False,
        "score": 0,
        "max_score": 5,
        "components": {}
    }
    
    # Check if this is an SLL (has KPIs and targets)
    has_kpis = bool(loan_app.kpi_metrics and len(loan_app.kpi_metrics) > 0)
    has_targets = bool(loan_app.target_reduction)
    
    # Convert target_reduction to float safely
    try:
        target_reduction_val = float(loan_app.target_reduction) if loan_app.target_reduction else 0
    except (ValueError, TypeError):
        target_reduction_val = 0
    
    if not (has_kpis or has_targets):
        compliance["applicable"] = False
        compliance["message"] = "Not structured as Sustainability-Linked Loan"
        return compliance
    
    compliance["applicable"] = True
    
    # 1. KPI Selection
    kpi_compliant = has_kpis
    compliance["components"]["kpi_selection"] = {
        "name": "Selection of KPIs",
        "compliant": kpi_compliant,
        "kpis": loan_app.kpi_metrics or [],
        "count": len(loan_app.kpi_metrics) if loan_app.kpi_metrics else 0
    }
    if kpi_compliant:
        compliance["score"] += 1
    
    # 2. SPT Calibration
    spt_compliant = has_targets and target_reduction_val >= 10  # At least 10% reduction
    compliance["components"]["spt_calibration"] = {
        "name": "Calibration of SPTs",
        "compliant": spt_compliant,
        "target_reduction": target_reduction_val,
        "is_ambitious": target_reduction_val >= 20
    }
    if spt_compliant:
        compliance["score"] += 1
    
    # 3. Loan Characteristics (margin adjustment - assumed for demo)
    compliance["components"]["loan_characteristics"] = {
        "name": "Loan Characteristics",
        "compliant": True,
        "details": "Margin adjustment mechanism available"
    }
    compliance["score"] += 1
    
    # 4. Reporting
    reporting_compliant = bool(loan_app.reporting_frequency)
    compliance["components"]["reporting"] = {
        "name": "Reporting",
        "compliant": reporting_compliant,
        "frequency": loan_app.reporting_frequency
    }
    if reporting_compliant:
        compliance["score"] += 1
    
    # 5. Verification (external review)
    # For demo, check if documents include verification
    compliance["components"]["verification"] = {
        "name": "Verification",
        "compliant": False,
        "details": "External verification recommended"
    }
    
    compliance["percentage"] = round((compliance["score"] / compliance["max_score"]) * 100)
    
    return compliance


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


def calculate_dynamic_esg_score(
    questionnaire_score: Dict,
    glp_compliance: Dict,
    dnsh_summary: Dict,
    sector_risk: Dict,
    uop_result: Dict,
    loan_app
) -> float:
    """
    Calculate a comprehensive ESG score based on multiple factors.
    Returns a score from 0-100.
    """
    score = 0.0
    max_score = 100.0
    
    # 1. Questionnaire Score (25 points max)
    q_score = questionnaire_score.get("total", 0)
    q_max = questionnaire_score.get("max_score", 100)
    questionnaire_contribution = (q_score / q_max * 25) if q_max > 0 else 0
    score += questionnaire_contribution
    
    # 2. GLP Compliance (25 points max)
    glp_score = glp_compliance.get("score", 0)
    glp_max = glp_compliance.get("max_score", 4)
    glp_contribution = (glp_score / glp_max * 25) if glp_max > 0 else 0
    score += glp_contribution
    
    # 3. DNSH Assessment (20 points max)
    if dnsh_summary.get("overall_pass", False):
        dnsh_contribution = 20
    else:
        passed = dnsh_summary.get("passed_count", 0)
        total = dnsh_summary.get("passed_count", 0) + dnsh_summary.get("failed_count", 0) + dnsh_summary.get("unclear_count", 0)
        dnsh_contribution = (passed / total * 15) if total > 0 else 5
    score += dnsh_contribution
    
    # 4. Sector Risk (15 points max) - Lower risk = higher score
    risk_level = sector_risk.get("level", "medium")
    if risk_level == "low":
        score += 15
    elif risk_level == "medium":
        score += 10
    else:  # high
        score += 5
    
    # 5. Use of Proceeds Validity (10 points max)
    if uop_result.get("is_valid", False):
        uop_confidence = uop_result.get("confidence", 0.5)
        score += 10 * uop_confidence
    
    # 6. Data Completeness Bonus (5 points max)
    completeness_fields = [
        loan_app.scope1_tco2, loan_app.scope2_tco2, loan_app.scope3_tco2,
        loan_app.baseline_year, loan_app.target_reduction, loan_app.kpi_metrics,
        loan_app.reporting_frequency
    ]
    filled = sum(1 for f in completeness_fields if f)
    completeness_bonus = (filled / len(completeness_fields)) * 5
    score += completeness_bonus
    
    # Ensure score is within bounds
    return round(min(max(score, 0), max_score), 1)


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
    
    # Calculate emissions metrics (basic)
    emissions = calculate_emissions_metrics(project_data)
    
    # Calculate comprehensive sustainability metrics
    sustainability_metrics = calculate_all_metrics(
        scope1=loan_app.scope1_tco2 or 0,
        scope2=loan_app.scope2_tco2 or 0,
        scope3=loan_app.scope3_tco2 or 0,
        annual_revenue=loan_app.annual_revenue or 0,
        sector=loan_app.sector or "",
        target_reduction=loan_app.target_reduction,
        baseline_year=loan_app.baseline_year,
        questionnaire_data=loan_app.questionnaire_data or {},
        glp_eligible=loan_app.glp_eligibility or uop_result.get("is_valid", False),
        sector_risk=sector_risk.get("level", "medium")
    )
    
    # Assess LMA GLP Compliance (Four Core Components)
    glp_compliance = assess_glp_compliance(loan_app, uop_result, dnsh_summary)
    
    # Assess SLL Compliance (if applicable)
    sll_compliance = assess_sll_compliance(loan_app)
    
    # Calculate ESG Score dynamically if not stored
    esg_score = loan_app.esg_score
    if esg_score is None:
        # Calculate composite ESG score based on multiple factors
        esg_score = calculate_dynamic_esg_score(
            questionnaire_score=questionnaire_score,
            glp_compliance=glp_compliance,
            dnsh_summary=dnsh_summary,
            sector_risk=sector_risk,
            uop_result=uop_result,
            loan_app=loan_app
        )
    
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
            # LMA Compliance Assessment
            "glp_compliance": glp_compliance,
            "sll_compliance": sll_compliance,
        },
        
        # Statistics tab data - comprehensive metrics
        "statistics": {
            **sustainability_metrics,
            "financial": {
                "amount_requested": loan_app.amount_requested,
                "currency": loan_app.currency,
                "loan_tenor": loan_app.loan_tenor,
                "annual_revenue": loan_app.annual_revenue,
            },
            "kpi_metrics": loan_app.kpi_metrics or [],
            "reporting_frequency": loan_app.reporting_frequency,
            "baseline_year": loan_app.baseline_year,
            "target_reduction": loan_app.target_reduction,
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


@router.get("/loan/{loan_id}/notes")
async def get_reviewer_notes(
    loan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get reviewer notes for a loan application."""
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    return {
        "loan_id": loan_id,
        "notes": loan_app.reviewer_notes or ""
    }


@router.post("/loan/{loan_id}/notes")
async def save_reviewer_notes(
    loan_id: int,
    notes: str = Query(..., description="Reviewer notes text"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save reviewer notes for a loan application."""
    
    loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
    if not loan_app:
        raise HTTPException(status_code=404, detail="Loan application not found")
    
    loan_app.reviewer_notes = notes
    
    # Log the action
    user_id = current_user.id if current_user else None
    log_audit_action(
        db, "LoanApplication", loan_id, "notes_saved", user_id,
        {"notes_length": len(notes)}
    )
    
    db.commit()
    
    return {"success": True, "loan_id": loan_id, "message": "Notes saved successfully"}
