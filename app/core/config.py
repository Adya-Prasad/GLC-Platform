"""
GLC Platform Configuration
Core configuration settings for the Green Lending Compliance platform.
"""

from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings


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
    REPORTS_DIR: Path = Path("./reports")
    
    # NLP Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    QA_MODEL: str = "deepset/roberta-base-squad2"
    RAG_MODEL: str = "google/flan-t5-small"
    SUMMARIZATION_MODEL: str = "sshleifer/distilbart-cnn-12-6"
    
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
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# GLP Categories as per LMA Green Loan Principles
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


# Extractive QA Questions for automatic processing
EXTRACTION_QUESTIONS = [
    "What is the use of proceeds?",
    "List the KPIs and their baseline values.",
    "Is there a management of proceeds description?",
    "What is the SPT target and the target year?",
    "Does the report specify external review or verification procedures?",
    "What are the Scope 1, 2, and 3 emissions?",
    "What environmental certifications does the project have?",
]
