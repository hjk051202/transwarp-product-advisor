"""CMMS adapters: MCP (default), HTTP, and local SQLite fallback."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from fieldops.db import approve_draft, get_by_work_order_id
from fieldops.integrations.base import CMMSAdapter
from fieldops.mcp_client import (
    create_work_order_via_mcp,
    get_work_order as get_work_order_via_mcp,
)


class MCPCMMSAdapter:
    async def create_work_order(self, draft: dict[str, Any]) -> dict[str, Any]:
        return await create_work_order_via_mcp(draft)

    async def get_work_order(self, work_order_id: str) -> dict[str, Any] | None:
        return await get_work_order_via_mcp(work_order_id)


class LocalCMMSAdapter:
    async def create_work_order(self, draft: dict[str, Any]) -> dict[str, Any]:
        work_order_id = f"WO-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:4].upper()}"
        approve_draft(draft["draft_id"], work_order_id)
        return {
            "work_order_id": work_order_id,
            "draft_id": draft["draft_id"],
            "status": "approved_local",
        }

    async def get_work_order(self, work_order_id: str) -> dict[str, Any] | None:
        return get_by_work_order_id(work_order_id)


class HttpCMMSAdapter:
    """Skeleton adapter for a real CMMS REST API."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key} if api_key else {}

    async def create_work_order(self, draft: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/work-orders",
                json=draft,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_work_order(self, work_order_id: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/work-orders/{work_order_id}",
                headers=self.headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()


def build_cmms_adapter() -> CMMSAdapter:
    kind = os.getenv("CMMS_ADAPTER", "mcp").lower()
    if kind == "local":
        return LocalCMMSAdapter()
    if kind == "http":
        return HttpCMMSAdapter(
            base_url=os.getenv("CMMS_HTTP_URL", "http://127.0.0.1:9000"),
            api_key=os.getenv("CMMS_HTTP_API_KEY", ""),
        )
    return MCPCMMSAdapter()
