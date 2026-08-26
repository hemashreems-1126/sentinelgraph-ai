from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import AuditLog
from app.schemas.case import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    case_id: Optional[str] = None,
    actor: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(AuditLog)
    if case_id:
        query = query.filter(AuditLog.case_id == case_id)
    if actor:
        query = query.filter(AuditLog.actor == actor)
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)

    return query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()
