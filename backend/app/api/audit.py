from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.agents.auditing import verify_chain
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


@router.get("/verify/{case_id}")
def verify_case_audit_chain(case_id: str, db: Session = Depends(get_db)):
    """Re-computes the SHA-256 hash chain for a case. Any edited, deleted or reordered entry is detected."""
    logs = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.id.asc()).all()
    if not logs:
        raise HTTPException(status_code=404, detail="No audit entries for this case")
    return {"case_id": case_id, **verify_chain(logs)}
