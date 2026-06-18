from fastapi.testclient import TestClient

from app.examples import get_example
from app.main import app

client = TestClient(app)

RISKY = get_example("risky-web.yaml").content
HARDENED = get_example("hardened-web.yaml").content


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_reports_ai_disabled_by_default():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ai"] == {"provider": "none", "enabled": False}


def test_rules_endpoint():
    response = client.get("/api/rules")
    assert response.status_code == 200
    rules = response.json()
    assert len(rules) >= 30
    assert {r["id"] for r in rules} >= {"PS-W001", "PS-A004", "PS-N003", "PS-S003"}


def test_examples_endpoint_returns_six():
    response = client.get("/api/examples")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "risky-web.yaml" in names
    assert len(names) == 6


def test_risky_manifest_fails():
    response = client.post("/api/analyze", json={"name": "risky", "content": RISKY})
    assert response.status_code == 200
    data = response.json()
    assert data["scorecard"]["status"] == "fail"
    assert data["scorecard"]["score"] < 60
    assert data["severity_counts"]["critical"] >= 1


def test_hardened_scores_higher_than_risky():
    risky = client.post("/api/analyze", json={"name": "r", "content": RISKY}).json()
    hardened = client.post("/api/analyze", json={"name": "h", "content": HARDENED}).json()
    assert hardened["scorecard"]["score"] > risky["scorecard"]["score"]
    assert hardened["scorecard"]["grade"] in {"A", "B", "C"}


def test_category_filter_limits_findings():
    payload = {
        "name": "filtered",
        "content": RISKY,
        "options": {"categories": ["RBAC"]},
    }
    data = client.post("/api/analyze", json=payload).json()
    categories = {finding["category"] for finding in data["findings"]}
    assert categories == {"RBAC"}


def test_strict_mode_escalates_severity():
    payload = {"name": "strict", "content": HARDENED, "options": {"strict": True}}
    normal = client.post("/api/analyze", json={"name": "n", "content": HARDENED}).json()
    strict = client.post("/api/analyze", json=payload).json()
    assert strict["scorecard"]["score"] <= normal["scorecard"]["score"]


def test_invalid_yaml_returns_422():
    response = client.post("/api/analyze", json={"name": "broken", "content": "kind: ["})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_ai_summary_falls_back_to_deterministic():
    response = client.post("/api/ai/summarize", json={"name": "risky", "content": RISKY})
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "none"
    assert body["ai_enabled"] is False
    assert body["prioritized_fixes"]


def test_ai_remediate_returns_items():
    response = client.post("/api/ai/remediate", json={"name": "risky", "content": RISKY})
    assert response.status_code == 200
    body = response.json()
    assert body["items"]
    assert body["items"][0]["rule_id"].startswith("PS-")
