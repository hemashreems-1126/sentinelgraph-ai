from typing import TypedDict, List, Dict, Any, Optional


class InvestigationState(TypedDict):
    # Case Identification & Control
    case_id: str
    alert_id: str
    alert_data: Dict[str, Any]
    customer_data: Dict[str, Any]
    planner_mode: str  # "static" | "adaptive"
    
    # Phase 2: Multi-Agent outputs
    plan: Dict[str, Any]
    hypotheses: List[Dict[str, Any]]
    
    # Sub-agent Evidence Store
    evidence_data: Dict[str, Any]
    graph_data: Dict[str, Any]
    behavior_data: Dict[str, Any]
    document_data: Dict[str, Any]
    intelligence_data: Dict[str, Any]
    assembled_case: Dict[str, Any]
    
    # Phase 3: Reasoning, Decision & Governance
    reasoning_output: Dict[str, Any]
    risk_evaluation: Dict[str, Any]
    sar_report: Dict[str, Any]
    
    # Flow Control & Iteration (Loop-back)
    iteration_count: int
    needs_more_evidence: bool
    missing_evidence_reasons: List[str]
    
    # Full chronological execution trail & Audit records
    agent_trail: List[Dict[str, Any]]
    audit_logs: List[Dict[str, Any]]
