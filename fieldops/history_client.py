"""LangChain MCP adapter for conversation history."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from langchain_mcp_adapters.client import MultiServerMCPClient

from fieldops.config import HISTORY_MCP_URL
from fieldops.db import create_conversation, get_conversation, list_conversations

_client = MultiServerMCPClient(
    {"history": {"url": HISTORY_MCP_URL, "transport": "streamable_http"}}
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


async def save_conversation_via_mcp(
    *,
    session_id: str,
    user_message: str,
    assistant_message: str,
    citations: list[dict[str, Any]],
    tool_trace: list[dict[str, Any]],
    mode: str,
) -> dict[str, Any]:
    conversation_id = f"CONV-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:4]}"
    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "save_conversation"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke(
                {
                    "conversation_id": conversation_id,
                    "session_id": session_id,
                    "user_message": user_message,
                    "assistant_message": assistant_message,
                    "citations": citations,
                    "tool_trace": tool_trace,
                    "mode": mode,
                }
            )
            return _content_to_json(result)
        except Exception:
            pass

    return create_conversation(
        conversation_id=conversation_id,
        session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
        citations=citations,
        tool_trace=tool_trace,
        mode=mode,
    )


async def list_conversations_via_mcp(limit: int = 20) -> list[dict[str, Any]]:
    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "list_conversations"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke({"limit": limit})
            data = _content_to_json(result)
            items = data.get("conversations")
            if isinstance(items, list):
                return items
        except Exception:
            pass
    return list_conversations(limit=limit)


async def get_conversation_via_mcp(conversation_id: str) -> dict[str, Any] | None:
    tools = await get_mcp_tools()
    tool = next((item for item in tools if item.name == "get_conversation"), None)
    if tool is not None:
        try:
            result = await tool.ainvoke({"conversation_id": conversation_id})
            data = _content_to_json(result)
            if data.get("conversation_id"):
                return data
        except Exception:
            pass
    return get_conversation(conversation_id)
