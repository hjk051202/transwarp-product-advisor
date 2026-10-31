"""CRM adapters: MCP (default), HTTP, and local SQLite fallback."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from fieldops.db import approve_lead, get_by_crm_lead_id
from fieldops.integrations.base import CRMAdapter
from fieldops.mcp_client import create_lead_via_mcp, get_lead as get_lead_via_mcp


class MCPCRMAdapter:
    async def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        return await create_lead_via_mcp(lead)

    async def get_lead(self, crm_lead_id: str) -> dict[str, Any] | None:
        return await get_lead_via_mcp(crm_lead_id)


class LocalCRMAdapter:
    async def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        crm_lead_id = f"CRM-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:4].upper()}"
        approve_lead(lead["lead_id"], crm_lead_id)
        return {
            "crm_lead_id": crm_lead_id,
            "lead_id": lead["lead_id"],
            "status": "approved_local",
        }

    async def get_lead(self, crm_lead_id: str) -> dict[str, Any] | None:
        return get_by_crm_lead_id(crm_lead_id)


class HttpCRMAdapter:
    """Skeleton adapter for a real CRM REST API."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key} if api_key else {}

    async def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/leads", json=lead, headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_lead(self, crm_lead_id: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/leads/{crm_lead_id}", headers=self.headers
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()


def build_crm_adapter() -> CRMAdapter:
    kind = os.getenv("CRM_ADAPTER", "mcp").lower()
    if kind == "local":
        return LocalCRMAdapter()
    if kind == "http":
        return HttpCRMAdapter(
            base_url=os.getenv("CRM_HTTP_URL", "http://127.0.0.1:9000"),
            api_key=os.getenv("CRM_HTTP_API_KEY", ""),
        )
    return MCPCRMAdapter()
