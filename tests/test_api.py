from __future__ import annotations

from fastapi.testclient import TestClient

from fieldops.main import app


def test_health_chat_and_history() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        response = client.post(
            "/chat",
            json={
                "message": "ArgoDB 和 TDH 怎么选？",
                "session_id": "SESS-api-test",
                "company": "某城商行",
                "industry": "金融",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        assert data["conversation_id"].startswith("CONV-")

        conversations = client.get("/conversations?limit=5")
        assert conversations.status_code == 200
        assert any(
            item["conversation_id"] == data["conversation_id"]
            for item in conversations.json()
        )

        detail = client.get(f"/conversations/{data['conversation_id']}")
        assert detail.status_code == 200
        assert detail.json()["session_id"] == "SESS-api-test"
