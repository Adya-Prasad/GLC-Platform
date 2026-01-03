"""
GLP Rules Engine
Implements LMA Green Loan Principles compliance checks including:
- Use of Proceeds validation
- DNSH (Do No Significant Harm) assessment
- Carbon Lock-in risk evaluation
- GLP eligibility determination
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.core.config import (
    GLP_CATEGORIES, DNSH_CRITERIA, CARBON_LOCKIN_INDICATORS,
    HIGH_RISK_SECTORS
)

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DNSHStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCLEAR = "unclear"
    NOT_APPLICABLE = "n/a"


@dataclass
class DNSHResult:
    """Result of a DNSH criterion check."""
    criterion: str
    status: DNSHStatus
    evidence: str
    notes: str


@dataclass
class CarbonLockinResult:
    """Result of carbon lock-in risk assessment."""
    risk_level: RiskLevel
    indicators_found: List[str]
    assessment: str
    recommendation: str


@dataclass
class GlpEligibilityResult:
    """Result of GLP eligibility assessment."""
    is_eligible: bool
    category: str
    confidence: float
    use_of_proceeds_valid: bool
    dnsh_pass: bool
    carbon_lockin_risk: RiskLevel
    issues: List[str]
    recommendations: List[str]


class GLPRulesEngine:
    """
    Implements Green Loan Principles compliance rules.
    Based on LMA Green Loan Principles framework.
    """
    
    def __init__(self):
        self.glp_categories = GLP_CATEGORIES
        self.dnsh_criteria = DNSH_CRITERIA
        self.carbon_lockin_indicators = CARBON_LOCKIN_INDICATORS
        self.high_risk_sectors = HIGH_RISK_SECTORS
    
    # ==================== Use of Proceeds ====================
    
    def validate_use_of_proceeds(
        self, 
        use_of_proceeds: str, 
        sector: str,
        project_type: str = "New"
    ) -> Dict[str, Any]:
        """
        Validate if use of proceeds aligns with GLP eligible categories.
        
        According to GLP:
        - Clear environmental benefits
        - Quantified where feasible
        - Aligned with eligible green project categories
        """
        use_lower = use_of_proceeds.lower()
        sector_lower = sector.lower()
        
        # Check for green keywords
        green_keywords = [
            "renewable", "solar", "wind", "hydro", "efficiency",
            "emission reduction", "clean", "sustainable", "recycling",
            "biodiversity", "conservation", "green", "low carbon",
            "electric vehicle", "public transport", "water treatment"
        ]
        
        # Check for red flags
        red_flags = [
            "fossil fuel expansion", "coal", "oil exploration",
            "mining without remediation", "deforestation"
        ]
        
        green_matches = [kw for kw in green_keywords if kw in use_lower]
        red_matches = [rf for rf in red_flags if rf in use_lower]
        
        # Determine validity
        is_valid = len(green_matches) > 0 and len(red_matches) == 0
        
        # Map to GLP category
        category, confidence = self._map_to_glp_category(use_of_proceeds, sector)
        
        return {
            "is_valid": is_valid,
            "glp_category": category,
            "confidence": confidence,
            "green_indicators": green_matches,
            "red_flags": red_matches,
            "assessment": self._generate_uop_assessment(
                is_valid, category, green_matches, red_matches
            )
        }
    
    def _map_to_glp_category(
        self, 
        use_of_proceeds: str, 
        sector: str
    ) -> Tuple[str, float]:
        """Map project to GLP eligible category."""
        text = f"{use_of_proceeds} {sector}".lower()
        
        category_mapping = {
            "Renewable Energy": [
                "wind turbine", "solar panel", "solar farm", "hydropower",
                "geothermal", "biomass", "renewable energy", "wind farm"
            ],
            "Energy Efficiency": [
                "energy efficiency", "retrofit", "led lighting", "hvac upgrade",
                "smart meter", "building management", "insulation"
            ],
            "Clean Transportation": [
                "electric vehicle", "ev charging", "public transit", "rail",
                "bicycle infrastructure", "hydrogen fuel", "fleet electrification"
            ],
            "Green Buildings": [
                "green building", "leed certified", "breeam", "net zero",
                "sustainable construction", "eco-friendly building"
            ],
            "Sustainable Water and Wastewater Management": [
                "water treatment", "desalination", "wastewater", "water recycling",
                "stormwater management", "water efficiency"
            ],
            "Pollution Prevention and Control": [
                "emission control", "air quality", "pollution reduction",
                "waste management", "hazardous waste", "soil remediation"
            ],
            "Climate Change Adaptation": [
                "flood defense", "climate resilience", "drought management",
                "coastal protection", "climate adaptation"
            ]
        }
        
        best_category = "Unknown"
        best_score = 0.0
        
        for category, keywords in category_mapping.items():
            matches = sum(1 for kw in keywords if kw in text)
            if matches > 0:
                score = min(0.95, 0.5 + (matches * 0.15))
                if score > best_score:
                    best_score = score
                    best_category = category
        
        return best_category, best_score
    
    def _generate_uop_assessment(
        self,
        is_valid: bool,
        category: str,
        green_matches: List[str],
        red_flags: List[str]
    ) -> str:
        """Generate human-readable assessment of use of proceeds."""
        if is_valid:
            assessment = f"Project qualifies under GLP category: {category}. "
            assessment += f"Green indicators identified: {', '.join(green_matches[:5])}."
        else:
            if red_flags:
                assessment = f"Project does NOT qualify due to red flags: {', '.join(red_flags)}."
            else:
                assessment = "Insufficient evidence of environmental benefit. Please provide more details."
        
        return assessment
    
    # ==================== DNSH Assessment ====================
    
    def assess_dnsh(
        self,
        project_data: Dict[str, Any],
        extracted_text: str = ""
    ) -> Dict[str, DNSHResult]:
        """
        Assess Do No Significant Harm criteria.
        
        The six EU Taxonomy DNSH criteria:
        1. Climate change mitigation
        2. Climate change adaptation
        3. Sustainable use of water resources
        4. Circular economy
        5. Pollution prevention
        6. Biodiversity protection
        """
        results = {}
        combined_text = f"{project_data.get('use_of_proceeds', '')} {extracted_text}".lower()
        location = project_data.get('location', '').lower()
        sector = project_data.get('sector', '').lower()
        
        # 1. Climate Mitigation
        results['climate_mitigation'] = self._check_climate_mitigation(
            combined_text, sector, project_data
        )
        
        # 2. Climate Adaptation
        results['climate_adaptation'] = self._check_climate_adaptation(
            combined_text, location
        )
        
        # 3. Water Use
        results['water_use'] = self._check_water_use(
            combined_text, sector, location
        )
        
        # 4. Circular Economy
        results['circular_economy'] = self._check_circular_economy(
            combined_text, sector
        )
        
        # 5. Pollution Prevention
        results['pollution'] = self._check_pollution(
            combined_text, sector
        )
        
        # 6. Biodiversity
        results['biodiversity'] = self._check_biodiversity(
            combined_text, location, sector
        )
        
        return results
    
    def _check_climate_mitigation(
        self, text: str, sector: str, project_data: Dict
    ) -> DNSHResult:
        """Check if project contributes to climate mitigation."""
        # Check for GHG increasing activities
        negative_indicators = ["increased emissions", "coal", "fossil fuel expansion"]
        positive_indicators = ["emission reduction", "carbon neutral", "net zero", "renewable"]
        
        has_negative = any(ind in text for ind in negative_indicators)
        has_positive = any(ind in text for ind in positive_indicators)
        
        # Check absolute emissions
        total_co2 = (
            project_data.get('scope1_tco2', 0) or 0 +
            project_data.get('scope2_tco2', 0) or 0 +
            project_data.get('scope3_tco2', 0) or 0
        )
        
        if has_negative:
            return DNSHResult(
                criterion="climate_mitigation",
                status=DNSHStatus.FAIL,
                evidence=f"Negative indicators found in project description",
                notes="Project may lead to significant GHG emissions"
            )
        elif has_positive:
            return DNSHResult(
                criterion="climate_mitigation",
                status=DNSHStatus.PASS,
                evidence=f"Positive climate indicators: renewable energy, emission reduction",
                notes=f"Total reported emissions: {total_co2:,.0f} tCO2"
            )
        else:
            return DNSHResult(
                criterion="climate_mitigation",
                status=DNSHStatus.UNCLEAR,
                evidence="Insufficient information on climate impact",
                notes="Additional documentation required"
            )
    
    def _check_climate_adaptation(self, text: str, location: str) -> DNSHResult:
        """Check climate adaptation and resilience."""
        resilience_indicators = [
            "climate resilient", "flood protection", "drought resistant",
            "weather resilient", "climate risk assessment"
        ]
        
        vulnerability_indicators = [
            "flood zone", "coastal area", "hurricane", "wildfire"
        ]
        
        has_resilience = any(ind in text for ind in resilience_indicators)
        has_vulnerability = any(ind in location or ind in text for ind in vulnerability_indicators)
        
        if has_vulnerability and not has_resilience:
            return DNSHResult(
                criterion="climate_adaptation",
                status=DNSHStatus.UNCLEAR,
                evidence="Project in climate-vulnerable area without clear adaptation measures",
                notes="Climate risk assessment recommended"
            )
        elif has_resilience:
            return DNSHResult(
                criterion="climate_adaptation",
                status=DNSHStatus.PASS,
                evidence="Climate resilience measures identified",
                notes="Project includes adaptation considerations"
            )
        else:
            return DNSHResult(
                criterion="climate_adaptation",
                status=DNSHStatus.PASS,
                evidence="No significant climate vulnerability identified",
                notes="Standard climate risk applies"
            )
    
    def _check_water_use(self, text: str, sector: str, location: str) -> DNSHResult:
        """Check sustainable water use."""
        water_intensive = ["mining", "textile", "agriculture", "data center", "cooling"]
        water_positive = ["water recycling", "rainwater", "water efficiency", "water conservation"]
        water_stressed = ["desert", "arid", "drought", "water scarcity"]
        
        is_intensive = any(ind in sector or ind in text for ind in water_intensive)
        has_mitigation = any(ind in text for ind in water_positive)
        in_stressed_area = any(ind in location or ind in text for ind in water_stressed)
        
        if is_intensive and in_stressed_area and not has_mitigation:
            return DNSHResult(
                criterion="water_use",
                status=DNSHStatus.FAIL,
                evidence="Water-intensive activity in water-stressed region without mitigation",
                notes="Water impact assessment required"
            )
        elif is_intensive and not has_mitigation:
            return DNSHResult(
                criterion="water_use",
                status=DNSHStatus.UNCLEAR,
                evidence="Water-intensive sector, mitigation measures not specified",
                notes="Recommend water management plan documentation"
            )
        else:
            return DNSHResult(
                criterion="water_use",
                status=DNSHStatus.PASS,
                evidence="No significant water impact or mitigation in place",
                notes=""
            )
    
    def _check_circular_economy(self, text: str, sector: str) -> DNSHResult:
        """Check circular economy alignment."""
        linear_indicators = ["single use", "disposable", "landfill"]
        circular_indicators = ["recycling", "reuse", "circular", "waste reduction", "recyclable"]
        
        has_linear = any(ind in text for ind in linear_indicators)
        has_circular = any(ind in text for ind in circular_indicators)
        
        if has_linear and not has_circular:
            return DNSHResult(
                criterion="circular_economy",
                status=DNSHStatus.FAIL,
                evidence="Linear economy indicators without circular measures",
                notes="Consider waste reduction strategies"
            )
        elif has_circular:
            return DNSHResult(
                criterion="circular_economy",
                status=DNSHStatus.PASS,
                evidence="Circular economy principles identified",
                notes=""
            )
        else:
            return DNSHResult(
                criterion="circular_economy",
                status=DNSHStatus.PASS,
                evidence="No significant circular economy concerns",
                notes=""
            )
    
    def _check_pollution(self, text: str, sector: str) -> DNSHResult:
        """Check pollution prevention."""
        polluting_sectors = ["chemical", "manufacturing", "mining", "oil", "refinery"]
        pollution_control = ["emission control", "pollution prevention", "air quality", "filter"]
        
        is_polluting_sector = any(s in sector.lower() for s in polluting_sectors)
        has_controls = any(ind in text for ind in pollution_control)
        
        if is_polluting_sector and not has_controls:
            return DNSHResult(
                criterion="pollution",
                status=DNSHStatus.UNCLEAR,
                evidence="Potentially polluting sector without documented controls",
                notes="Pollution prevention measures should be documented"
            )
        else:
            return DNSHResult(
                criterion="pollution",
                status=DNSHStatus.PASS,
                evidence="No significant pollution concerns or controls in place",
                notes=""
            )
    
    def _check_biodiversity(self, text: str, location: str, sector: str) -> DNSHResult:
        """Check biodiversity and ecosystem protection."""
        sensitive_indicators = [
            "protected area", "nature reserve", "national park", "wetland",
            "endangered species", "primary forest", "unesco"
        ]
        positive_indicators = [
            "biodiversity", "habitat restoration", "conservation",
            "environmental impact assessment", "eia approved"
        ]
        
        in_sensitive_area = any(ind in location or ind in text for ind in sensitive_indicators)
        has_protection = any(ind in text for ind in positive_indicators)
        
        if in_sensitive_area and not has_protection:
            return DNSHResult(
                criterion="biodiversity",
                status=DNSHStatus.FAIL,
                evidence="Project in ecologically sensitive area without documented protection",
                notes="Environmental Impact Assessment required"
            )
        elif has_protection:
            return DNSHResult(
                criterion="biodiversity",
                status=DNSHStatus.PASS,
                evidence="Biodiversity protection measures identified",
                notes=""
            )
        else:
            return DNSHResult(
                criterion="biodiversity",
                status=DNSHStatus.PASS,
                evidence="No significant biodiversity concerns identified",
                notes=""
            )
    
    def get_dnsh_summary(self, dnsh_results: Dict[str, DNSHResult]) -> Dict[str, Any]:
        """Summarize DNSH assessment results."""
        passed = sum(1 for r in dnsh_results.values() if r.status == DNSHStatus.PASS)
        failed = sum(1 for r in dnsh_results.values() if r.status == DNSHStatus.FAIL)
        unclear = sum(1 for r in dnsh_results.values() if r.status == DNSHStatus.UNCLEAR)
        
        overall_pass = failed == 0
        
        return {
            "overall_pass": overall_pass,
            "passed_count": passed,
            "failed_count": failed,
            "unclear_count": unclear,
            "results": {k: {"status": v.status.value, "evidence": v.evidence, "notes": v.notes} 
                       for k, v in dnsh_results.items()}
        }
    
    # ==================== Carbon Lock-in ====================
    
    def assess_carbon_lockin(
        self,
        project_data: Dict[str, Any],
        extracted_text: str = ""
    ) -> CarbonLockinResult:
        """
        Assess carbon lock-in risk.
        
        Carbon lock-in occurs when investments in carbon-intensive infrastructure
        delay the transition to low-carbon alternatives and create stranded asset risk.
        """
        combined_text = f"{project_data.get('use_of_proceeds', '')} {extracted_text}".lower()
        sector = project_data.get('sector', '').lower()
        
        # Check for carbon lock-in indicators
        indicators_found = [
            ind for ind in self.carbon_lockin_indicators
            if ind.lower() in combined_text
        ]
        
        # Check sector risk
        is_high_risk_sector = any(
            s.lower() in sector for s in self.high_risk_sectors
        )
        
        # Check for transition elements
        transition_indicators = [
            "transition", "phase out", "decommission", "renewable replacement",
            "electrification", "hydrogen transition"
        ]
        has_transition_plan = any(t in combined_text for t in transition_indicators)
        
        # Determine risk level
        if len(indicators_found) >= 2 or (indicators_found and is_high_risk_sector):
            risk_level = RiskLevel.HIGH
            assessment = (
                f"High carbon lock-in risk identified. "
                f"Indicators: {', '.join(indicators_found)}. "
                "This investment may delay climate transition and create stranded asset risk."
            )
            recommendation = (
                "Consider alternative low-carbon investments or require detailed transition plan."
            )
        elif indicators_found or is_high_risk_sector:
            if has_transition_plan:
                risk_level = RiskLevel.MEDIUM
                assessment = (
                    "Moderate carbon lock-in risk with transition elements identified. "
                    "Project includes some transition planning."
                )
                recommendation = (
                    "Require detailed transition timeline and interim targets."
                )
            else:
                risk_level = RiskLevel.MEDIUM
                assessment = (
                    f"Moderate carbon lock-in risk. Sector or activity may pose transition risk."
                )
                recommendation = (
                    "Request transition strategy and alignment with Paris Agreement targets."
                )
        else:
            risk_level = RiskLevel.LOW
            assessment = "Low carbon lock-in risk. No significant fossil fuel infrastructure identified."
            recommendation = "Standard monitoring applies."
        
        return CarbonLockinResult(
            risk_level=risk_level,
            indicators_found=indicators_found,
            assessment=assessment,
            recommendation=recommendation
        )
    
    # ==================== Overall GLP Eligibility ====================
    
    def assess_glp_eligibility(
        self,
        project_data: Dict[str, Any],
        extracted_text: str = ""
    ) -> GlpEligibilityResult:
        """
        Comprehensive GLP eligibility assessment.
        Combines use of proceeds, DNSH, and carbon lock-in checks.
        """
        issues = []
        recommendations = []
        
        # 1. Use of Proceeds check
        uop_result = self.validate_use_of_proceeds(
            project_data.get('use_of_proceeds', ''),
            project_data.get('sector', ''),
            project_data.get('project_type', 'New')
        )
        
        if not uop_result['is_valid']:
            issues.append(uop_result['assessment'])
        if uop_result['red_flags']:
            issues.append(f"Red flags: {', '.join(uop_result['red_flags'])}")
        
        # 2. DNSH check
        dnsh_results = self.assess_dnsh(project_data, extracted_text)
        dnsh_summary = self.get_dnsh_summary(dnsh_results)
        
        if not dnsh_summary['overall_pass']:
            failed_criteria = [
                k for k, v in dnsh_results.items() 
                if v.status == DNSHStatus.FAIL
            ]
            issues.append(f"DNSH criteria failed: {', '.join(failed_criteria)}")
        
        if dnsh_summary['unclear_count'] > 0:
            recommendations.append(
                "Provide additional documentation for unclear DNSH criteria."
            )
        
        # 3. Carbon lock-in check
        lockin_result = self.assess_carbon_lockin(project_data, extracted_text)
        
        if lockin_result.risk_level == RiskLevel.HIGH:
            issues.append(lockin_result.assessment)
            recommendations.append(lockin_result.recommendation)
        elif lockin_result.risk_level == RiskLevel.MEDIUM:
            recommendations.append(lockin_result.recommendation)
        
        # Determine overall eligibility
        is_eligible = (
            uop_result['is_valid'] and 
            dnsh_summary['overall_pass'] and
            lockin_result.risk_level != RiskLevel.HIGH
        )
        
        # Add standard recommendations
        if is_eligible:
            recommendations.append(
                "Proceed with standard GLP documentation requirements."
            )
            recommendations.append(
                "Ensure annual reporting on use of proceeds and environmental impact."
            )
        
        return GlpEligibilityResult(
            is_eligible=is_eligible,
            category=uop_result['glp_category'],
            confidence=uop_result['confidence'],
            use_of_proceeds_valid=uop_result['is_valid'],
            dnsh_pass=dnsh_summary['overall_pass'],
            carbon_lockin_risk=lockin_result.risk_level,
            issues=issues,
            recommendations=recommendations
        )


# Singleton instance
glp_rules_engine = GLPRulesEngine()
