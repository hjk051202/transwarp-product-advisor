from __future__ import annotations

from fastapi.testclient import TestClient

from fieldops.main import app


def test_health_and_chat() -> None:
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        response = client.post(
            "/chat",
            json={
                "message": "X100 报 E-204，出水温度高，客户已停机。",
                "serial": "8F2-1042",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        assert data["citations"]
        assert data["draft"]["draft_id"].startswith("DRF-")

        draft_id = data["draft"]["draft_id"]
        approved = client.post(f"/work-orders/{draft_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["work_order_id"].startswith("WO-")
