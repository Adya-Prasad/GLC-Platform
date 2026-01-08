"""
ORM Models
SQLAlchemy models for the GLC Platform database.
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, 
    ForeignKey, Enum, JSON, LargeBinary, Boolean
)
from sqlalchemy.orm import relationship
from app.models.db import Base


class UserRole(enum.Enum):
    """User role enumeration."""
    BORROWER = "borrower"
    LENDER = "lender"
    SHAREHOLDER = "shareholder"


class ApplicationStatus(enum.Enum):
    """Loan application status enumeration."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationResult(enum.Enum):
    """Verification result enumeration."""
    PASS = "pass"
    FAIL = "fail"
    UNCLEAR = "unclear"
    PENDING = "pending"
    NEEDS_INFO = "needs_info"


class User(Base):
    """User model for borrowers, lenders, and shareholder (simplified for hackathon)."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    passcode = Column(String(6), nullable=False) 
    
    # Relationships
    borrower_profile = relationship("Borrower", back_populates="user", uselist=False)
    uploaded_documents = relationship("Document", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")


class Borrower(Base):
    """Borrower profile with organization details."""
    __tablename__ = "borrowers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_name = Column(String(500), nullable=False)
    industry = Column(String(255))
    country = Column(String(100))
    gst_number = Column(String(50))
    credit_score = Column(String(50))
    website = Column(String(255))
    contact_info = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="borrower_profile")
    loan_applications = relationship("LoanApplication", back_populates="borrower")


class LoanApplication(Base):
    """Loan application for green project financing."""
    __tablename__ = "loan_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String(50), unique=True, index=True, nullable=False)  # LOAN_1, LOAN_2, etc.
    borrower_id = Column(Integer, ForeignKey("borrowers.id"), nullable=False)
    project_name = Column(String(500), nullable=False)
    sector = Column(String(255), nullable=False)
    location = Column(String(255), default="none")  # HQ location
    project_location = Column(String(255), default="none")  # Project site location
    project_type = Column(String(50), default="none")  # New or Existing
    amount_requested = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    tranche_type = Column(String(100))
    use_of_proceeds = Column(Text, default="none")
    project_description = Column(Text, default="none", nullable=False)  # Detailed project description
    annual_revenue = Column(Float, nullable=True)  # Organization annual revenue (optional)
    
    # Carbon emissions data
    scope1_tco2 = Column(Float, default=0.0)
    scope2_tco2 = Column(Float, default=0.0)
    scope3_tco2 = Column(Float, default=0.0)
    total_tco2 = Column(Float, default=0.0)
    baseline_year = Column(Integer)
    
    # Additional data
    additional_info = Column(Text, default="none")
    cloud_doc_url = Column(String(500), default="none")  # Cloud document URL
    
    # ESG and compliance scores
    esg_score = Column(Float)
    glp_eligibility = Column(Boolean)
    glp_category = Column(String(255))
    carbon_lockin_risk = Column(String(50))
    dnsh_status = Column(JSON)
    
    # Status tracking
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Project Timeline
    planned_start_date = Column(DateTime, nullable=False)
    
    # Organization Snapshot
    org_name = Column(String(255), default="none")  # Snapshot of org name at time of application
    tax_id = Column(String(100))
    credit_score = Column(Integer)

    # Use of proceeds and GHG specific columns
    
    # Contact & Personal
    project_pin_code = Column(String(20), default="none")
    contact_email = Column(String(255), default="none")
    contact_phone = Column(String(50), default="none")
    has_existing_loan = Column(Boolean, default=False)
    
    # Shareholder Entities
    shareholder_entities = Column(Integer, default=0, nullable=False)
    
    # Project & Env Details
    reporting_frequency = Column(String(50), default="Annual")
    target_reduction = Column(String(50), default="none")
    kpi_metrics = Column(JSON, default=[])

    # Compliance & Consent
    consent_agreed = Column(Boolean, default=False)
    questionnaire_data = Column(JSON, default={})

    # Parsed fields from document analysis
    parsed_fields = Column(JSON, default={})
    
    # Raw application JSON (stored for reference)
    raw_application_json = Column(JSON, default={})
    
    # Relationships
    borrower = relationship("Borrower", back_populates="loan_applications")
    projects = relationship("Project", back_populates="loan_application")
    documents = relationship("Document", back_populates="loan_application")
    kpis = relationship("KPI", back_populates="loan_application")
    verifications = relationship("Verification", back_populates="loan_application")


class Project(Base):
    """Individual project within a loan application."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    name = Column(String(500))
    use_of_proceeds_text = Column(Text)
    glp_category_guess = Column(String(255))
    allocated_amount = Column(Float)
    description = Column(Text)
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="projects")


class KPI(Base):
    """Key Performance Indicator for sustainability tracking."""
    __tablename__ = "kpis"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    kpi_name = Column(String(255), nullable=False)
    unit = Column(String(100))
    baseline_value = Column(Float)
    current_value = Column(Float)
    spt_target = Column(Float)  # Sustainability Performance Target
    target_year = Column(Integer)
    ambition_score = Column(Float)  # How ambitious the target is
    is_ambitious = Column(Boolean)
    methodology = Column(Text)
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="kpis")


class Document(Base):
    """Uploaded document for loan application."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    file_type = Column(String(50))
    doc_category = Column(String(50), default="general") # e.g. project_details, vendor_agreement, certification
    file_size = Column(Integer)
    text_extracted = Column(Text)
    extraction_status = Column(String(50), default="pending")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    chunks = relationship("DocChunk", back_populates="document")


class DocChunk(Base):
    """Document chunk for vector search."""
    __tablename__ = "doc_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    token_count = Column(Integer)
    embedding_blob = Column(LargeBinary)  # Stored as binary for efficiency
    start_char = Column(Integer)
    end_char = Column(Integer)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")


class Verification(Base):
    """Verification record for loan application claims."""
    __tablename__ = "verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    verifier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verifier_role = Column(String(50))
    verification_type = Column(String(100))  # e.g., "use_of_proceeds", "kpi", "dnsh"
    claim = Column(Text)
    result = Column(Enum(VerificationResult), default=VerificationResult.PENDING)
    confidence = Column(Float)
    evidence = Column(JSON, default=[])  # List of evidence passages
    notes = Column(Text)
    score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    loan_application = relationship("LoanApplication", back_populates="verifications")


class AuditLog(Base):
    """Audit trail for all actions in the system."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)  # e.g., "LoanApplication", "Document"
    entity_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "create", "update", "verify"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON, default={})  # Additional action data
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")


class IngestionJob(Base):
    """Track document ingestion jobs."""
    __tablename__ = "ingestion_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loan_applications.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    documents_processed = Column(Integer, default=0)
    chunks_created = Column(Integer, default=0)
    error_message = Column(Text)
    summary = Column(JSON, default={})
