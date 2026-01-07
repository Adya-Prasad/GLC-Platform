"""
Report Generation Service
Generate GLP investor reports in JSON and PDF formats.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid
import json
from sqlalchemy.orm import Session

from app.models.orm_models import LoanApplication, Document, KPI, Verification
from app.core.config import settings
from app.utils.storage import get_loan_dir

logger = logging.getLogger(__name__)


class ReportService:
    """Generate compliance and investor reports."""
    
    def generate_report(self, db: Session, loan_id: int, format: str = "json") -> Dict[str, Any]:
        """Generate GLP investor report."""
        
        # Get loan application with related data
        loan_app = db.query(LoanApplication).filter(LoanApplication.id == loan_id).first()
        if not loan_app:
            raise ValueError(f"Loan application {loan_id} not found")
        
        borrower = loan_app.borrower
        documents = loan_app.documents
        kpis = loan_app.kpis
        verifications = loan_app.verifications
        
        # Build report data
        report_id = f"GLP-{loan_id}-{uuid.uuid4().hex[:8].upper()}"
        
        report_data = {
            "report_id": report_id,
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "GLP Investor Report",
            
            "project_summary": {
                "project_name": loan_app.project_name,
                "borrower": borrower.org_name if borrower else "none",
                "sector": loan_app.sector,
                "location": loan_app.location,
                "project_type": loan_app.project_type,
                "loan_amount": f"{loan_app.currency} {loan_app.amount_requested:,.2f}",
                "application_status": loan_app.status.value if loan_app.status else "none",
                "use_of_proceeds": loan_app.use_of_proceeds,
            },
            
            "glp_eligibility": {
                "is_eligible": loan_app.glp_eligibility,
                "category": loan_app.glp_category,
                "carbon_lockin_risk": loan_app.carbon_lockin_risk,
                "dnsh_assessment": loan_app.dnsh_status or {},
            },
            
            "emissions_profile": {
                "scope1_tco2": loan_app.scope1_tco2,
                "scope2_tco2": loan_app.scope2_tco2,
                "scope3_tco2": loan_app.scope3_tco2,
                "total_tco2": loan_app.total_tco2,
                "baseline_year": loan_app.baseline_year,
            },
            
            "kpi_table": [
                {
                    "kpi_name": kpi.kpi_name,
                    "unit": kpi.unit,
                    "baseline_value": kpi.baseline_value,
                    "current_value": kpi.current_value,
                    "spt_target": kpi.spt_target,
                    "target_year": kpi.target_year,
                    "is_ambitious": kpi.is_ambitious,
                } for kpi in kpis
            ],
            
            "verification_summary": {
                "total_verifications": len(verifications),
                "latest_verification": {
                    "date": verifications[-1].created_at.isoformat() if verifications else None,
                    "result": verifications[-1].result.value if verifications else None,
                    "confidence": verifications[-1].confidence if verifications else None,
                } if verifications else None,
                "evidence_count": sum(len(v.evidence or []) for v in verifications),
            },
            
            "esg_composite_score": {
                "total_score": loan_app.esg_score,
                "grade": self._get_grade(loan_app.esg_score or 0),
                "breakdown": loan_app.parsed_fields.get('esg_breakdown', {}) if loan_app.parsed_fields else {},
            },
            
            "supporting_documents": [
                {
                    "filename": doc.filename,
                    "uploaded_at": doc.uploaded_at.isoformat(),
                    "status": doc.extraction_status,
                } for doc in documents
            ],
            
            "recommendations": self._generate_recommendations(loan_app),
        }
        
        # Save report JSON into loan-specific folder
        try:
            loan_dir = get_loan_dir(loan_app.loan_id)
            with open(loan_dir / f"{report_id}.json", "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Could not write report JSON to loan dir: {e}")

        if format == "pdf":
            pdf_path = self._generate_pdf(report_data, loan_app.loan_id)
            report_data["pdf_url"] = str(pdf_path)

        return report_data
    
    def _get_grade(self, score: float) -> str:
        if score >= 90: return 'A+'
        elif score >= 80: return 'A'
        elif score >= 70: return 'B'
        elif score >= 60: return 'C'
        elif score >= 50: return 'D'
        else: return 'F'
    
    def _generate_recommendations(self, loan_app: LoanApplication) -> list:
        recs = []
        if not loan_app.glp_eligibility:
            recs.append("Review use of proceeds to align with GLP eligible categories")
        if loan_app.carbon_lockin_risk == "high":
            recs.append("Develop transition strategy to mitigate carbon lock-in risk")
        if (loan_app.esg_score or 0) < 70:
            recs.append("Improve data completeness and documentation")
        if not loan_app.kpis:
            recs.append("Define KPIs and SPTs for sustainability tracking")
        if not recs:
            recs.append("Strong GLP alignment. Continue annual reporting.")
        return recs
    
    def _generate_pdf(self, report_data: Dict[str, Any], loan_id: str) -> Path:
        """Generate PDF report into loan-specific folder (uses loan_assets/LOAN_ID)."""
        report_dir = get_loan_dir(loan_id)
        report_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{report_data['report_id']}.pdf"
        pdf_path = report_dir / filename
        
        # Create HTML template
        html_content = self._build_html_report(report_data)
        
        try:
            from weasyprint import HTML
            HTML(string=html_content).write_pdf(pdf_path)
            logger.info(f"PDF report generated: {pdf_path}")
        except Exception:
            # Fallback: save as HTML
            html_path = report_dir / f"{report_data['report_id']}.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            pdf_path = html_path
            logger.warning("WeasyPrint not available or failed, saved as HTML")
        
        return pdf_path
    
    def _build_html_report(self, data: Dict[str, Any]) -> str:
        """Build HTML report template."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GLP Report - {data['report_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; color: #333; }}
        h1 {{ color: #2e7d32; border-bottom: 2px solid #2e7d32; padding-bottom: 10px; }}
        h2 {{ color: #388e3c; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #e8f5e9; }}
        .score {{ font-size: 2em; color: #2e7d32; font-weight: bold; }}
        .eligible {{ color: #2e7d32; font-weight: bold; }}
        .not-eligible {{ color: #c62828; font-weight: bold; }}
        .section {{ margin: 20px 0; padding: 15px; background: #f5f5f5; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>GLP Investor Report</h1>
    <p><strong>Report ID:</strong> {data['report_id']}</p>
    <p><strong>Generated:</strong> {data['generated_at']}</p>
    
    <h2>Project Summary</h2>
    <div class="section">
        <p><strong>Project:</strong> {data['project_summary']['project_name']}</p>
        <p><strong>Borrower:</strong> {data['project_summary']['borrower']}</p>
        <p><strong>Sector:</strong> {data['project_summary']['sector']}</p>
        <p><strong>Location:</strong> {data['project_summary']['location']}</p>
        <p><strong>Loan Amount:</strong> {data['project_summary']['loan_amount']}</p>
    </div>
    
    <h2>GLP Eligibility</h2>
    <div class="section">
        <p class="{'eligible' if data['glp_eligibility']['is_eligible'] else 'not-eligible'}">
            {'✓ ELIGIBLE' if data['glp_eligibility']['is_eligible'] else '✗ NOT ELIGIBLE'}
        </p>
        <p><strong>Category:</strong> {data['glp_eligibility']['category']}</p>
        <p><strong>Carbon Lock-in Risk:</strong> {data['glp_eligibility']['carbon_lockin_risk']}</p>
    </div>
    
    <h2>ESG Score</h2>
    <div class="section">
        <p class="score">{data['esg_composite_score']['total_score']} ({data['esg_composite_score']['grade']})</p>
    </div>
    
    <h2>Emissions Profile</h2>
    <table>
        <tr><th>Scope</th><th>tCO2</th></tr>
        <tr><td>Scope 1</td><td>{data['emissions_profile']['scope1_tco2'] or 'N/A'}</td></tr>
        <tr><td>Scope 2</td><td>{data['emissions_profile']['scope2_tco2'] or 'N/A'}</td></tr>
        <tr><td>Scope 3</td><td>{data['emissions_profile']['scope3_tco2'] or 'N/A'}</td></tr>
        <tr><th>Total</th><th>{data['emissions_profile']['total_tco2'] or 'N/A'}</th></tr>
    </table>
    
    <h2>Recommendations</h2>
    <ul>
        {''.join(f'<li>{r}</li>' for r in data['recommendations'])}
    </ul>
</body>
</html>
"""


report_service = ReportService()
