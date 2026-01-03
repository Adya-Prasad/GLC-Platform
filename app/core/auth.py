"""
Authentication Module
Mock authentication for prototype - provides token generation and validation.
"""

import secrets
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.db import get_db
from app.models.orm_models import User, UserRole


# Security scheme for swagger docs
security = HTTPBearer(auto_error=False)


def generate_token() -> str:
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def get_user_by_token(db: Session, token: str) -> Optional[User]:
    """Retrieve user by their authentication token."""
    return db.query(User).filter(User.token == token).first()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user from the authorization header.
    For prototype, returns None if no valid token (allows anonymous access).
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    user = get_user_by_token(db, token)
    return user


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Require authentication for an endpoint.
    Raises 401 if no valid token provided.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    user = get_user_by_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


def require_borrower(user: User = Depends(require_auth)) -> User:
    """Require user to be a borrower."""
    if user.role != UserRole.BORROWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires borrower access"
        )
    return user


def require_lender(user: User = Depends(require_auth)) -> User:
    """Require user to be a lender (admin)."""
    if user.role != UserRole.LENDER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires lender access"
        )
    return user


def require_reviewer(user: User = Depends(require_auth)) -> User:
    """Require user to be a reviewer or lender."""
    if user.role not in [UserRole.LENDER, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires reviewer access"
        )
    return user


class MockAuth:
    """
    Mock authentication for rapid prototyping.
    Creates users on-the-fly for demo purposes.
    """
    
    @staticmethod
    def create_or_get_user(db: Session, name: str, email: str, role: UserRole) -> User:
        """Create a new user or return existing one."""
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update token if needed
            if not user.token:
                user.token = generate_token()
                db.commit()
            return user
        
        # Create new user
        user = User(
            name=name,
            email=email,
            role=role,
            token=generate_token(),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def quick_login(db: Session, role: str) -> User:
        """
        Quick login for demo - creates a demo user for the role.
        """
        role_enum = UserRole(role.lower())
        
        demo_users = {
            UserRole.BORROWER: ("Demo Borrower", "borrower@demo.glc"),
            UserRole.LENDER: ("Demo Lender", "lender@demo.glc"),
            UserRole.REVIEWER: ("External Reviewer", "reviewer@demo.glc"),
        }
        
        name, email = demo_users.get(role_enum, ("Demo User", f"{role}@demo.glc"))
        return MockAuth.create_or_get_user(db, name, email, role_enum)


def log_audit_action(
    db: Session,
    entity_type: str,
    entity_id: int,
    action: str,
    user_id: Optional[int] = None,
    data: dict = None
):
    """Log an action to the audit trail."""
    from app.models.orm_models import AuditLog
    
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id,
        data=data or {}
    )
    db.add(log)
    db.commit()
