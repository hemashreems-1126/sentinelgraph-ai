from fastapi.testclient import TestClient

from app.config import settings
from app.db.session import init_db
from app.main import app
from app.security import cors_settings


def _client():
    init_db()
    return TestClient(app)


def test_security_headers_present():
    res = _client().get("/api/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "no-referrer"


def test_admin_token_blocks_dataset_reset_and_evaluation(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "s3cret-token")
    c = _client()
    body = {"num_customers": 40, "num_transactions": 200, "seed": 42, "confirm_reset": True}
    assert c.post("/api/alerts/generate", json=body).status_code == 401
    assert c.post("/api/alerts/generate", json=body, headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert c.post("/api/evaluation/run", json={}).status_code == 401
    ok = c.post("/api/alerts/generate", json=body, headers={"X-Admin-Token": "s3cret-token"})
    assert ok.status_code == 200
    # Reads stay open for analysts.
    assert c.get("/api/alerts").status_code == 200


def test_no_token_configured_keeps_local_dev_open(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_TOKEN", None)
    res = _client().post("/api/alerts/generate", json={"num_customers": 40, "num_transactions": 200, "seed": 42})
    assert res.status_code == 400  # reaches the handler (needs confirm_reset), not 401


def test_cors_never_combines_wildcard_with_credentials(monkeypatch):
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "*")
    assert cors_settings()["allow_credentials"] is False
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", "https://sentinelgraph-frontend.onrender.com, http://localhost:5173")
    cfg = cors_settings()
    assert cfg["allow_origins"] == ["https://sentinelgraph-frontend.onrender.com", "http://localhost:5173"]
    assert cfg["allow_credentials"] is True
