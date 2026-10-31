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
                "message": "ArgoDB 和 TDH 怎么选？",
                "company": "某城商行",
                "industry": "金融",
                "contact": "demo@example.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        assert data["citations"]
        assert data["lead"]["lead_id"].startswith("LEAD-")

        lead_id = data["lead"]["lead_id"]
        approved = client.post(f"/leads/{lead_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["crm_lead_id"].startswith("CRM-")
