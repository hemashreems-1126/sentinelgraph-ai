import pytest
from app.db.session import SessionLocal, init_db
from app.db.models import Customer, Account, Transaction
from app.services.data_generator import SyntheticAMLDataGenerator


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_synthetic_data_generator_generates_entities(db_session):
    generator = SyntheticAMLDataGenerator(seed=42)
    stats = generator.generate_and_seed_database(
        db_session,
        num_customers=50,
        num_transactions=300
    )

    assert stats["num_customers"] == 50
    assert stats["num_accounts"] >= 50
    assert stats["total_transactions"] >= 300
    assert stats["injected_fraud_transactions"] > 0
    assert 0.05 <= stats["fraud_ratio"] <= 0.25

    customers = db_session.query(Customer).all()
    assert len(customers) == 50

    # Verify fraud pattern distribution
    fraud_txns = db_session.query(Transaction).filter(Transaction.is_fraud_injected == True).all()
    fraud_types = {t.fraud_pattern_type for t in fraud_txns}
    assert "STRUCTURING" in fraud_types or "LAYERING" in fraud_types or "MULE_ACCOUNT" in fraud_types
