"""
Pydantic Schemas
Request and response models for API validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


# ==================== Enums ====================

class UserRoleEnum(str, Enum):
    BORROWER = "borrower"
    LENDER = "lender"
    REVIEWER = "reviewer"


class ApplicationStatusEnum(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_INFO = "needs_info"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationResultEnum(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    UNCLEAR = "unclear"
    PENDING = "pending"


# ==================== User Schemas ====================

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    role: UserRoleEnum


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    token: Optional[str] = None
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    role: UserRoleEnum


# ==================== Borrower Schemas ====================

class BorrowerBase(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=500)
    industry: Optional[str] = None
    country: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = {}


class BorrowerCreate(BorrowerBase):
    user_id: int


class BorrowerResponse(BorrowerBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Loan Application Schemas ====================

class LoanApplicationCreate(BaseModel):
    """Request body for creating a new loan application."""
    org_name: str = Field(..., description="Organization name")
    project_name: str = Field(..., description="Project name")
    sector: str = Field(..., description="Project sector (e.g., Renewable Energy)")
    location: str = Field(..., description="Project location")
    project_type: str = Field(default="New", description="New or Existing project")
    amount_requested: float = Field(..., gt=0, description="Loan amount requested")
    currency: str = Field(default="USD", description="Currency code")
    use_of_proceeds: str = Field(..., description="Description of how funds will be used")
    scope1_tco2: Optional[float] = Field(None, ge=0, description="Scope 1 emissions in tCO2")
    scope2_tco2: Optional[float] = Field(None, ge=0, description="Scope 2 emissions in tCO2")
    scope3_tco2: Optional[float] = Field(None, ge=0, description="Scope 3 emissions in tCO2")
    baseline_year: Optional[int] = Field(None, description="Baseline year for emissions")
    additional_info: Optional[str] = Field(None, description="Additional project information")


class LoanApplicationResponse(BaseModel):
    id: int
    borrower_id: int
    project_name: str
    sector: str
    location: Optional[str]
    project_type: Optional[str]
    amount_requested: float
    currency: str
    use_of_proceeds: Optional[str]
    scope1_tco2: Optional[float]
    scope2_tco2: Optional[float]
    scope3_tco2: Optional[float]
    total_tco2: Optional[float]
    baseline_year: Optional[int]
    esg_score: Optional[float]
    glp_eligibility: Optional[bool]
    glp_category: Optional[str]
    carbon_lockin_risk: Optional[str]
    status: ApplicationStatusEnum
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LoanApplicationListItem(BaseModel):
    """Summary item for application list views."""
    id: int
    project_name: str
    borrower_name: str
    org_name: str
    sector: str
    amount_requested: float
    currency: str
    status: ApplicationStatusEnum
    esg_score: Optional[float]
    glp_eligibility: Optional[bool]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApplicationCreateResponse(BaseModel):
    """Response for loan application creation."""
    id: int
    status: str
    message: str


# ==================== Document Schemas ====================

class DocumentResponse(BaseModel):
    id: int
    loan_app_id: int
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    extraction_status: str
    text_extracted: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    text_extracted: Optional[str]
    status: str
    message: str


# ==================== KPI Schemas ====================

class KPIBase(BaseModel):
    kpi_name: str
    unit: Optional[str] = None
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    spt_target: Optional[float] = None
    target_year: Optional[int] = None
    methodology: Optional[str] = None


class KPICreate(KPIBase):
    loan_app_id: int
    project_id: Optional[int] = None


class KPIResponse(KPIBase):
    id: int
    loan_app_id: int
    ambition_score: Optional[float]
    is_ambitious: Optional[bool]
    
    class Config:
        from_attributes = True


# ==================== Verification Schemas ====================

class VerificationCreate(BaseModel):
    verifier_role: str = Field(..., description="Role of verifier (lender, reviewer)")
    result: VerificationResultEnum
    notes: Optional[str] = None


class VerificationResponse(BaseModel):
    id: int
    loan_app_id: int
    verifier_role: Optional[str]
    verification_type: Optional[str]
    claim: Optional[str]
    result: VerificationResultEnum
    confidence: Optional[float]
    evidence: List[Dict[str, Any]]
    notes: Optional[str]
    score: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==================== Parsed Fields & Analysis ====================

class DNSHCheck(BaseModel):
    """Do No Significant Harm check result."""
    criterion: str
    status: str  # pass, fail, unclear
    evidence: Optional[str] = None
    notes: Optional[str] = None


class ParsedFields(BaseModel):
    """Fields extracted from documents via NLP."""
    use_of_proceeds: Optional[str] = None
    kpis: List[Dict[str, Any]] = []
    glp_category_guess: Optional[str] = None
    dnsh: Dict[str, str] = {}
    management_of_proceeds: Optional[str] = None
    external_review: Optional[str] = None


class VerificationSummary(BaseModel):
    """Summary of verification analysis."""
    conclusion: str  # Verified, Unclear, Unverified
    confidence: float
    evidence: List[Dict[str, Any]] = []


class ApplicationDetailResponse(BaseModel):
    """Detailed application view for lenders."""
    loan_app: LoanApplicationResponse
    borrower: BorrowerResponse
    documents: List[DocumentResponse]
    kpis: List[KPIResponse]
    parsed_fields: ParsedFields
    verification: VerificationSummary
    esg_score: float
    dnsh_checks: List[DNSHCheck]
    carbon_lockin_risk: str


# ==================== Portfolio Schemas ====================

class PortfolioSummary(BaseModel):
    """Aggregated portfolio metrics."""
    total_applications: int
    total_financed_amount: float
    total_financed_co2: float
    num_green_projects: int
    num_pending: int
    num_approved: int
    num_rejected: int
    percent_eligible_green: float
    avg_esg_score: float
    flagged_count: int
    sector_breakdown: Dict[str, int]
    status_breakdown: Dict[str, int]


# ==================== Report Schemas ====================

class ReportRequest(BaseModel):
    format: str = Field(default="json", description="Output format: json or pdf")


class GlpReportData(BaseModel):
    """GLP Investor Report data structure."""
    report_id: str
    generated_at: datetime
    project_summary: Dict[str, Any]
    glp_eligibility: Dict[str, Any]
    kpi_table: List[Dict[str, Any]]
    verification_summary: Dict[str, Any]
    esg_composite_score: float
    dnsh_assessment: Dict[str, Any]
    carbon_lockin_assessment: Dict[str, Any]
    recommendations: List[str]


# ==================== Ingestion Schemas ====================

class IngestionJobResponse(BaseModel):
    job_id: int
    loan_app_id: int
    status: str
    message: str


class IngestionSummary(BaseModel):
    """Summary of ingestion results."""
    job_id: int
    loan_app_id: int
    status: str
    documents_processed: int
    chunks_created: int
    fields_extracted: Dict[str, Any]
    esg_score: Optional[float]
    glp_category: Optional[str]
    processing_time_seconds: float


# ==================== Audit Log Schemas ====================

class AuditLogResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    user_id: Optional[int]
    timestamp: datetime
    data: Dict[str, Any]
    
    class Config:
        from_attributes = True


# ==================== External Review Schemas ====================

class ExternalReviewRequest(BaseModel):
    reviewer_name: Optional[str] = None
    reviewer_org: Optional[str] = None


class ExternalReviewResponse(BaseModel):
    loan_app_id: int
    package_url: str
    generated_at: datetime
    contents: List[str]
