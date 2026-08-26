from app.agents.risk_scoring import compute_deterministic_risk_score, risk_scoring_node
from app.agents.state import InvestigationState


def test_deterministic_risk_scoring_bands():
    # Low Risk Case
    score_low, band_low, decision_low, _, _ = compute_deterministic_risk_score(
        alert_raw_score=20.0,
        graph_data={"high_risk_connections_count": 0, "has_cycles": False, "degree_centrality": 0.02},
        behavior_data={"velocity_z_score": 0.5, "amount_z_score": 0.4, "outbound_ratio": 0.2},
        intel_data={"intelligence_risk_score": 0.0},
        doc_data={"document_risk_score": 10.0}
    )
    assert score_low <= 30.0
    assert band_low == "LOW"
    assert decision_low == "ALLOW"

    # High / Critical Risk Case
    score_high, band_high, decision_high, _, _ = compute_deterministic_risk_score(
        alert_raw_score=90.0,
        graph_data={"high_risk_connections_count": 3, "has_cycles": True, "degree_centrality": 0.45},
        behavior_data={"velocity_z_score": 3.8, "amount_z_score": 3.2, "outbound_ratio": 0.98},
        intel_data={"intelligence_risk_score": 85.0},
        doc_data={"document_risk_score": 80.0}
    )
    assert score_high >= 71.0
    assert band_high in ["HIGH", "CRITICAL"]
    assert decision_high == "BLOCK"


def test_risk_scoring_node_in_state():
    state: InvestigationState = {
        "case_id": "CASE_RISK_TEST",
        "alert_id": "ALT_01",
        "alert_data": {"raw_score": 75.0},
        "customer_data": {},
        "planner_mode": "static",
        "plan": {},
        "hypotheses": [],
        "evidence_data": {},
        "graph_data": {"high_risk_connections_count": 1, "has_cycles": False, "degree_centrality": 0.1},
        "behavior_data": {"velocity_z_score": 2.5, "amount_z_score": 1.8, "outbound_ratio": 0.85},
        "document_data": {"document_risk_score": 40.0},
        "intelligence_data": {"intelligence_risk_score": 30.0},
        "assembled_case": {},
        "reasoning_output": {},
        "risk_evaluation": {},
        "sar_report": {},
        "iteration_count": 1,
        "needs_more_evidence": False,
        "missing_evidence_reasons": [],
        "agent_trail": [],
        "audit_logs": []
    }

    out = risk_scoring_node(state)
    assert "risk_evaluation" in out
    assert out["risk_evaluation"]["is_deterministic"] is True
    assert 0.0 <= out["risk_evaluation"]["final_risk_score"] <= 100.0
    assert out["risk_evaluation"]["final_decision"] in ["ALLOW", "REVIEW", "BLOCK"]
