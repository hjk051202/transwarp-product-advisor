from __future__ import annotations

import pytest

from fieldops.mcp_client import get_mcp_tools


@pytest.mark.asyncio
async def test_cmms_mcp_tools_discovered() -> None:
    tools = await get_mcp_tools()
    if not tools:
        pytest.skip("cmms-mcp is not running on 127.0.0.1:8765")
    names = {tool.name for tool in tools}
    assert {"create_work_order", "get_work_order"} <= names
