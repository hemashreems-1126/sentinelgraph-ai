import pytest
from app.db.session import SessionLocal, init_db
from app.services.data_generator import SyntheticAMLDataGenerator
from app.services.monitor import transaction_monitor
from app.services.triage import alert_triage_service
from app.db.models import Alert


@pytest.fixture(scope="module")
def seeded_db():
    init_db()
    db = SessionLocal()
    gen = SyntheticAMLDataGenerator(seed=42)
    gen.generate_and_seed_database(db, num_customers=60, num_transactions=400)
    yield db
    db.close()


def test_monitor_detects_alerts(seeded_db):
    alerts = transaction_monitor.scan_and_generate_alerts(seeded_db)
    assert len(alerts) > 0

    alert_types = {a.alert_type for a in alerts}
    assert len(alert_types) >= 2  # Rule + ML isolation forest

    # Check split types are tagged
    train_count = sum(1 for a in alerts if a.split_type == "TRAIN")
    test_count = sum(1 for a in alerts if a.split_type == "TEST")
    assert train_count > 0
    assert test_count > 0


def test_triage_service_prioritizes_alerts(seeded_db):
    triaged = alert_triage_service.prioritize_alerts(seeded_db, limit=50)
    assert len(triaged) > 0

    # Ensure prioritized ranks are ordered (1, 2, 3...)
    ranks = [a.priority_rank for a in triaged]
    assert ranks == sorted(ranks)
    assert all(a.status == "TRIAGED" for a in triaged)
