"""API Package"""
from app.api.borrower import router as borrower_router
from app.api.lender import router as lender_router
from app.api.admin import router as admin_router

__all__ = ["borrower_router", "lender_router", "admin_router"]
