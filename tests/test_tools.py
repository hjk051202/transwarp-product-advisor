from __future__ import annotations

import json

from fieldops.tools import (
    check_compatibility,
    compare_products,
    draft_lead,
    list_products,
    search_cases,
)


def test_list_and_compare_products() -> None:
    products = json.loads(list_products.invoke({"workload": "报表"}))
    assert any(item["product"] == "ArgoDB" for item in products)

    comparison = json.loads(
        compare_products.invoke({"product_a": "ArgoDB", "product_b": "TDH"})
    )
    assert comparison["product_a"]["product"] == "ArgoDB"
    assert comparison["product_b"]["product"] == "TDH"


def test_cases_and_compatibility() -> None:
    cases = json.loads(search_cases.invoke({"industry": "金融"}))
    assert cases["count"] >= 1

    compat = json.loads(
        check_compatibility.invoke({"os_name": "麒麟", "cpu": "鲲鹏"})
    )
    assert compat["os_support"]
    assert compat["cpu_support"]


def test_draft_lead_tool() -> None:
    lead = json.loads(
        draft_lead.invoke(
            {
                "company": "pytest 银行",
                "industry": "金融",
                "contact": "pytest@example.com",
                "need": "ArgoDB 选型",
                "products": ["ArgoDB"],
            }
        )
    )
    assert lead["lead_id"].startswith("LEAD-")
    assert lead["status"] == "draft"
    assert lead["products"] == ["ArgoDB"]
