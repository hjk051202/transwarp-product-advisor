"""Native LangChain tools for product selection and lead capture."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from langchain_core.tools import tool

from fieldops.data import (
    check_compatibility as compatibility_lookup,
    get_product,
    list_products as list_product_data,
    search_cases as search_case_data,
)
from fieldops.db import create_lead
from fieldops.rag import search_json


def _dumps(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@tool
def search_knowledge(query: str) -> str:
    """检索星环产品资料、选型指南、案例和兼容性说明。

    当需要产品定位、适用场景、案例或国产化兼容性依据时使用。
    返回结果包含 doc_id、产品、章节、页码和原文片段，回答时应引用。

    Args:
        query: 检索关键词，例如 ArgoDB TDH 数据仓库 选型。
    """

    return search_json(query, k=4)


@tool
def list_products(workload: str | None = None, industry: str | None = None) -> str:
    """列出星环产品及其定位。

    当客户想了解产品线，或需要按业务负载/行业筛选产品时使用。

    Args:
        workload: 业务负载，例如 报表、实时分析、数据湖、OLTP、图。
        industry: 行业，例如 金融、政务、能源、制造。
    """

    products = list_product_data(workload=workload, industry=industry)
    return _dumps(
        [
            {
                "product": item["key"],
                "name": item["name"],
                "category": item["category"],
                "one_liner": item["one_liner"],
                "workloads": item["workloads"],
                "industries": item["industries"],
            }
            for item in products
        ]
    )


@tool
def compare_products(product_a: str, product_b: str) -> str:
    """对比两个星环产品的定位、适用场景和差异。

    当客户在两个产品之间犹豫，例如 ArgoDB vs TDH、TDH vs TDC 时使用。

    Args:
        product_a: 第一个产品名，例如 ArgoDB。
        product_b: 第二个产品名，例如 TDH。
    """

    left = get_product(product_a)
    right = get_product(product_b)
    if not left or not right:
        return _dumps(
            {
                "error": "产品名不存在，可选：ArgoDB、TDH、TDC、Sophon、StellarDB、KunDB",
                "product_a": product_a,
                "product_b": product_b,
            }
        )
    return _dumps(
        {
            "product_a": {
                "product": left["key"],
                "category": left["category"],
                "one_liner": left["one_liner"],
                "workloads": left["workloads"],
                "strengths": left["strengths"],
                "not_primary_for": left["not_primary_for"],
            },
            "product_b": {
                "product": right["key"],
                "category": right["category"],
                "one_liner": right["one_liner"],
                "workloads": right["workloads"],
                "strengths": right["strengths"],
                "not_primary_for": right["not_primary_for"],
            },
            "decision_hint": (
                f"如果需求更接近 {left['workloads'][0]}，优先 {left['key']}；"
                f"如果更接近 {right['workloads'][0]}，优先 {right['key']}。"
            ),
        }
    )


@tool
def search_cases(industry: str, scenario: str = "") -> str:
    """检索星环在某个行业的公开案例摘要。

    当客户问“有没有同行业案例”时使用。

    Args:
        industry: 行业，例如 金融、政务、能源、制造。
        scenario: 场景关键词，例如 数据仓库、反欺诈、图谱。
    """

    cases = search_case_data(industry=industry, scenario=scenario)
    return _dumps({"industry": industry, "count": len(cases), "cases": cases})


@tool
def check_compatibility(os_name: str, cpu: str) -> str:
    """查询星环产品对操作系统和 CPU 的兼容性摘要。

    当客户问国产化、麒麟/统信、鲲鹏/海光适配时使用。
    返回的是演示摘要，具体版本必须以官方兼容性列表为准。

    Args:
        os_name: 操作系统，例如 麒麟、统信、CentOS。
        cpu: CPU 架构，例如 x86、鲲鹏、海光。
    """

    return _dumps(compatibility_lookup(os_name, cpu))


@tool
def draft_lead(
    company: str,
    industry: str,
    contact: str,
    need: str,
    products: list[str] | None = None,
) -> str:
    """生成售前线索草稿，但不直接写入 CRM。

    当客户表达选型、试用、报价、方案交流等意向时使用。
    该工具只写本地 draft 表，必须由销售/售前确认后才能写入 CRM。

    Args:
        company: 客户公司名。
        industry: 行业。
        contact: 联系方式（可脱敏）。
        need: 客户需求摘要。
        products: 推荐产品列表。
    """

    products = products or []
    lead_id = f"LEAD-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:4]}"
    lead = create_lead(
        lead_id=lead_id,
        company=company or "待补充",
        industry=industry or "待补充",
        contact=contact or "待补充",
        need=need,
        products=products,
    )
    return _dumps(lead)


NATIVE_TOOLS = [
    search_knowledge,
    list_products,
    compare_products,
    search_cases,
    check_compatibility,
    draft_lead,
]
