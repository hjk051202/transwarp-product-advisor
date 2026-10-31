from __future__ import annotations

import pytest

from fieldops.db import create_lead
from fieldops.integrations import build_catalog_adapter, build_crm_adapter


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
async def test_local_crm_adapter(monkeypatch) -> None:
    monkeypatch.setenv("CRM_ADAPTER", "local")
    lead = create_lead(
        lead_id="LEAD-adapter-test",
        company="adapter test",
        industry="金融",
        contact="test@example.com",
        need="ArgoDB 选型",
        products=["ArgoDB"],
    )
    adapter = build_crm_adapter()
    result = await adapter.create_lead(lead)
    assert result["crm_lead_id"].startswith("CRM-")
    fetched = await adapter.get_lead(result["crm_lead_id"])
    assert fetched is not None
    assert fetched["lead_id"] == "LEAD-adapter-test"
