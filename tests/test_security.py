from __future__ import annotations

from fastapi.testclient import TestClient

from fieldops.main import app


def test_api_key_required(monkeypatch) -> None:
    monkeypatch.setenv("FIELDOPS_API_KEY", "test-secret")
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/chat", json={"message": "hello"}).status_code == 401
        response = client.post(
            "/chat",
            json={"message": "X100 报 E-204，出水温度高。", "serial": "8F2-1042"},
            headers={"X-API-Key": "test-secret"},
        )
        assert response.status_code == 200
        assert response.headers["X-Request-ID"]


def test_audit_log_written() -> None:
    with TestClient(app) as client:
        client.post(
            "/chat",
            json={"message": "SN 8F2-1042 还在保修吗？", "serial": "8F2-1042"},
            headers={"X-User": "pytest"},
        )
        logs = client.get("/audit?limit=10")
        assert logs.status_code == 200
        assert any(item["action"] == "chat.request" for item in logs.json())
