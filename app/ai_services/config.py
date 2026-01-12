"""
GLC Platform Configuration
Core configuration settings for the Green Lending Compliance platform.
"""

from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings

from dotenv import load_dotenv
load_dotenv()  

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Info
    APP_NAME: str = "GLC Platform"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Green Lending and Financing Platform for Green Projects and Startups Loan Management"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./glc_data.db"
    
    # File Storage
    UPLOAD_DIR: Path = Path("./loan_assets")
    FAISS_INDEX_DIR: Path = Path("./faiss_indexes")
    VECTOR_DB_PATH: Path = Path("./vector_db")

    # AI Models
    EMBEDDING_MODEL: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    RAG_LLM_MODEL: str = "google/flan-t5-base"
        
    TEXT_CHUNK_SIZE: int = 1000
    TEXT_CHUNK_OVERLAP: int = 200
    
    
    # FAISS Settings
    FAISS_TOP_K: int = 6
    CHUNK_SIZE: int = 500  # tokens
    CHUNK_OVERLAP: int = 50  # tokens
    
    # ESG Scoring Weights (must sum to 1.0)
    ESG_WEIGHT_COMPLETENESS: float = 0.20
    ESG_WEIGHT_VERIFIABILITY: float = 0.25
    ESG_WEIGHT_GLP_ALIGNMENT: float = 0.25
    ESG_WEIGHT_DNSH_PENALTY: float = 0.30
    
    # SPT Calibration
    SPT_AMBITION_THRESHOLD: float = 0.20  # 20% improvement required for "ambitious"
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
# settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# settings.FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

# GLP Categories as per LMA Green Loan Principles (2023 Update)
# Reference: LMA, APLMA, LSTA Green Loan Principles February 2023
GLP_CATEGORIES = [
    "Renewable Energy",
    "Energy Efficiency",
    "Pollution Prevention and Control",
    "Environmentally Sustainable Management of Living Natural Resources and Land Use",
    "Terrestrial and Aquatic Biodiversity Conservation",
    "Clean Transportation",
    "Sustainable Water and Wastewater Management",
    "Climate Change Adaptation",
    "Eco-efficient and/or Circular Economy Adapted Products",
    "Green Buildings",
]

# LMA Four Core Components of Green Loan Principles
GLP_CORE_COMPONENTS = {
    "use_of_proceeds": {
        "name": "Use of Proceeds",
        "description": "Proceeds must be applied to eligible Green Projects with clear environmental benefits",
        "requirements": [
            "Clear environmental benefits that can be assessed and quantified",
            "Alignment with eligible green project categories",
            "May finance new or refinance existing green projects"
        ]
    },
    "project_evaluation": {
        "name": "Process for Project Evaluation and Selection",
        "description": "Borrower must communicate environmental objectives and project selection criteria",
        "requirements": [
            "Clear communication of environmental sustainability objectives",
            "Process for determining project eligibility within GLP categories",
            "Identification and management of environmental and social risks"
        ]
    },
    "management_of_proceeds": {
        "name": "Management of Proceeds",
        "description": "Proceeds must be tracked and allocated to eligible green projects",
        "requirements": [
            "Proceeds credited to dedicated account or tracked appropriately",
            "Clear designation of green tranches if multiple facilities",
            "Transparency in temporary treatment of unallocated proceeds"
        ]
    },
    "reporting": {
        "name": "Reporting",
        "description": "Annual reporting on use of proceeds and environmental impact",
        "requirements": [
            "List of green projects with amounts allocated",
            "Brief description of each project",
            "Expected environmental impact with quantitative metrics where feasible",
            "Annual updates until fully drawn and as necessary thereafter"
        ]
    }
}

# LMA Sustainability-Linked Loan Principles (SLLP) Five Core Components
SLLP_CORE_COMPONENTS = {
    "kpi_selection": {
        "name": "Selection of KPIs",
        "description": "KPIs must be relevant, core, and material to borrower's business",
        "requirements": [
            "Relevant to borrower's overall business and ESG strategy",
            "Measurable or quantifiable on consistent methodological basis",
            "Externally verifiable",
            "Able to be benchmarked against industry standards"
        ]
    },
    "spt_calibration": {
        "name": "Calibration of SPTs",
        "description": "SPTs must represent material improvement beyond business-as-usual",
        "requirements": [
            "Ambitious targets beyond business-as-usual trajectory",
            "Consistent with borrower's overall sustainability strategy",
            "Determined before or at loan execution",
            "Benchmarked against science-based trajectories where possible"
        ]
    },
    "loan_characteristics": {
        "name": "Loan Characteristics",
        "description": "Economic outcome linked to SPT achievement",
        "requirements": [
            "Margin adjustment mechanism (up and/or down)",
            "Clear trigger events for margin changes",
            "Proportional and meaningful financial incentive"
        ]
    },
    "reporting": {
        "name": "Reporting",
        "description": "Regular disclosure of KPI performance",
        "requirements": [
            "At least annual reporting on KPI performance",
            "Sufficient information for lenders to monitor SPT progress",
            "Public disclosure recommended where possible"
        ]
    },
    "verification": {
        "name": "Verification",
        "description": "Independent external verification of SPT performance",
        "requirements": [
            "Annual verification by qualified external reviewer",
            "Verification of performance against each SPT",
            "Public disclosure of verification report recommended"
        ]
    }
}

# LMA Transition Loan Principles (TLP) - Exposure Draft 2025
# For high-emitting sectors transitioning to low-carbon
TRANSITION_LOAN_CRITERIA = {
    "entity_level_strategy": {
        "name": "Entity-Level Transition Strategy",
        "description": "Borrower must evidence credible transition plan aligned with Paris Agreement",
        "indicators": [
            "Published transition plan or planning process",
            "Time-bound phase-out of high-emitting assets",
            "Capital allocation to transition-aligned activities",
            "Scope 1, 2, and material Scope 3 coverage",
            "Value chain engagement commitments"
        ]
    },
    "use_of_proceeds": {
        "name": "Use of Proceeds for Transition",
        "description": "Proceeds for assets/activities contributing to decarbonization",
        "eligible_activities": [
            "Capital expenditure for low-carbon technology",
            "Operating expenditure for transition activities",
            "R&D for emerging low-carbon solutions",
            "Early decommissioning of high-carbon assets",
            "Replacement with lower-emission alternatives"
        ]
    },
    "project_evaluation": {
        "name": "Project Evaluation and Selection",
        "description": "Projects must align with recognized pathways and avoid lock-in",
        "tests": [
            "Alignment with IEA NZE, IPCC, or national pathways",
            "Absence of technically/economically feasible low-carbon alternatives",
            "DNSH assessment for environmental and social objectives",
            "Carbon lock-in risk assessment"
        ]
    },
    "management_of_proceeds": {
        "name": "Management of Proceeds",
        "description": "Dedicated tracking of transition loan proceeds"
    },
    "reporting": {
        "name": "Reporting",
        "description": "Annual disclosure of allocations and impact",
        "requirements": [
            "Allocation to transition projects",
            "Expected and achieved emissions reductions",
            "Methodologies and key assumptions",
            "Forward-looking indicators for longer-tenor loans"
        ]
    }
}

# External Review Types (LMA External Review Guidance 2024)
EXTERNAL_REVIEW_TYPES = {
    "second_party_opinion": {
        "name": "Second Party Opinion (SPO)",
        "description": "Pre-issuance assessment of framework alignment with principles",
        "scope": "Framework review, not ongoing performance",
        "timing": "Prior to or at execution"
    },
    "verification": {
        "name": "Verification",
        "description": "Detailed review against ethical standards",
        "scope": "Financial and non-financial information",
        "timing": "Annual or as specified"
    },
    "rating_scoring": {
        "name": "SLL Rating/Scoring",
        "description": "Assessment of KPI/SPT quality and ambition",
        "scope": "Materiality, ambition, and credibility of targets",
        "timing": "Pre-execution and/or ongoing"
    }
}

# Minimal required fields for loan application payloads
REQUIRED_FIELDS = [
    "org_name",
    "project_name",
    "amount_requested",
    "currency",
    "planned_start_date",
    "shareholder_entities",
]

# DNSH (Do No Significant Harm) Criteria
DNSH_CRITERIA = {
    "climate_mitigation": "Project does not lead to significant GHG emissions",
    "climate_adaptation": "Project is climate-resilient",
    "water_use": "Project does not harm water resources",
    "circular_economy": "Project supports circular economy principles",
    "pollution": "Project does not cause pollution",
    "biodiversity": "Project protects ecosystems and biodiversity",
}

# Carbon Lock-in Risk Indicators
CARBON_LOCKIN_INDICATORS = [
    "fossil fuel",
    "coal",
    "oil drilling",
    "natural gas infrastructure",
    "carbon capture retrofit for fossil",
    "gas pipeline",
    "LNG terminal",
]
HIGH_RISK_SECTORS = [
    "Fossil fuel utilities",
    "Oil & gas",
    "Mining and quarrying",
    "Chemicals",
    "Agriculture, forestry, and fishing",
    "Transportation and storage",
    "Construction materials",
    "Heavy Industry",
    "Aviation",
]

MEDIUM_RISK_SECTORS = [
    "Construction",
    "Wholesale and retail trade",
    "Real estate activities",
    "Manufacturing of machinery and equipment",
    "Water supply, sewerage and waste management",
    "Food and beverage",
    "Healthcare services",
]

LOW_RISK_SECTORS = [
    "Renewable energy",
    "Financial and insurance activities",
    "Healthcare and social assistance",
    "Education services",
    "Professional, scientific and technical services",
    "Information technology services",
]

# Science-Based Targets Initiative (SBTi) Alignment Thresholds
SBTI_THRESHOLDS = {
    "1.5C_pathway": {
        "annual_reduction_rate": 4.2,  # % per year minimum
        "description": "1.5°C aligned pathway requires ~4.2% annual linear reduction"
    },
    "well_below_2C": {
        "annual_reduction_rate": 2.5,  # % per year minimum
        "description": "Well-below 2°C pathway requires ~2.5% annual reduction"
    },
    "2C_pathway": {
        "annual_reduction_rate": 1.23,  # % per year minimum
        "description": "2°C pathway requires ~1.23% annual reduction"
    }
}

# Margin Adjustment Ranges for SLLs (basis points)
SLL_MARGIN_ADJUSTMENTS = {
    "typical_range": {"min": 2.5, "max": 10},  # basis points
    "aggressive_range": {"min": 10, "max": 25},
    "description": "Margin adjustment typically 2.5-10 bps, can be higher for ambitious targets"
}

# GHG Protocol Scope Definitions
GHG_PROTOCOL_SCOPES = {
    "scope1": {
        "name": "Scope 1 - Direct Emissions",
        "description": "Direct GHG emissions from owned or controlled sources",
        "examples": ["Company vehicles", "On-site fuel combustion", "Process emissions"]
    },
    "scope2": {
        "name": "Scope 2 - Indirect Emissions (Energy)",
        "description": "Indirect GHG emissions from purchased electricity, steam, heating, cooling",
        "examples": ["Purchased electricity", "Purchased heat/steam", "Purchased cooling"]
    },
    "scope3": {
        "name": "Scope 3 - Value Chain Emissions",
        "description": "All other indirect emissions in company's value chain",
        "categories": [
            "Purchased goods and services",
            "Capital goods",
            "Fuel and energy related activities",
            "Upstream transportation",
            "Waste generated in operations",
            "Business travel",
            "Employee commuting",
            "Upstream leased assets",
            "Downstream transportation",
            "Processing of sold products",
            "Use of sold products",
            "End-of-life treatment",
            "Downstream leased assets",
            "Franchises",
            "Investments"
        ]
    }
}

# EU Taxonomy Environmental Objectives (for DNSH assessment)
EU_TAXONOMY_OBJECTIVES = [
    "Climate change mitigation",
    "Climate change adaptation",
    "Sustainable use and protection of water and marine resources",
    "Transition to a circular economy",
    "Pollution prevention and control",
    "Protection and restoration of biodiversity and ecosystems"
]

# Declassification Events (LMA Green Loan Draft Provisions 2024)
DECLASSIFICATION_EVENTS = [
    "Proceeds not applied to eligible green projects",
    "Material breach of green loan provisions",
    "Failure to provide required reporting",
    "Evidence of non-compliance with GLP",
    "Material ESG controversy (optional)",
    "Failure to maintain tracking of proceeds"
]


# Extractive QA Questions for automatic processing
EXTRACTION_QUESTIONS = [
    "What is the use of proceeds?",
    "List the KPIs and their baseline values.",
    "Is there a management of proceeds description?",
    "What is the SPT target and the target year?",
    "Does the report specify external review or verification procedures?",
    "What are the Scope 1, 2, and 3 emissions?",
]
