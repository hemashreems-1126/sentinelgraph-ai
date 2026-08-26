import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from app.db.session import get_db, SessionLocal
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

    feedback_obj = InvestigatorFeedback(
        case_id=case_id,
        investigator_id=feedback_in.investigator_id,
        feedback_type=feedback_in.feedback_type,
        notes=feedback_in.notes,
        adjusted_decision=feedback_in.adjusted_decision
    )
    db.add(feedback_obj)

    # If decision overridden by human compliance analyst, record audit trail
    if feedback_in.adjusted_decision and feedback_in.adjusted_decision != case_obj.final_decision:
        case_obj.final_decision = feedback_in.adjusted_decision
        case_obj.decision_rationale = (
            f"[HUMAN OVERRIDE by {feedback_in.investigator_id}]: {feedback_in.notes} "
            f"(Original System Decision: {case_obj.final_decision})"
        )
        db.add(AuditLog(
            case_id=case_id,
            alert_id=case_obj.alert_id,
            actor=f"ComplianceOfficer ({feedback_in.investigator_id})",
            action_type="DECISION_OVERRIDDEN",
            description=f"Human investigator changed decision to {feedback_in.adjusted_decision}. Reason: {feedback_in.notes}",
            input_payload={"original_decision": case_obj.final_decision},
            output_payload={"new_decision": feedback_in.adjusted_decision},
            execution_time_ms=0.0,
            verification_hash="HUMAN_SIGNOFF_VERIFIED"
        ))

    db.commit()
    db.refresh(feedback_obj)
    return feedback_obj
