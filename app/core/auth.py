"""
Authentication Module
Simplified authentication for hackathon - name + 6-digit passcode.
"""

from typing import Optional, Tuple
from fastapi import Depends, Query
from sqlalchemy.orm import Session


def get_db_conn():
    """Wrapper to break circular import with app.models.db."""
    from app.models.db import get_db
    yield from get_db()


def get_current_user(
    db: Session = Depends(get_db_conn),
    current_user_id: Optional[int] = Query(None, description="Current user ID for authentication")
) -> Optional['User']:
    """
    Get the current user from the current_user_id query parameter.
    For hackathon - simple ID-based lookup.
    """
    if current_user_id:
        from app.models.orm_models import User
        return db.query(User).filter(User.id == current_user_id).first()
    return None


class MockAuth:
    """
    Simplified authentication for hackathon.
    Users login with name + 6-digit passcode.
    """
    
    @staticmethod
    def login_user(db: Session, name: str, passcode: str, role: 'UserRole') -> Tuple[Optional['User'], str]:
        """
        Login or register a user with passcode verification.
        
        Returns:
            Tuple of (User, status) where status is one of:
            - "new_user": User was created
            - "existing_user": User found and passcode matched
            - "passcode_mismatch": User found but passcode didn't match
        """
        from app.models.orm_models import User
        
        # Look up existing user by name and role
        user = db.query(User).filter(User.name == name, User.role == role).first()
        
        if user:
            # Check passcode
            if user.passcode == passcode:
                return user, "existing_user"
            else:
                return None, "passcode_mismatch"
        
        # Create new user
        user = User(name=name, role=role, passcode=passcode)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user, "new_user"
    
    @staticmethod
    def quick_login(db: Session, role: str, name: str = None, passcode: str = None) -> 'User':
        """
        Quick login for API endpoints - returns user object only.
        Creates demo user if name/passcode not provided.
        """
        from app.models.orm_models import UserRole, User
        role_enum = UserRole(role.lower())
        
        # Use provided name or default demo names
        if not name:
            demo_users = {
                UserRole.BORROWER: ("Demo Borrower", "000000"),
                UserRole.LENDER: ("Demo Lender", "000000"),
                UserRole.SHAREHOLDER: ("External shareholder", "000000"),
            }
            name, passcode = demo_users.get(role_enum, (f"Demo {role}", "000000"))
        
        if not passcode:
            passcode = "000000"
        
        # Try to find existing user
        user = db.query(User).filter(User.name == name, User.role == role_enum).first()
        
        if user:
            return user
        
        # Create new user
        user = User(name=name, role=role_enum, passcode=passcode)
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    @staticmethod
    def login_with_passcode(db: Session, role: str, name: str, passcode: str) -> Tuple[Optional['User'], str]:
        """
        Login with passcode verification - for the login endpoint.
        Returns tuple of (user, status).
        """
        from app.models.orm_models import UserRole
        role_enum = UserRole(role.lower())
        return MockAuth.login_user(db, name, passcode, role_enum)


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
