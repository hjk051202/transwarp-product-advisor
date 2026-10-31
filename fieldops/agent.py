"""LangChain agent assembly for the Transwarp product advisor."""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from fieldops.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    OPENAI_API_KEY,
    OPENAI_MODEL,
)
from fieldops.mock_llm import ProductAdvisorModel
from fieldops.tools import NATIVE_TOOLS

SYSTEM_PROMPT = """你是「星环产品选型助手」，面向星环科技的产品售前和客户咨询。

工作规则：
1. 先澄清业务负载、数据量、部署环境和国产化要求，再给产品建议。
2. 产品定位和适用场景必须检索公开产品资料/选型指南，并引用文档名、章节、页码。
3. 需要对比时调用 compare_products；需要案例时调用 search_cases；国产化问题调用 check_compatibility。
4. 不编造产品版本、价格、性能数字和客户名称；不确定时明确说“需以官方资料/售前确认为准”。
5. 对比产品时要说明“为什么不是另一个”，不要只列优点。
6. 回答结构：需求判断 → 推荐方案 → 对比/案例/兼容性 → 依据。
"""

_agent: Any | None = None
_mode: str = "offline"


def build_model() -> tuple[Any, str]:
    if DEEPSEEK_API_KEY:
        return (
            ChatOpenAI(
                model=DEEPSEEK_MODEL,
                api_key=DEEPSEEK_API_KEY,
                base_url=DEEPSEEK_BASE_URL,
                temperature=0,
            ),
            "deepseek",
        )
    if OPENAI_API_KEY:
        return (
            ChatOpenAI(
                model=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=0,
            ),
            "openai",
        )
    return ProductAdvisorModel(), "offline-mock"


async def build_agent() -> tuple[Any, str]:
    model, mode = build_model()
    agent = create_agent(model=model, tools=list(NATIVE_TOOLS), system_prompt=SYSTEM_PROMPT)
    return agent, mode


async def get_agent() -> tuple[Any, str]:
    global _agent, _mode
    if _agent is None:
        _agent, _mode = await build_agent()
    return _agent, _mode


def reset_agent() -> None:
    global _agent, _mode
    _agent = None
    _mode = "offline"
