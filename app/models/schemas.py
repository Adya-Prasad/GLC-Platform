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
    SHAREHOLDER = "shareholder"


class ApplicationStatusEnum(str, Enum):
    PENDING = "pending"
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
    role: UserRoleEnum


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    name: str
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
    # Organization Details
    org_name: str = Field(..., description="Organization name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone number")
    org_gst: Optional[str] = Field(None, description="GST / Tax ID")
    credit_score: Optional[str] = Field(None, description="Credit Score")
    location: Optional[str] = Field(None, description="Headquarters location")
    website: Optional[str] = Field(None, description="Website URL")
    
    # Project Information
    project_name: str = Field(..., description="Project title")
    sector: str = Field(..., description="Project sector")
    project_location: Optional[str] = Field(None, description="Project site location")
    project_pin_code: Optional[str] = Field(None, description="Project Postal/Zip Code")
    project_type: str = Field(default="New Project", description="New or Existing project")
    reporting_frequency: Optional[str] = Field(None, description="Annual, Half-yearly, Quarterly")
    has_existing_loan: bool = Field(default=False, description="Does borrower have existing loans?")
    planned_start_date: str = Field(..., description="Planned project start date (YYYY-MM-DD)")
    shareholder_entities: int = Field(..., ge=0, description="Number of shareholder entities involved in the project")
    amount_requested: float = Field(..., gt=0, description="Loan amount requested")
    currency: str = Field(default="USD", description="Currency code")
    project_description: str = Field(..., description="Detailed project description")
    annual_revenue: Optional[float] = Field(None, description="Organization annual revenue")
    tax_id: Optional[str] = Field(None, description="Organization tax identifier (e.g., GSTIN)")
    credit_score: Optional[int] = Field(None, description="Organization credit score")
    headquarters_location: Optional[str] = Field(None, description="Headquarters location")

    # Project aliases matching incoming JSON
    project_title: Optional[str] = Field(None, description="Project title (alias)")
    project_sector: Optional[str] = Field(None, description="Project sector (alias)")

    # Green KPIs
    use_of_proceeds: str = Field(..., description="Description of how funds will be used")
    ghg_target_reduction: Optional[int] = Field(None, description="GHG target reduction percentage")
    ghg_baseline_year: Optional[int] = Field(None, description="GHG baseline year")
    scope1_tco2: Optional[float] = Field(None, ge=0, description="Scope 1 emissions in tCO2")
    scope2_tco2: Optional[float] = Field(None, ge=0, description="Scope 2 emissions in tCO2")
    scope3_tco2: Optional[float] = Field(None, ge=0, description="Scope 3 emissions in tCO2")
    installed_capacity: Optional[str] = Field(None, description="MW capacity")
    target_reduction: Optional[str] = Field(None, description="% reduction")
    baseline_year: Optional[int] = Field(None, description="Baseline year for emissions")
    kpi_metrics: List[str] = Field(default=[], description="Selected KPIs")
    
    # Supporting Docs
    additional_info: Optional[str] = Field(None, description="Additional project information")
    cloud_doc_url: Optional[str] = Field(None, description="Cloud document URL")

    # ESG Questionnaire & Consent
    questionnaire_data: Dict[str, Any] = Field(default={}, description="GLP Questionnaire answers")
    consent_agreed: bool = Field(default=False, description="User agreed to terms")
    
   


class LoanApplicationResponse(BaseModel):
    id: int
    loan_id: str  # LOAN_1, LOAN_2, etc.
    borrower_id: int
    project_name: str
    sector: str
    location: Optional[str]
    project_location: Optional[str]
    project_type: Optional[str]
    project_description: str
    annual_revenue: Optional[float] = None
    amount_requested: float
    currency: str
    use_of_proceeds: Optional[str]
    use_of_proceeds_description: Optional[str]
    scope1_tco2: Optional[float]
    scope2_tco2: Optional[float]
    scope3_tco2: Optional[float]
    total_tco2: Optional[float]
    baseline_year: Optional[int]
    ghg_target_reduction: Optional[int]
    ghg_baseline_year: Optional[int]
    
    project_pin_code: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    has_existing_loan: Optional[bool]
    
    planned_start_date: Optional[str]
    org_name: Optional[str] = None
    organization_name: Optional[str] = None
    tax_id: Optional[str] = None
    credit_score: Optional[int] = None
    headquarters_location: Optional[str] = None
    shareholder_entities: Optional[int] = 0
    
    reporting_frequency: Optional[str]
    installed_capacity: Optional[str]
    target_reduction: Optional[str]
    kpi_metrics: Optional[List[str]]
    
    questionnaire_data: Optional[Dict[str, Any]]
    cloud_doc_url: Optional[str]
    raw_application_json: Optional[Dict[str, Any]]
    
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
    loan_id: str  # LOAN_1, LOAN_2, etc.
    project_name: str
    borrower_name: str
    org_name: str
    sector: str
    amount_requested: float
    currency: str
    status: ApplicationStatusEnum
    esg_score: Optional[float]
    glp_eligibility: Optional[bool]
    planned_start_date: Optional[str]
    shareholder_entities: Optional[int] = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class ApplicationCreateResponse(BaseModel):
    """Response for loan application creation."""
    id: int
    loan_id: str  # LOAN_1, LOAN_2, etc.
    status: str
    message: str


# ==================== Document Schemas ====================

class DocumentResponse(BaseModel):
    id: int
    loan_id: int
    filename: str
    file_type: Optional[str]
    doc_category: Optional[str]
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
    loan_id: int
    project_id: Optional[int] = None


class KPIResponse(KPIBase):
    id: int
    loan_id: int
    ambition_score: Optional[float]
    is_ambitious: Optional[bool]
    
    class Config:
        from_attributes = True


# ==================== Verification Schemas ====================

class VerificationCreate(BaseModel):
    verifier_role: str = Field(..., description="Role of verifier (lender, shareholder)")
    result: VerificationResultEnum
    notes: Optional[str] = None


class VerificationResponse(BaseModel):
    id: int
    loan_id: int
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
    loan_id: int
    status: str
    message: str


class IngestionSummary(BaseModel):
    """Summary of ingestion results."""
    job_id: int
    loan_id: int
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
    shareholder_name: Optional[str] = None
    shareholder_org: Optional[str] = None


class ExternalReviewResponse(BaseModel):
    loan_id: int
    package_url: str
    generated_at: datetime
    contents: List[str]
