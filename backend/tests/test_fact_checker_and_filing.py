import copy
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, init_db
from app.db.models import Alert, InvestigationCase
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.agents.workflow import execute_investigation_case
from app.agents.fact_checker import extract_numbers, fact_check_report
from app.agents.filing_decision import decide_filing


@pytest.fixture(scope="module")
def upi_case():
    """Seed a small India-first dataset and investigate one UPI mule alert end to end."""
    init_db()
    db = SessionLocal()
    try:
        SyntheticAMLDataGenerator(seed=7).generate_and_seed_database(db, num_customers=200, num_transactions=3000)
        transaction_monitor.scan_and_generate_alerts(db)
        alert = db.query(Alert).filter(Alert.alert_type == "UPI_MULE_CHAIN").first()
        assert alert is not None, "UPI mule rule should fire on generated data"
        alert_id = alert.alert_id
    finally:
        db.close()
    case_id = f"CASE_TEST_{uuid.uuid4().hex[:6]}"
    return case_id, execute_investigation_case(case_id, alert_id)


# ---------------- number extraction ----------------

def test_extract_numbers_handles_indian_format_and_ignores_ids():
    nums = extract_numbers("Received ₹4,20,000.50 in 12 credits (TXN_000123, ACC_CUST_0089_2); 95% left.")
    assert nums == [420000.5, 12.0, 95.0]


# ---------------- filing decision (pure policy function) ----------------

def test_no_red_flags_means_no_file_with_memo():
    d = decide_filing(25.0, [])
    assert d["decision"] == "NO_FILE"
    assert d["tier"] is None
    assert d["reasons"], "a non-filing decision must be documented"


def test_two_strong_flags_file_even_with_low_score():
    flags = [{"code": "CASH_BELOW_PAN_THRESHOLD", "strength": "STRONG", "description": "x"},
             {"code": "MANY_UNRELATED_PAYERS", "strength": "STRONG", "description": "y"}]
    d = decide_filing(40.0, flags)
    assert d["decision"] == "FILE_STR"
    assert d["tier"] == "TIER_2_PRIORITY"


def test_live_mule_pattern_is_tier_1():
    flags = [{"code": "RAPID_PASS_THROUGH", "strength": "STRONG", "description": "x"},
             {"code": "MANY_UNRELATED_PAYERS", "strength": "STRONG", "description": "y"}]
    assert decide_filing(55.0, flags)["tier"] == "TIER_1_URGENT"


def test_sanctions_match_always_files_tier_1():
    d = decide_filing(10.0, [{"code": "SANCTIONS_MATCH", "strength": "STRONG", "description": "x"}])
    assert d["decision"] == "FILE_STR" and d["tier"] == "TIER_1_URGENT"


# ---------------- end-to-end report + fact check ----------------

def test_upi_mule_case_produces_verified_str(upi_case):
    _, state = upi_case
    report = state["sar_report"]
    v = report["verification"]
    assert state["filing_decision"]["decision"] == "FILE_STR"
    assert report["report_type"] == "STR_DRAFT"
    assert v["total_claims"] >= 4
    assert v["verified_claims"] == v["total_claims"]
    assert v["approval_status"] == "READY_FOR_REVIEW"
    assert v["completeness"]["score"] == 1.0
    assert "FIU-IND" in report["formatted_markdown_report"]
    agents = [s["agent_name"] for s in state["agent_trail"]]
    assert any("FilingDecision" in a for a in agents)
    assert any("FactChecker" in a for a in agents)


def test_agents_never_see_ground_truth_labels(upi_case):
    _, state = upi_case
    for t in state["evidence_data"]["recent_transactions"]:
        assert "is_fraud_injected" not in t and "fraud_pattern_type" not in t


def test_fact_checker_catches_hallucinations(upi_case):
    _, state = upi_case
    r = copy.deepcopy(state["sar_report"])
    real = next(c for c in r["claims"] if c["claim_id"] == "C_INFLOW")
    # 1. invented number inside an otherwise real sentence
    real["text"] = real["text"].replace("from", "from 15 accounts, from", 1)
    # 2. claim with no evidence (the old template's '+3.14 standard deviations')
    r["claims"].append({"claim_id": "C_FAKE", "category": "why", "evidence_ids": [], "assertions": [],
                        "subject_accounts": [], "text": "Velocity deviated +3.14 standard deviations."})
    # 3. claim with real evidence but a wrong total
    r["claims"].append({"claim_id": "C_WRONG", "category": "what", "evidence_ids": real["evidence_ids"],
                        "assertions": [{"metric": "total_amount", "op": "==", "value": 999999.0}],
                        "subject_accounts": [], "text": "The account received ₹9,99,999.00."})
    # 4. evidence ID that does not exist
    r["claims"].append({"claim_id": "C_GHOST", "category": "what", "evidence_ids": ["TXN_DOES_NOT_EXIST"],
                        "assertions": [{"metric": "txn_count", "op": "==", "value": 1}],
                        "subject_accounts": [], "text": "There was 1 transfer."})
    # 5. number smuggled into free text
    r["modus_operandi"] += " Roughly 40 victims were involved."

    checked, v = fact_check_report(r)
    status = {c["claim_id"]: c["status"] for c in checked["claims"]}
    assert status["C_INFLOW"] == "UNVERIFIED"
    assert status["C_FAKE"] == "UNVERIFIED"
    assert status["C_WRONG"] == "UNVERIFIED"
    assert status["C_GHOST"] == "UNVERIFIED"
    assert v["free_text_issues"]
    assert v["approval_status"] == "BLOCKED_UNVERIFIED_CLAIMS"


def test_api_blocks_approval_of_unverified_report(upi_case):
    case_id, state = upi_case
    client = TestClient(app)
    db = SessionLocal()
    try:
        case = db.query(InvestigationCase).filter(InvestigationCase.case_id == case_id).first()
        tampered = copy.deepcopy(case.sar_narrative_json)
        tampered["verification"]["approval_status"] = "BLOCKED_UNVERIFIED_CLAIMS"
        tampered["verification"]["unverified_claims"] = 1
        case.sar_narrative_json = tampered
        db.commit()
    finally:
        db.close()

    blocked = client.post(f"/api/investigations/{case_id}/feedback",
                          json={"feedback_type": "AGREE", "notes": "looks fine"})
    assert blocked.status_code == 409

    allowed = client.post(f"/api/investigations/{case_id}/feedback",
                          json={"feedback_type": "DISAGREE", "notes": "claim 3 is wrong"})
    assert allowed.status_code == 200
