"""
Models Package
Database models and Pydantic schemas for the GLC Platform.
"""

from app.models.db import Base, engine, SessionLocal, get_db, init_db
from app.models.orm_models import (
    User, UserRole, Borrower, LoanApplication, ApplicationStatus,
    Project, KPI, Document, DocChunk, Verification, VerificationResult,
    AuditLog, IngestionJob
)
from app.models.schemas import (
    UserCreate, UserResponse, UserLogin,
    BorrowerCreate, BorrowerResponse,
    LoanApplicationCreate, LoanApplicationResponse, LoanApplicationListItem,
    DocumentResponse, DocumentUploadResponse,
    KPICreate, KPIResponse,
    VerificationCreate, VerificationResponse,
    PortfolioSummary, GlpReportData,
    IngestionJobResponse, IngestionSummary,
    AuditLogResponse
)

__all__ = [
    "Base", "engine", "SessionLocal", "get_db", "init_db",
    "User", "UserRole", "Borrower", "LoanApplication", "ApplicationStatus",
    "Project", "KPI", "Document", "DocChunk", "Verification", "VerificationResult",
    "AuditLog", "IngestionJob"
]
