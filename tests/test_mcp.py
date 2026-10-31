from __future__ import annotations

import pytest

from fieldops.history_client import get_mcp_tools


@pytest.mark.asyncio
async def test_history_mcp_tools_discovered() -> None:
    tools = await get_mcp_tools()
    if not tools:
        pytest.skip("history-mcp is not running on 127.0.0.1:8765")
    names = {tool.name for tool in tools}
    assert {"save_conversation", "get_conversation", "list_conversations"} <= names
