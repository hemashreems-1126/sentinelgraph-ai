import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any


class EvidenceItemResponse(BaseModel):
    id: int
    agent_name: str
    evidence_type: str
    data_json: Dict[str, Any]
    confidence_score: float
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class HypothesisResponse(BaseModel):
    id: int
    hypothesis_id: str
    title: str
    description: str
    probability: float
    status: str
    corroborating_evidence: Optional[List[str]] = None
    contradicting_evidence: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    id: int
    case_id: Optional[str]
    alert_id: Optional[str]
    actor: str
    action_type: str
    description: str
    input_payload: Optional[Dict[str, Any]] = None
    output_payload: Optional[Dict[str, Any]] = None
    execution_time_ms: float
    verification_hash: str
    timestamp: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigatorFeedbackCreate(BaseModel):
    investigator_id: str = "analyst_1"
    feedback_type: str = Field(..., description="AGREE, DISAGREE, OVERRIDE, FALSE_POSITIVE, POLICY_ADJUSTMENT")
    notes: str
    adjusted_decision: Optional[str] = None


class InvestigatorFeedbackResponse(BaseModel):
    id: int
    case_id: str
    investigator_id: str
    feedback_type: str
    notes: str
    adjusted_decision: Optional[str]
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class StartInvestigationRequest(BaseModel):
    alert_id: str
    planner_mode: str = Field(default="static", description="'static' or 'adaptive'")


class InvestigationCaseSummaryResponse(BaseModel):
    id: int
    case_id: str
    alert_id: str
    planner_mode: str
    status: str
    iterations_count: int
    final_risk_score: float
    final_risk_band: str
    final_decision: str
    decision_rationale: Optional[str]
    created_at: datetime.datetime
    completed_at: Optional[datetime.datetime]

    model_config = ConfigDict(from_attributes=True)


class InvestigationCaseDetailResponse(InvestigationCaseSummaryResponse):
    plan_json: Optional[Dict[str, Any]] = None
    hypotheses_json: Optional[List[Dict[str, Any]]] = None
    subagent_evidence_json: Optional[Dict[str, Any]] = None
    reasoning_json: Optional[Dict[str, Any]] = None
    sar_report_text: Optional[str] = None
    sar_narrative_json: Optional[Dict[str, Any]] = None
    agent_trail_json: Optional[List[Dict[str, Any]]] = None
    evidence_items: List[EvidenceItemResponse] = []
    hypotheses: List[HypothesisResponse] = []
    audit_logs: List[AuditLogResponse] = []
    feedback: List[InvestigatorFeedbackResponse] = []

    model_config = ConfigDict(from_attributes=True)
