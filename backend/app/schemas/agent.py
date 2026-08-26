from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AgentStepResult(BaseModel):
    agent_name: str
    action: str
    status: str = "COMPLETED"
    duration_ms: float = 0.0
    summary: str
    details: Dict[str, Any] = {}
    timestamp: str


class InvestigationPlanSchema(BaseModel):
    planner_mode: str
    alert_type: str
    primary_objective: str
    required_data_sources: List[str]
    planned_steps: List[Dict[str, Any]]
    adaptation_reason: Optional[str] = None


class SARReportSchema(BaseModel):
    subject_name: str
    subject_id: str
    alert_type: str
    risk_level: str
    recommended_action: str
    executive_summary: str
    suspicious_activity_narrative: str
    nexus_and_methodology: str
    law_enforcement_referral_recommended: bool
    requires_human_signoff: bool = True
