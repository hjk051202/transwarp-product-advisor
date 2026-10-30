"""LangChain agent assembly for FieldOps Copilot."""

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
from fieldops.mcp_client import get_mcp_tools
from fieldops.mock_llm import MockToolCallingModel
from fieldops.tools import NATIVE_TOOLS

SYSTEM_PROMPT = """你是「设备售后运维助手」，面向工业设备厂商的售后工程师。

工作规则：
1. 安全第一：涉及高压、燃气、安全联锁时，先要求停机挂牌（LOTO），再给建议。
2. 故障诊断必须检索手册/服务公告/历史工单，并引用文档名、章节和页码。
3. 设备实时工况、保修、备件库存必须调用工具查询，不能凭文档猜测。
4. 不编造备件号、故障码和处理步骤；资料不足时明确说“资料不足，建议转人工”。
5. 诊断完成后，调用 draft_work_order 生成工单草稿；不要直接创建正式工单。
6. 写操作需要工程师在界面上确认，草稿不是正式工单。
7. 回答结构：初步判断 → 建议排查 → 保修/备件 → 依据。
"""

_agent: Any | None = None
_mode: str = "offline"


def build_model() -> tuple[Any, str]:
    if DEEPSEEK_API_KEY:
        model = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            temperature=0,
        )
        return model, "deepseek"
    if OPENAI_API_KEY:
        model = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0,
        )
        return model, "openai"
    return MockToolCallingModel(), "offline-mock"


async def build_agent() -> tuple[Any, str]:
    model, mode = build_model()
    tools = list(NATIVE_TOOLS)
    try:
        mcp_tools = await get_mcp_tools()
        tools.extend(mcp_tools)
        if not mcp_tools:
            mode = f"{mode}-mcp-unavailable"
    except Exception:
        mode = f"{mode}-mcp-unavailable"

    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
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
