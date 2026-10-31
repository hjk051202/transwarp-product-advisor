from __future__ import annotations

import pytest

from fieldops.db import create_conversation
from fieldops.integrations import build_catalog_adapter, build_history_adapter


def test_json_catalog_adapter() -> None:
    catalog = build_catalog_adapter()
    product = catalog.get_product("ArgoDB")
    assert product is not None
    assert product["category"].startswith("分布式分析型")

    products = catalog.list_products(workload="报表")
    assert any(item["key"] == "ArgoDB" for item in products)

    cases = catalog.search_cases(industry="金融")
    assert cases


@pytest.mark.asyncio
async def test_local_history_adapter(monkeypatch) -> None:
    monkeypatch.setenv("HISTORY_ADAPTER", "local")
    created = create_conversation(
        conversation_id="CONV-adapter-test",
        session_id="SESS-adapter",
        user_message="ArgoDB 和 TDH 怎么选？",
        assistant_message="建议根据报表/数仓需求选型。",
        citations=[],
        tool_trace=[],
        mode="offline",
    )
    adapter = build_history_adapter()
    fetched = await adapter.get_conversation(created["conversation_id"])
    assert fetched is not None
    assert fetched["session_id"] == "SESS-adapter"

    items = await adapter.list_conversations(limit=10)
    assert any(item["conversation_id"] == "CONV-adapter-test" for item in items)
