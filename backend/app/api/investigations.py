import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from app.db.session import get_db, SessionLocal
from app.agents.auditing import GENESIS_HASH, entry_hash
from app.db.models import (
    InvestigationCase,
    Alert,
    EvidenceItem,
    Hypothesis,
    AuditLog,
    InvestigatorFeedback
)
from app.schemas.case import (
    StartInvestigationRequest,
    InvestigationCaseSummaryResponse,
    InvestigationCaseDetailResponse,
    InvestigatorFeedbackCreate,
    InvestigatorFeedbackResponse
)
from app.agents.workflow import execute_investigation_case

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.get("", response_model=List[InvestigationCaseSummaryResponse])
def list_investigations(
    status: Optional[str] = None,
    decision: Optional[str] = None,
    risk_band: Optional[str] = None,
    planner_mode: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(InvestigationCase)
    if status:
        query = query.filter(InvestigationCase.status == status)
    if decision:
        query = query.filter(InvestigationCase.final_decision == decision)
    if risk_band:
        query = query.filter(InvestigationCase.final_risk_band == risk_band)
    if planner_mode:
        query = query.filter(InvestigationCase.planner_mode == planner_mode)

    return query.order_by(InvestigationCase.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/{case_id}", response_model=InvestigationCaseDetailResponse)
def get_investigation_detail(case_id: str, db: Session = Depends(get_db)):
    case_obj = db.query(InvestigationCase).options(
        selectinload(InvestigationCase.evidence_items),
        selectinload(InvestigationCase.hypotheses),
        selectinload(InvestigationCase.audit_logs),
        selectinload(InvestigationCase.feedback)
    ).filter(InvestigationCase.case_id == case_id).first()
    
    if not case_obj:
        raise HTTPException(status_code=404, detail="Investigation case not found")

    return case_obj


@router.post("/start", response_model=InvestigationCaseDetailResponse)
def start_investigation(
    req: StartInvestigationRequest,
    db: Session = Depends(get_db)
):
    """
    Executes full multi-agent LangGraph investigation pipeline:
    Supervisor -> Planner -> Hypotheses -> 6 Subagents -> Reasoning -> Risk Scoring -> Auditing -> SAR Drafter.
    """
    case_id = f"CASE_{uuid.uuid4().hex[:8].upper()}"

    try:
        execute_investigation_case(
            case_id=case_id,
            alert_id=req.alert_id,
            planner_mode=req.planner_mode
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Investigation workflow failed: {str(e)}")

    case_obj = db.query(InvestigationCase).options(
        selectinload(InvestigationCase.evidence_items),
        selectinload(InvestigationCase.hypotheses),
        selectinload(InvestigationCase.audit_logs),
        selectinload(InvestigationCase.feedback)
    ).filter(InvestigationCase.case_id == case_id).first()
    
    if not case_obj:
        raise HTTPException(status_code=500, detail="Failed to retrieve completed investigation case")
    return case_obj


@router.post("/{case_id}/feedback", response_model=InvestigatorFeedbackResponse)
def submit_investigator_feedback(
    case_id: str,
    feedback_in: InvestigatorFeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Step 11: Investigator Feedback Loop for Continuous Learning & Threshold Tuning.
    """
    case_obj = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
    if not case_obj:
        raise HTTPException(status_code=404, detail="Investigation case not found")

    # Approval gate: an analyst cannot sign off ("AGREE") on a report that still contains
    # claims the Fact Checker could not verify against the ledger. Disagreeing/overriding is allowed.
    verification = (case_obj.sar_narrative_json or {}).get("verification") or {}
    if feedback_in.feedback_type == "AGREE" and verification.get("approval_status") == "BLOCKED_UNVERIFIED_CLAIMS":
        raise HTTPException(
            status_code=409,
            detail=(
                f"Approval blocked: {verification.get('unverified_claims', 0)} claim(s) in the report are not "
                f"supported by the ledger. Correct or remove them, or record a DISAGREE/OVERRIDE instead."
            ),
        )

    feedback_obj = InvestigatorFeedback(
        case_id=case_id,
        investigator_id=feedback_in.investigator_id,
        feedback_type=feedback_in.feedback_type,
        notes=feedback_in.notes,
        adjusted_decision=feedback_in.adjusted_decision
    )
    db.add(feedback_obj)

    # Every analyst action is appended to the case's hash chain — sign-off is the most
    # important event in the audit trail, whether or not it changes the decision.
    original_decision = case_obj.final_decision
    overridden = bool(feedback_in.adjusted_decision and feedback_in.adjusted_decision != original_decision)
    if overridden:
        case_obj.final_decision = feedback_in.adjusted_decision
        case_obj.decision_rationale = (
            f"[HUMAN OVERRIDE by {feedback_in.investigator_id}]: {feedback_in.notes} "
            f"(Original system decision: {original_decision})"
        )
    last = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.id.desc()).first()
    prev_hash = last.verification_hash if last else GENESIS_HASH
    actor = f"ComplianceOfficer ({feedback_in.investigator_id})"
    action = "DECISION_OVERRIDDEN" if overridden else f"ANALYST_{feedback_in.feedback_type}"
    payload = {
        "feedback_type": feedback_in.feedback_type,
        "notes": feedback_in.notes,
        "original_decision": original_decision,
        "new_decision": case_obj.final_decision,
    }
    ts = datetime.datetime.utcnow()
    db.add(AuditLog(
        case_id=case_id,
        alert_id=case_obj.alert_id,
        actor=actor,
        action_type=action,
        description=(f"Analyst changed decision from {original_decision} to {case_obj.final_decision}. Reason: {feedback_in.notes}"
                     if overridden else f"Analyst recorded {feedback_in.feedback_type}. Notes: {feedback_in.notes}"),
        input_payload={"original_decision": original_decision},
        output_payload=payload,
        execution_time_ms=0.0,
        verification_hash=entry_hash(actor, action, ts, payload, prev_hash),
        prev_hash=prev_hash,
        timestamp=ts,
    ))

    db.commit()
    db.refresh(feedback_obj)
    return feedback_obj
