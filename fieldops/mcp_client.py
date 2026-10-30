"""LangChain MCP adapter for the CMMS server.

The server is normally started as a separate process:
    MCP_TRANSPORT=streamable-http python -m mcp_server.cmms_server

The client talks to it over Streamable HTTP, so it also works in environments
where stdio pipes are restricted.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from langchain_mcp_adapters.client import MultiServerMCPClient

from fieldops.db import approve_draft, get_by_work_order_id

MCP_URL = os.getenv("CMMS_MCP_URL", "http://127.0.0.1:8765/mcp")
_client = MultiServerMCPClient(
    {"cmms": {"url": MCP_URL, "transport": "streamable_http"}}
)
_tools: list[Any] | None = None


async def get_mcp_tools() -> list[Any]:
    global _tools
    if not _tools:
        try:
            _tools = await _client.get_tools()
        except Exception:
            _tools = []
    return _tools


def _content_to_json(result: Any) -> dict[str, Any]:
    """Normalize MCP content blocks (or a plain dict/string) to a dict."""

    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            value = json.loads(result)
            return value if isinstance(value, dict) else {"result": value}
        except json.JSONDecodeError:
            return {"result": result}
    if isinstance(result, list):
        for item in result:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                try:
                    value = json.loads(item["text"])
                    if isinstance(value, dict):
                        return value
                except json.JSONDecodeError:
                    return {"result": item["text"]}
        return {"result": result}
    return {"result": result}


async def create_work_order_via_mcp(draft: dict[str, Any]) -> dict[str, Any]:
    """Call cmms-mcp.create_work_order, with a local fallback for demos."""

    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "create_work_order"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke(
                {
                    "draft_id": draft["draft_id"],
                    "asset_id": draft["asset_id"],
                    "title": draft["title"],
                    "description": draft["description"],
                    "priority": draft["priority"],
                    "parts": draft.get("parts", []),
                    "scheduled_at": draft.get("scheduled_at"),
                }
            )
            return _content_to_json(result)
        except Exception as exc:  # keep the demo usable if MCP is down
            fallback_error = str(exc)
    else:
        fallback_error = "MCP create_work_order tool not available"

    work_order_id = f"WO-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:4].upper()}"
    approve_draft(draft["draft_id"], work_order_id)
    return {
        "work_order_id": work_order_id,
        "draft_id": draft["draft_id"],
        "status": "approved_local_fallback",
        "mcp_error": fallback_error,
    }


async def get_work_order(work_order_id: str) -> dict[str, Any] | None:
    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "get_work_order"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke({"work_order_id": work_order_id})
            data = _content_to_json(result)
            if data.get("work_order_id"):
                return data
        except Exception:
            pass
    return get_by_work_order_id(work_order_id)
