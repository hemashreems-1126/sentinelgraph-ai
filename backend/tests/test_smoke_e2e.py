import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db


@pytest.fixture
def client():
    init_db()
    return TestClient(app)


def test_full_investigation_pipeline_e2e_smoke(client):
    """
    Complete End-to-End Smoke Test exercising all 11 stages of SentinelGraph:
    1. Alert Generation (Synthetic data)
    2. Transaction Monitor (Rule + Isolation Forest)
    3. Alert Prioritization (Triage)
    4. Investigation Planner (Static + Adaptive)
    5. Hypothesis Generation Agent
    6. Specialised Sub-Agents (Evidence, Graph, Behavior, Documents, Intel, Assembly)
    7. Shared Knowledge Store & Memory
    8. Analysis & Reasoning Agent
    9. Risk Assignment Agent (Deterministic Python)
    10. Auditing Agent (SHA-256 logs)
    11. SAR Drafting Agent + Investigator Feedback Loop
    """
    # Step 1: Generate & Monitor
    gen_res = client.post("/api/alerts/generate", json={"num_customers": 50, "num_transactions": 300, "seed": 42})
    assert gen_res.status_code == 200

    # Step 2: Prioritize
    prio_res = client.post("/api/alerts/prioritize", json={"batch_size": 10})
    assert prio_res.status_code == 200
    triaged_alerts = prio_res.json()
    assert len(triaged_alerts) > 0

    target_alert_id = triaged_alerts[0]["alert_id"]

    # Step 3: Run Full Multi-Agent Investigation (Static Mode)
    inv_res = client.post("/api/investigations/start", json={
        "alert_id": target_alert_id,
        "planner_mode": "static"
    })
    assert inv_res.status_code == 200
    case_data = inv_res.json()

    # Validate Case Outputs
    case_id = case_data["case_id"]
    assert case_data["status"] == "COMPLETED"
    assert 0.0 <= case_data["final_risk_score"] <= 100.0
    assert case_data["final_risk_band"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert case_data["final_decision"] in ["ALLOW", "REVIEW", "BLOCK"]
    assert case_data["sar_report_text"] is not None
    assert len(case_data["agent_trail_json"]) >= 8  # Full per-agent step trail

    # Verify per-agent trail contains all key agents
    agent_names = [step["agent_name"] for step in case_data["agent_trail_json"]]
    assert any("Supervisor" in name for name in agent_names)
    assert any("Planner" in name for name in agent_names)
    assert any("Hypothesis" in name for name in agent_names)
    assert any("Evidence" in name for name in agent_names)
    assert any("Graph" in name for name in agent_names)
    assert any("Behavior" in name for name in agent_names)
    assert any("Document" in name for name in agent_names)
    assert any("Intelligence" in name for name in agent_names)
    assert any("Assembly" in name for name in agent_names)
    assert any("Reasoning" in name for name in agent_names)
    assert any("RiskAssignment" in name for name in agent_names)
    assert any("Auditing" in name for name in agent_names)
    assert any("ReportSAR" in name for name in agent_names)

    # Step 4: Verify Immutable Audit Trail in Database
    audit_res = client.get(f"/api/audit?case_id={case_id}")
    assert audit_res.status_code == 200
    audit_logs = audit_res.json()
    assert len(audit_logs) >= 8
    assert all("verification_hash" in log and len(log["verification_hash"]) > 0 for log in audit_logs)

    # Step 5: Test Investigator Feedback Loop & Override
    feedback_res = client.post(f"/api/investigations/{case_id}/feedback", json={
        "investigator_id": "senior_officer_42",
        "feedback_type": "OVERRIDE",
        "notes": "Verified source of funds directly with correspondent bank. Clearing transaction with monitoring flag.",
        "adjusted_decision": "REVIEW"
    })
    assert feedback_res.status_code == 200
    feedback_data = feedback_res.json()
    assert feedback_data["feedback_type"] == "OVERRIDE"

    # Step 6: Verify Case Details reflect feedback
    detail_res = client.get(f"/api/investigations/{case_id}")
    assert detail_res.status_code == 200
    updated_case = detail_res.json()
    assert updated_case["final_decision"] == "REVIEW"
    assert len(updated_case["feedback"]) >= 1
