from fastapi.testclient import TestClient
from app.main import app
from app.api.routes import RISKY_EXAMPLE, HARDENED_EXAMPLE

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rules():
    response = client.get("/api/rules")
    assert response.status_code == 200
    assert len(response.json()) >= 10


def test_risky_manifest_has_findings():
    response = client.post("/api/analyze", json={"name": "risky", "content": RISKY_EXAMPLE})
    assert response.status_code == 200
    data = response.json()
    assert data["score"] < 65
    assert data["severity_counts"]["critical"] >= 1
    assert data["severity_counts"]["high"] >= 1


def test_hardened_manifest_scores_better():
    risky = client.post("/api/analyze", json={"name": "risky", "content": RISKY_EXAMPLE}).json()
    hardened = client.post("/api/analyze", json={"name": "hardened", "content": HARDENED_EXAMPLE}).json()
    assert hardened["score"] > risky["score"]


def test_invalid_yaml_returns_422():
    response = client.post("/api/analyze", json={"name": "broken", "content": "kind: ["})
    assert response.status_code == 422
