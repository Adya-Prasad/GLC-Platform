"""
ESG Scoring Engine
Computes composite ESG scores based on data completeness, verifiability, GLP alignment.
"""

import logging
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

from app.core.config import settings, REQUIRED_FIELDS, GLP_CATEGORIES
from app.services.glp_rules import glp_rules_engine, DNSHStatus, RiskLevel

logger = logging.getLogger(__name__)


@dataclass
class SPTCalibration:
    kpi_name: str
    baseline_value: float
    spt_target: float
    target_year: int
    sector_baseline: float
    ambition_score: float
    is_ambitious: bool
    assessment: str


@dataclass
class ESGScore:
    total_score: float
    completeness_score: float
    verifiability_score: float
    glp_alignment_score: float
    dnsh_penalty: float
    carbon_penalty: float
    breakdown: Dict[str, Any]
    grade: str
    recommendations: List[str]


class SectorBaselineLoader:
    def __init__(self):
        self.baselines = {
            "Renewable Energy": {2023: 20.0, 2030: 12.0, 2050: 0.0},
            "Energy Efficiency": {2023: 150.0, 2030: 100.0, 2050: 20.0},
            "Clean Transportation": {2023: 100.0, 2030: 60.0, 2050: 0.0},
            "Green Buildings": {2023: 50.0, 2030: 35.0, 2050: 0.0},
            "default": {2023: 100.0, 2030: 80.0, 2050: 20.0},
        }
    
    def get_baseline(self, sector: str, year: int) -> float:
        data = self.baselines.get(sector, self.baselines['default'])
        if year in data:
            return data[year]
        years = sorted(data.keys())
        if year <= years[0]:
            return data[years[0]]
        if year >= years[-1]:
            return data[years[-1]]
        for i, y in enumerate(years):
            if y > year:
                r = (year - years[i-1]) / (y - years[i-1])
                return data[years[i-1]] + r * (data[y] - data[years[i-1]])
        return 100.0


class ESGScoringEngine:
    def __init__(self):
        self.baseline_loader = SectorBaselineLoader()
        self.weight_completeness = settings.ESG_WEIGHT_COMPLETENESS
        self.weight_verifiability = settings.ESG_WEIGHT_VERIFIABILITY
        self.weight_glp_alignment = settings.ESG_WEIGHT_GLP_ALIGNMENT
        self.spt_ambition_threshold = settings.SPT_AMBITION_THRESHOLD
    
    def calculate_completeness_score(self, project_data: Dict[str, Any]) -> Tuple[float, Dict[str, bool]]:
        field_status = {}
        present_count = 0
        for field in REQUIRED_FIELDS:
            value = project_data.get(field)
            is_present = value is not None and value != '' and value != 0
            field_status[field] = is_present
            if is_present:
                present_count += 1
        score = (present_count / len(REQUIRED_FIELDS)) * 100
        if project_data.get('document_count', 0) > 0:
            score = min(100, score + 10)
        return score, field_status
    
    def calculate_verifiability_score(self, claims: List[Dict], evidence: List[Dict]) -> Tuple[float, Dict]:
        if not claims:
            return 50.0, {"message": "No claims to verify"}
        verified = sum(1 for c in claims if c.get('confidence', 0) >= 0.6)
        return (verified / len(claims)) * 100, {'verified': verified, 'total': len(claims)}
    
    def calculate_glp_alignment_score(self, project_data: Dict, extracted_text: str = "") -> Tuple[float, Dict]:
        eligibility = glp_rules_engine.assess_glp_eligibility(project_data, extracted_text)
        score = 40 * eligibility.confidence if eligibility.is_eligible else 10.0
        if eligibility.category in GLP_CATEGORIES:
            score += 20 * eligibility.confidence
        mop_text = project_data.get('use_of_proceeds', '') + ' ' + extracted_text
        if any(kw in mop_text.lower() for kw in ['tracking', 'allocation']):
            score += 20
        if any(kw in mop_text.lower() for kw in ['annual report', 'disclosure']):
            score += 20
        return min(100, score), {'category': eligibility.category}
    
    def calculate_dnsh_penalty(self, project_data: Dict, extracted_text: str = "") -> Tuple[float, Dict]:
        dnsh = glp_rules_engine.assess_dnsh(project_data, extracted_text)
        summary = glp_rules_engine.get_dnsh_summary(dnsh)
        if not summary['overall_pass']:
            return 30.0, summary
        return summary['unclear_count'] * 5, summary
    
    def calculate_carbon_penalty(self, project_data: Dict, extracted_text: str = "") -> Tuple[float, Dict]:
        result = glp_rules_engine.assess_carbon_lockin(project_data, extracted_text)
        penalties = {RiskLevel.HIGH: 20.0, RiskLevel.MEDIUM: 10.0, RiskLevel.LOW: 0.0}
        return penalties[result.risk_level], {'risk_level': result.risk_level.value}
    
    def calibrate_spt(self, kpi_name: str, baseline: float, target: float, year: int, sector: str) -> SPTCalibration:
        sector_baseline = self.baseline_loader.get_baseline(sector, year)
        ambition = max(0, min(1, 1 - (target / sector_baseline))) if target < sector_baseline else 0
        return SPTCalibration(kpi_name, baseline, target, year, sector_baseline, ambition, ambition >= 0.2, "")
    
    def calculate_composite_score(self, project_data: Dict, claims: List = None, evidence: List = None, extracted_text: str = "") -> ESGScore:
        claims, evidence = claims or [], evidence or []
        comp, comp_d = self.calculate_completeness_score(project_data)
        verif, verif_d = self.calculate_verifiability_score(claims, evidence)
        glp, glp_d = self.calculate_glp_alignment_score(project_data, extracted_text)
        dnsh_p, dnsh_d = self.calculate_dnsh_penalty(project_data, extracted_text)
        carbon_p, carbon_d = self.calculate_carbon_penalty(project_data, extracted_text)
        total = max(0, min(100, comp * 0.20 + verif * 0.25 + glp * 0.25 - dnsh_p - carbon_p))
        grade = 'A+' if total >= 90 else 'A' if total >= 80 else 'B' if total >= 70 else 'C' if total >= 60 else 'D' if total >= 50 else 'F'
        recs = []
        if comp < 80: recs.append("Improve data completeness")
        if verif < 60: recs.append("Upload supporting documents")
        if dnsh_p > 0: recs.append("Address DNSH concerns")
        return ESGScore(round(total, 1), round(comp, 1), round(verif, 1), round(glp, 1), dnsh_p, carbon_p, 
                       {'completeness': comp_d, 'glp': glp_d, 'dnsh': dnsh_d, 'carbon': carbon_d}, grade, recs or ["Strong ESG profile"])


esg_scoring_engine = ESGScoringEngine()
