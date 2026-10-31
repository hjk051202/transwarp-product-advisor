"""LangChain MCP adapter for the CRM server."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from langchain_mcp_adapters.client import MultiServerMCPClient

from fieldops.config import CRM_MCP_URL
from fieldops.db import approve_lead, get_by_crm_lead_id

_client = MultiServerMCPClient(
    {"crm": {"url": CRM_MCP_URL, "transport": "streamable_http"}}
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


async def create_lead_via_mcp(lead: dict[str, Any]) -> dict[str, Any]:
    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "create_lead"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke(
                {
                    "lead_id": lead["lead_id"],
                    "company": lead["company"],
                    "industry": lead["industry"],
                    "contact": lead["contact"],
                    "need": lead["need"],
                    "products": lead.get("products", []),
                }
            )
            return _content_to_json(result)
        except Exception as exc:
            fallback_error = str(exc)
    else:
        fallback_error = "MCP create_lead tool not available"

    crm_lead_id = f"CRM-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:4].upper()}"
    approve_lead(lead["lead_id"], crm_lead_id)
    return {
        "crm_lead_id": crm_lead_id,
        "lead_id": lead["lead_id"],
        "status": "approved_local_fallback",
        "mcp_error": fallback_error,
    }


async def get_lead(crm_lead_id: str) -> dict[str, Any] | None:
    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "get_lead"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke({"crm_lead_id": crm_lead_id})
            data = _content_to_json(result)
            if data.get("crm_lead_id"):
                return data
        except Exception:
            pass
    return get_by_crm_lead_id(crm_lead_id)
