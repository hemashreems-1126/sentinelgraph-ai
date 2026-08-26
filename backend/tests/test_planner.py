from app.agents.planner import get_static_checklist, planner_node
from app.agents.state import InvestigationState


def test_static_checklist_for_structuring():
    checklist = get_static_checklist("STRUCTURING", "HIGH")
    assert checklist["planner_mode"] == "static"
    assert checklist["alert_type"] == "STRUCTURING"
    assert len(checklist["planned_steps"]) == 6
    agent_names = [s["agent"] for s in checklist["planned_steps"]]
    assert "EvidenceRetrievalAgent" in agent_names
    assert "GraphRelationshipAgent" in agent_names
    assert "CaseAssemblyAgent" in agent_names


def test_planner_node_adaptive_and_static():
    state_static: InvestigationState = {
        "case_id": "CASE_TEST_01",
        "alert_id": "ALT_01",
        "alert_data": {"alert_type": "STRUCTURING", "severity": "HIGH"},
        "customer_data": {},
        "planner_mode": "static",
        "plan": {},
        "hypotheses": [],
        "evidence_data": {},
        "graph_data": {},
        "behavior_data": {},
        "document_data": {},
        "intelligence_data": {},
        "assembled_case": {},
        "reasoning_output": {},
        "risk_evaluation": {},
        "sar_report": {},
        "iteration_count": 0,
        "needs_more_evidence": False,
        "missing_evidence_reasons": [],
        "agent_trail": [],
        "audit_logs": []
    }

    out_static = planner_node(state_static)
    assert out_static["plan"]["planner_mode"] == "static"
    assert len(out_static["agent_trail"]) == 1

    state_adaptive: InvestigationState = {
        "case_id": "CASE_TEST_02",
        "alert_id": "ALT_02",
        "alert_data": {"alert_type": "LAYERING", "severity": "CRITICAL"},
        "customer_data": {},
        "planner_mode": "adaptive",
        "plan": {},
        "hypotheses": [],
        "evidence_data": {},
        "graph_data": {},
        "behavior_data": {},
        "document_data": {},
        "intelligence_data": {},
        "assembled_case": {},
        "reasoning_output": {},
        "risk_evaluation": {},
        "sar_report": {},
        "iteration_count": 0,
        "needs_more_evidence": False,
        "missing_evidence_reasons": [],
        "agent_trail": [],
        "audit_logs": []
    }

    out_adaptive = planner_node(state_adaptive)
    assert out_adaptive["plan"]["planner_mode"] == "adaptive"
    assert "adaptation_reason" in out_adaptive["plan"]
