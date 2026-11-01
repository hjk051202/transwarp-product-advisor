"""History adapters: MCP (default), HTTP, and local SQLite fallback."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx

from fieldops.db import create_conversation, get_conversation, list_conversations
from fieldops.history_client import (
    get_conversation_via_mcp,
    list_conversations_via_mcp,
    save_conversation_via_mcp,
)
from fieldops.integrations.base import HistoryAdapter


class MCPHistoryAdapter:
    async def save_conversation(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await save_conversation_via_mcp(**payload)

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        return await get_conversation_via_mcp(conversation_id)

    async def list_conversations(self, limit: int = 20) -> list[dict[str, Any]]:
        return await list_conversations_via_mcp(limit=limit)


class LocalHistoryAdapter:
    async def save_conversation(self, payload: dict[str, Any]) -> dict[str, Any]:
        payload = dict(payload)
        payload.setdefault(
            "conversation_id",
            f"CONV-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:4]}",
        )
        return create_conversation(**payload)

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        return get_conversation(conversation_id)

    async def list_conversations(self, limit: int = 20) -> list[dict[str, Any]]:
        return list_conversations(limit=limit)


class HttpHistoryAdapter:
    """Skeleton adapter for a real conversation-history API."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key} if api_key else {}

    async def save_conversation(self, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/conversations", json=payload, headers=self.headers
            )
            response.raise_for_status()
            return response.json()

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/conversations/{conversation_id}",
                headers=self.headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def list_conversations(self, limit: int = 20) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/conversations",
                params={"limit": limit},
                headers=self.headers,
            )
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, list) else []


def build_history_adapter() -> HistoryAdapter:
    kind = os.getenv("HISTORY_ADAPTER", "mcp").lower()
    if kind == "local":
        return LocalHistoryAdapter()
    if kind == "http":
        return HttpHistoryAdapter(
            base_url=os.getenv("HISTORY_HTTP_URL", "http://127.0.0.1:9000"),
            api_key=os.getenv("HISTORY_HTTP_API_KEY", ""),
        )
    return MCPHistoryAdapter()
