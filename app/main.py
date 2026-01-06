"""
GLC Platform - Green Lending and Compliance Framework
Main FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import logging

from app.core.config import settings
from app.models.db import init_db
from app.api.borrower import router as borrower_router
from app.api.lender import router as lender_router
from app.api.admin import router as admin_router
from app.api.audit import router as audit_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(borrower_router, prefix="/api/v1")
app.include_router(lender_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")

# Mount static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Mount reports for download
reports_path = settings.REPORTS_DIR / "packages"
reports_path.mkdir(parents=True, exist_ok=True)
app.mount("/downloads", StaticFiles(directory=str(reports_path)), name="downloads")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    logger.info("🚀 Starting GLC Platform...")
    init_db()
    logger.info("✅ GLC Platform is ready!")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard application."""
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    return FileResponse(index_path)

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    login_path = Path(__file__).parent.parent / "static" / "signup.html"
    return FileResponse(login_path)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve favicon.ico."""
    return FileResponse(Path(__file__).parent.parent / "static" / "img" / "favicon.ico")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/v1/auth/login")
async def mock_login(role: str = "borrower", name: str = None, passcode: str = None):
    """Mock login endpoint with passcode verification."""
    from app.models.db import SessionLocal
    from app.core.auth import MockAuth
    
    if not name or not passcode:
        return {"error": "Name and passcode are required", "status": "error"}
    
    if len(passcode) != 6 or not passcode.isdigit():
        return {"error": "Passcode must be exactly 6 digits", "status": "error"}
    
    db = SessionLocal()
    try:
        user, login_status = MockAuth.login_with_passcode(db, role, name, passcode)
        
        if login_status == "passcode_mismatch":
            return {
                "error": "Incorrect passcode for this user",
                "status": "passcode_mismatch"
            }
        
        return {
            "user_id": user.id,
            "name": user.name,
            "role": user.role.value,
            "status": login_status  # "new_user" or "existing_user"
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
