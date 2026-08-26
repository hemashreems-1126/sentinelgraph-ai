import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db


@pytest.fixture
def client():
    init_db()
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SentinelGraph"


def test_generate_and_list_alerts(client):
    # 1. Generate alerts
    gen_res = client.post("/api/alerts/generate", json={"num_customers": 40, "num_transactions": 200, "seed": 42})
    assert gen_res.status_code == 200
    data = gen_res.json()
    assert data["alerts_generated_count"] > 0

    # 2. List alerts
    list_res = client.get("/api/alerts")
    assert list_res.status_code == 200
    alerts = list_res.json()
    assert len(alerts) > 0

    # 3. Triage & Prioritize
    prio_res = client.post("/api/alerts/prioritize", json={"batch_size": 20})
    assert prio_res.status_code == 200
    triaged = prio_res.json()
    assert len(triaged) > 0


def test_evaluation_api(client):
    eval_res = client.get("/api/evaluation/latest")
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert "precision_score" in data
    assert "recall_score" in data
    assert "confusion_matrix_json" in data
