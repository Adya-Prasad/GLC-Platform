"""
Sustainability Metrics Calculator
Calculates comprehensive metrics for green loan assessment based on:
- GHG Protocol standards
- Carbon intensity benchmarks by industry
- Transition credibility assessment
- SPT (Sustainability Performance Target) calibration
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import math


# Industry carbon intensity benchmarks (tCO2e per million USD revenue)
# Source: Compiled from EcoHedge 2024, WEF Net-Zero Tracker, PCAF standards
SECTOR_CARBON_BENCHMARKS = {
    "Fossil fuel utilities": {"intensity": 2500, "risk": "high", "pathway_target_2030": 1500},
    "Oil & gas": {"intensity": 2200, "risk": "high", "pathway_target_2030": 1200},
    "Mining and quarrying": {"intensity": 1800, "risk": "high", "pathway_target_2030": 1000},
    "Chemicals": {"intensity": 1200, "risk": "high", "pathway_target_2030": 700},
    "Heavy Industry": {"intensity": 1500, "risk": "high", "pathway_target_2030": 900},
    "Aviation": {"intensity": 1100, "risk": "high", "pathway_target_2030": 650},
    "Transportation and storage": {"intensity": 800, "risk": "medium", "pathway_target_2030": 450},
    "Construction materials": {"intensity": 900, "risk": "medium", "pathway_target_2030": 500},
    "Agriculture, forestry, and fishing": {"intensity": 600, "risk": "medium", "pathway_target_2030": 350},
    "Construction": {"intensity": 400, "risk": "medium", "pathway_target_2030": 250},
    "Manufacturing of machinery and equipment": {"intensity": 350, "risk": "medium", "pathway_target_2030": 200},
    "Food and beverage": {"intensity": 300, "risk": "medium", "pathway_target_2030": 180},
    "Water supply, sewerage and waste management": {"intensity": 250, "risk": "medium", "pathway_target_2030": 150},
    "Wholesale and retail trade": {"intensity": 150, "risk": "low", "pathway_target_2030": 90},
    "Real estate activities": {"intensity": 120, "risk": "low", "pathway_target_2030": 70},
    "Healthcare services": {"intensity": 100, "risk": "low", "pathway_target_2030": 60},
    "Information technology services": {"intensity": 80, "risk": "low", "pathway_target_2030": 50},
    "Financial and insurance activities": {"intensity": 50, "risk": "low", "pathway_target_2030": 30},
    "Education services": {"intensity": 40, "risk": "low", "pathway_target_2030": 25},
    "Renewable energy": {"intensity": 20, "risk": "low", "pathway_target_2030": 10},
    "Professional, scientific and technical services": {"intensity": 60, "risk": "low", "pathway_target_2030": 35},
}

DEFAULT_BENCHMARK = {"intensity": 200, "risk": "medium", "pathway_target_2030": 120}


@dataclass
class TransitionScore:
    """Transition Evidence & Credibility Assessment"""
    total_score: float  # 0-100
    governance_score: float  # Climate governance (0-25)
    alignment_score: float  # Paris alignment (0-25)
    emissions_score: float  # Emissions trajectory (0-25)
    ambition_score: float  # Target ambition (0-25)
    grade: str  # A, B, C, D, F
    assessment: str


@dataclass
class CarbonMetrics:
    """Carbon footprint and intensity metrics"""
    total_emissions: float  # tCO2e
    scope1: float
    scope2: float
    scope3: float
    carbon_intensity: float  # tCO2e per million revenue
    sector_benchmark: float  # Industry average
    benchmark_performance: str  # "above", "at", "below" benchmark
    performance_ratio: float  # Actual / Benchmark (lower is better)
    absolute_reduction_potential: float  # If target_reduction provided
    intensity_reduction_potential: float


@dataclass
class SPTMetrics:
    """Sustainability Performance Target metrics"""
    baseline_emissions: float
    target_emissions: float
    target_year: int
    reduction_percentage: float
    annual_reduction_rate: float  # CAGR needed
    is_science_based: bool  # Aligned with 1.5°C pathway (~4.2% annual)
    ambition_level: str  # "low", "moderate", "ambitious", "science-based"
    pathway_alignment: float  # 0-100% aligned with sector pathway


def get_sector_benchmark(sector: str) -> Dict[str, Any]:
    """Get carbon benchmark for a sector"""
    # Try exact match first
    if sector in SECTOR_CARBON_BENCHMARKS:
        return SECTOR_CARBON_BENCHMARKS[sector]
    
    # Try partial match
    sector_lower = sector.lower()
    for key, value in SECTOR_CARBON_BENCHMARKS.items():
        if key.lower() in sector_lower or sector_lower in key.lower():
            return value
    
    return DEFAULT_BENCHMARK


def calculate_carbon_intensity(total_emissions: float, annual_revenue: float) -> float:
    """Calculate carbon intensity (tCO2e per million USD revenue)"""
    if not annual_revenue or annual_revenue <= 0:
        return 0
    return round((total_emissions / annual_revenue) * 1_000_000, 2)


def calculate_transition_score(
    questionnaire_data: Dict,
    has_targets: bool,
    target_reduction: float,
    has_baseline: bool,
    sector_risk: str,
    glp_eligible: bool
) -> TransitionScore:
    """
    Calculate Transition Evidence & Credibility Score
    Based on: governance + alignment + emissions trajectory + ambition
    """
    score = 0
    
    # 1. Governance Score (0-25) - Climate governance and disclosure
    governance = 0
    if questionnaire_data:
        if questionnaire_data.get("q_adopt_ghg_protocol") == "yes":
            governance += 8
        if questionnaire_data.get("q_published_climate_disclosures") == "yes":
            governance += 8
        if questionnaire_data.get("q_regulatory_compliance") == "fully_compliant":
            governance += 9
        elif questionnaire_data.get("q_regulatory_compliance") == "in_progress":
            governance += 5
    governance = min(25, governance)
    
    # 2. Alignment Score (0-25) - Paris/taxonomy alignment
    alignment = 0
    if glp_eligible:
        alignment += 15
    if questionnaire_data:
        if questionnaire_data.get("q_timebound_targets") == "yes":
            alignment += 5
        if questionnaire_data.get("q_phaseout_highcarbon") == "yes":
            alignment += 5
    alignment = min(25, alignment)
    
    # 3. Emissions Score (0-25) - Based on sector risk and data availability
    emissions = 0
    if has_baseline:
        emissions += 10
    if has_targets:
        emissions += 10
    if sector_risk == "low":
        emissions += 5
    elif sector_risk == "medium":
        emissions += 3
    emissions = min(25, emissions)
    
    # 4. Ambition Score (0-25) - Target ambition level
    ambition = 0
    if target_reduction:
        try:
            reduction = float(target_reduction)
            if reduction >= 50:
                ambition = 25
            elif reduction >= 30:
                ambition = 20
            elif reduction >= 20:
                ambition = 15
            elif reduction >= 10:
                ambition = 10
            else:
                ambition = 5
        except:
            ambition = 0
    ambition = min(25, ambition)
    
    total = governance + alignment + emissions + ambition
    
    # Determine grade
    if total >= 85:
        grade = "A"
    elif total >= 70:
        grade = "B"
    elif total >= 55:
        grade = "C"
    elif total >= 40:
        grade = "D"
    else:
        grade = "F"
    
    # Assessment text
    if total >= 70:
        assessment = "Strong transition credibility with clear climate governance and ambitious targets."
    elif total >= 50:
        assessment = "Moderate transition evidence. Consider strengthening climate disclosures and targets."
    else:
        assessment = "Limited transition evidence. Recommend establishing baseline data and science-based targets."
    
    return TransitionScore(
        total_score=round(total, 1),
        governance_score=governance,
        alignment_score=alignment,
        emissions_score=emissions,
        ambition_score=ambition,
        grade=grade,
        assessment=assessment
    )


def calculate_carbon_metrics(
    scope1: float,
    scope2: float,
    scope3: float,
    annual_revenue: float,
    sector: str,
    target_reduction: Optional[float] = None
) -> CarbonMetrics:
    """Calculate comprehensive carbon metrics"""
    total = (scope1 or 0) + (scope2 or 0) + (scope3 or 0)
    
    # Get sector benchmark
    benchmark_data = get_sector_benchmark(sector)
    sector_benchmark = benchmark_data["intensity"]
    
    # Calculate intensity
    intensity = calculate_carbon_intensity(total, annual_revenue)
    
    # Benchmark comparison
    if intensity <= 0 or sector_benchmark <= 0:
        performance = "unknown"
        ratio = 0
    elif intensity < sector_benchmark * 0.8:
        performance = "below"  # Better than benchmark
        ratio = round(intensity / sector_benchmark, 2)
    elif intensity <= sector_benchmark * 1.2:
        performance = "at"
        ratio = round(intensity / sector_benchmark, 2)
    else:
        performance = "above"  # Worse than benchmark
        ratio = round(intensity / sector_benchmark, 2)
    
    # Reduction potentials
    absolute_reduction = 0
    intensity_reduction = 0
    if target_reduction:
        try:
            reduction_pct = float(target_reduction) / 100
            absolute_reduction = round(total * reduction_pct, 2)
            intensity_reduction = round(intensity * reduction_pct, 2)
        except:
            pass
    
    return CarbonMetrics(
        total_emissions=total,
        scope1=scope1 or 0,
        scope2=scope2 or 0,
        scope3=scope3 or 0,
        carbon_intensity=intensity,
        sector_benchmark=sector_benchmark,
        benchmark_performance=performance,
        performance_ratio=ratio,
        absolute_reduction_potential=absolute_reduction,
        intensity_reduction_potential=intensity_reduction
    )


def calculate_spt_metrics(
    total_emissions: float,
    target_reduction: Optional[float],
    baseline_year: Optional[int],
    target_year: int = 2030,
    sector: str = ""
) -> Optional[SPTMetrics]:
    """Calculate SPT (Sustainability Performance Target) metrics"""
    if not target_reduction or not total_emissions:
        return None
    
    try:
        reduction_pct = float(target_reduction)
    except:
        return None
    
    target_emissions = total_emissions * (1 - reduction_pct / 100)
    
    # Calculate years to target
    current_year = 2025
    base_year = baseline_year or current_year
    years_to_target = max(1, target_year - base_year)
    
    # Calculate annual reduction rate (CAGR)
    if total_emissions > 0 and target_emissions >= 0:
        annual_rate = (1 - (target_emissions / total_emissions) ** (1 / years_to_target)) * 100
    else:
        annual_rate = 0
    
    # Science-based target check (1.5°C pathway requires ~4.2% annual reduction)
    is_science_based = annual_rate >= 4.2
    
    # Ambition level
    if annual_rate >= 7:
        ambition = "science-based"
    elif annual_rate >= 4.2:
        ambition = "ambitious"
    elif annual_rate >= 2.5:
        ambition = "moderate"
    else:
        ambition = "low"
    
    # Pathway alignment (compare to sector 2030 target)
    benchmark = get_sector_benchmark(sector)
    pathway_target = benchmark.get("pathway_target_2030", benchmark["intensity"])
    current_benchmark = benchmark["intensity"]
    
    if current_benchmark > 0:
        required_reduction = ((current_benchmark - pathway_target) / current_benchmark) * 100
        pathway_alignment = min(100, (reduction_pct / required_reduction) * 100) if required_reduction > 0 else 100
    else:
        pathway_alignment = 50
    
    return SPTMetrics(
        baseline_emissions=total_emissions,
        target_emissions=round(target_emissions, 2),
        target_year=target_year,
        reduction_percentage=reduction_pct,
        annual_reduction_rate=round(annual_rate, 2),
        is_science_based=is_science_based,
        ambition_level=ambition,
        pathway_alignment=round(pathway_alignment, 1)
    )


def calculate_all_metrics(
    scope1: float,
    scope2: float,
    scope3: float,
    annual_revenue: float,
    sector: str,
    target_reduction: Optional[float],
    baseline_year: Optional[int],
    questionnaire_data: Dict,
    glp_eligible: bool,
    sector_risk: str
) -> Dict[str, Any]:
    """Calculate all sustainability metrics for the Statistics tab"""
    
    total_emissions = (scope1 or 0) + (scope2 or 0) + (scope3 or 0)
    
    # Carbon metrics
    carbon = calculate_carbon_metrics(
        scope1, scope2, scope3, annual_revenue, sector, target_reduction
    )
    
    # Transition score
    transition = calculate_transition_score(
        questionnaire_data,
        has_targets=bool(target_reduction),
        target_reduction=target_reduction,
        has_baseline=bool(baseline_year),
        sector_risk=sector_risk,
        glp_eligible=glp_eligible
    )
    
    # SPT metrics
    spt = calculate_spt_metrics(
        total_emissions, target_reduction, baseline_year, 2030, sector
    )
    
    # Emissions breakdown percentages
    if total_emissions > 0:
        scope1_pct = round((scope1 or 0) / total_emissions * 100, 1)
        scope2_pct = round((scope2 or 0) / total_emissions * 100, 1)
        scope3_pct = round((scope3 or 0) / total_emissions * 100, 1)
    else:
        scope1_pct = scope2_pct = scope3_pct = 0
    
    return {
        "emissions": {
            "total": total_emissions,
            "scope1": scope1 or 0,
            "scope2": scope2 or 0,
            "scope3": scope3 or 0,
            "scope1_pct": scope1_pct,
            "scope2_pct": scope2_pct,
            "scope3_pct": scope3_pct,
        },
        "carbon_intensity": {
            "value": carbon.carbon_intensity,
            "unit": "tCO2e/M USD",
            "sector_benchmark": carbon.sector_benchmark,
            "performance": carbon.benchmark_performance,
            "ratio": carbon.performance_ratio,
        },
        "transition_score": {
            "total": transition.total_score,
            "governance": transition.governance_score,
            "alignment": transition.alignment_score,
            "emissions": transition.emissions_score,
            "ambition": transition.ambition_score,
            "grade": transition.grade,
            "assessment": transition.assessment,
        },
        "spt_metrics": {
            "baseline_emissions": spt.baseline_emissions if spt else total_emissions,
            "target_emissions": spt.target_emissions if spt else None,
            "reduction_percentage": spt.reduction_percentage if spt else None,
            "annual_reduction_rate": spt.annual_reduction_rate if spt else None,
            "is_science_based": spt.is_science_based if spt else False,
            "ambition_level": spt.ambition_level if spt else "unknown",
            "pathway_alignment": spt.pathway_alignment if spt else 0,
        } if spt else None,
        "reduction_potential": {
            "absolute": carbon.absolute_reduction_potential,
            "intensity": carbon.intensity_reduction_potential,
        },
        "sector_benchmark": get_sector_benchmark(sector),
    }
