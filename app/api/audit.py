"""
Audit API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from dbms.db import get_db
from dbms.orm_models import AuditLog, User
from dbms.schemas import AuditLogResponse
from app.operations.auth import get_current_user

router = APIRouter(prefix="/audit", tags=["Audit"])

@router.get("/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
async def get_audit_trail(
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a specific entity."""
    # In a real app, strict permission checks here. 
    # For hackathon, we allow if user is authenticated.
    
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return logs
