import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal, init_db
from app.db.models import Alert, AuditLog
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.agents.workflow import execute_investigation_case


@pytest.fixture(scope="module")
def case_id():
    init_db()
    db = SessionLocal()
    try:
        SyntheticAMLDataGenerator(seed=11).generate_and_seed_database(db, num_customers=80, num_transactions=600)
        transaction_monitor.scan_and_generate_alerts(db)
        alert_id = db.query(Alert).first().alert_id
    finally:
        db.close()
    cid = f"CASE_AUDIT_{uuid.uuid4().hex[:6]}"
    execute_investigation_case(cid, alert_id)
    return cid


def test_untouched_chain_verifies(case_id):
    res = TestClient(app).get(f"/api/audit/verify/{case_id}").json()
    assert res["valid"] is True and res["entries"] >= 10


def test_analyst_signoff_is_chained(case_id):
    client = TestClient(app)
    r = client.post(f"/api/investigations/{case_id}/feedback",
                    json={"feedback_type": "DISAGREE", "notes": "needs more KYC"})
    assert r.status_code == 200
    res = client.get(f"/api/audit/verify/{case_id}").json()
    assert res["valid"] is True
    db = SessionLocal()
    try:
        last = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.id.desc()).first()
        assert last.action_type == "ANALYST_DISAGREE"
    finally:
        db.close()


def test_editing_an_entry_breaks_the_chain(case_id):
    db = SessionLocal()
    try:
        entry = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.id.asc()).offset(3).first()
        entry.output_payload = {**(entry.output_payload or {}), "tampered": True}
        db.commit()
    finally:
        db.close()
    res = TestClient(app).get(f"/api/audit/verify/{case_id}").json()
    assert res["valid"] is False and res["broken_at"] == 3


def test_deleting_an_entry_breaks_the_chain(case_id):
    db = SessionLocal()
    try:
        # restore order of business: remove an entry in the middle
        entry = db.query(AuditLog).filter(AuditLog.case_id == case_id).order_by(AuditLog.id.asc()).offset(5).first()
        db.delete(entry)
        db.commit()
    finally:
        db.close()
    res = TestClient(app).get(f"/api/audit/verify/{case_id}").json()
    assert res["valid"] is False
