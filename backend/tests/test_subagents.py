import pytest
from app.db.session import SessionLocal, init_db
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.agents.subagents.evidence import evidence_retrieval_node
from app.agents.subagents.graph import graph_relationship_node
from app.agents.subagents.behavior import behavior_analysis_node
from app.agents.subagents.document import document_analysis_node
from app.agents.subagents.intelligence import external_intelligence_node
from app.agents.subagents.assembly import case_assembly_node
from app.agents.hypothesis import hypothesis_node
from app.agents.state import InvestigationState
from app.db.models import Alert


@pytest.fixture(scope="module")
def seeded_env():
    init_db()
    db = SessionLocal()
    gen = SyntheticAMLDataGenerator(seed=42)
    gen.generate_and_seed_database(db, num_customers=40, num_transactions=250)
    alerts = transaction_monitor.scan_and_generate_alerts(db)
    yield db, alerts[0] if alerts else None
    db.close()


def test_subagents_execution_pipeline(seeded_env):
    db, sample_alert = seeded_env
    assert sample_alert is not None

    state: InvestigationState = {
        "case_id": "CASE_SUBAGENT_TEST",
        "alert_id": sample_alert.alert_id,
        "alert_data": {
            "alert_id": sample_alert.alert_id,
            "entity_type": sample_alert.entity_type,
            "entity_id": sample_alert.entity_id,
            "alert_type": sample_alert.alert_type,
            "severity": sample_alert.severity,
            "raw_score": sample_alert.raw_score,
            "features_json": sample_alert.features_json or {}
        },
        "customer_data": {
            "customer_id": "CUST_0001",
            "full_name": "Test Subject",
            "risk_tier": "HIGH",
            "occupation": "Import/Export Merchant",
            "is_pep": True,
            "is_sanctioned": False,
            "kyc_notes": "Enhanced Due Diligence completed."
        },
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

    # 1. Hypothesis Generation
    state = hypothesis_node(state)
    assert len(state["hypotheses"]) >= 2

    # 2. Evidence Retrieval
    state = evidence_retrieval_node(state)
    assert "total_transactions_analyzed" in state["evidence_data"]

    # 3. Graph Relationship
    state = graph_relationship_node(state)
    assert "total_counterparties" in state["graph_data"]

    # 4. Behavior Analysis
    state = behavior_analysis_node(state)
    assert "velocity_z_score" in state["behavior_data"]

    # 5. Document Analysis
    state = document_analysis_node(state)
    assert "document_risk_score" in state["document_data"]

    # 6. External Intelligence (Mocked)
    state = external_intelligence_node(state)
    assert state["intelligence_data"]["is_mocked_feed"] is True
    assert state["intelligence_data"]["pep_match"] is True

    # 7. Case Assembly
    state = case_assembly_node(state)
    assert "assembled_case" in state
    assert len(state["agent_trail"]) == 7
