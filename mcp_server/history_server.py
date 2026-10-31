"""Conversation-history MCP server."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from fieldops.db import (
    create_conversation,
    get_conversation as get_conversation_record,
    init_db,
    list_conversations,
)

mcp = FastMCP(
    "history",
    host=os.getenv("MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("MCP_PORT", "8765")),
)


@mcp.tool()
def save_conversation(
    conversation_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
    citations: list[dict[str, Any]] | None = None,
    tool_trace: list[dict[str, Any]] | None = None,
    mode: str = "offline",
) -> dict:
    """Save one completed chat exchange to conversation history."""

    init_db()
    return create_conversation(
        conversation_id=conversation_id,
        session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
        citations=citations or [],
        tool_trace=tool_trace or [],
        mode=mode,
    )


@mcp.tool()
def get_conversation(conversation_id: str) -> dict:
    """Read a saved conversation by ID."""

    init_db()
    conversation = get_conversation_record(conversation_id)
    if not conversation:
        return {"error": f"conversation {conversation_id} not found"}
    return conversation


@mcp.tool()
def list_conversations(limit: int = 20) -> dict:
    """List recent conversation history."""

    init_db()
    return {"conversations": list_conversations(limit=max(1, min(limit, 100)))}


if __name__ == "__main__":
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "stdio"))  # type: ignore[arg-type]
