"""Deterministic tool-calling model used when no LLM API key is configured.

It implements the small part of LangChain's BaseChatModel contract that
``create_agent`` needs: bind_tools + _generate. The behavior is intentionally
scripted so the demo and tests can run fully offline; set DEEPSEEK_API_KEY or
OPENAI_API_KEY to use a real model instead.
"""

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.outputs import ChatGeneration, ChatResult


def _extract_serial(text: str) -> str:
    match = re.search(r"\b([0-9A-Z]{3}-\d{4})\b", text.upper())
    return match.group(1) if match else "8F2-1042"


def _parse_json(content: Any) -> dict[str, Any]:
    if isinstance(content, dict):
        return content
    if not isinstance(content, str):
        return {}
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


class MockToolCallingModel(BaseChatModel):
    """A tiny rule-based model that emits realistic tool calls."""

    bound_tools: list[str] = []
    call_counter: int = 0

    @property
    def _llm_type(self) -> str:
        return "fieldops-mock"

    def bind_tools(self, tools: Any, *, tool_choice: Any = None, **kwargs: Any):
        names: list[str] = []
        for item in tools:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict):
                names.append(item.get("name") or item.get("function", {}).get("name", ""))
            else:
                names.append(getattr(item, "name", ""))
        self.bound_tools = [name for name in names if name]
        return self

    def _next_id(self, name: str) -> str:
        self.call_counter += 1
        return f"call_{name}_{self.call_counter}"

    def _call(self, name: str, args: dict[str, Any]) -> dict[str, Any] | None:
        if self.bound_tools and name not in self.bound_tools:
            return None
        return {"name": name, "args": args, "id": self._next_id(name), "type": "tool_call"}

    @staticmethod
    def _tool_messages(messages: list[BaseMessage]) -> list[ToolMessage]:
        return [m for m in messages if isinstance(m, ToolMessage)]

    @staticmethod
    def _latest(messages: list[BaseMessage], name: str) -> dict[str, Any]:
        for message in reversed(messages):
            if isinstance(message, ToolMessage) and message.name == name:
                return _parse_json(message.content)
        return {}

    @staticmethod
    def _text(messages: list[BaseMessage]) -> str:
        for message in reversed(messages):
            if isinstance(message, HumanMessage) and message.content:
                return str(message.content)
        return ""

    def _final_answer(
        self, messages: list[BaseMessage], draft: dict[str, Any], is_e204: bool
    ) -> str:
        telemetry = self._latest(messages, "get_telemetry")
        warranty = self._latest(messages, "check_warranty")
        parts = self._latest(messages, "check_parts")
        knowledge = self._latest(messages, "search_knowledge")
        results = knowledge.get("results", []) if isinstance(knowledge, dict) else []

        if not is_e204:
            lines: list[str] = []
            if warranty:
                lines.append(
                    f"设备 **{warranty.get('serial')}**（{warranty.get('model')}）"
                    f"保修状态：**{warranty.get('warranty')}**，"
                    f"到期日 {warranty.get('warranty_end')}。"
                )
            if parts:
                lines.append(
                    f"备件 **{parts.get('part_no')} {parts.get('name')}**："
                    f"{parts.get('region')}仓库存 **{parts.get('stock')}** 件，"
                    f"单价 {parts.get('price_cny')} 元。"
                )
            if results:
                lines.append("\n**依据**")
                for item in results[:4]:
                    page = f"p.{item['page']}" if item.get("page") else ""
                    lines.append(
                        f"- {item.get('title', '')} {item.get('section', '')} "
                        f"{page}（{item.get('doc_id', '')}）"
                    )
            return "\n".join(lines) if lines else "资料不足，建议转人工确认。"

        lines = ["### 初步判断"]
        latest = telemetry.get("latest", {}) if telemetry else {}
        if latest:
            lines.append(
                "E-204 是冷却风扇异常触发的**高温保护**。"
                f"当前出水温度 **{latest.get('outlet_temp_c')}°C**，"
                f"风扇转速 **{latest.get('fan_rpm')} rpm**，"
                f"控制指令 **{latest.get('fan_command_pct')}%**，符合“风扇未转”的特征。"
            )
        else:
            lines.append("根据手册，E-204 通常与冷却风扇、F3 保险或接插件有关。")

        lines.append("\n### 建议排查")
        lines.append("1. 按手册 §7.3 执行 **LOTO 断电**，确认设备完全停机。")
        lines.append("2. 检查 **F3 保险**与风扇接插件 XF3；若 F3 熔断，更换 5A 保险并检查线束。")
        lines.append("3. 若风扇卡死，更换风扇组件 **FAN-12038**。")

        if warranty:
            lines.append("\n### 保修")
            lines.append(
                f"设备 {warranty.get('serial')}（{warranty.get('model')}）"
                f"状态：**{warranty.get('warranty')}**，到期日 {warranty.get('warranty_end')}。"
            )

        if parts:
            lines.append("\n### 备件")
            lines.append(
                f"{parts.get('part_no')} {parts.get('name')}："
                f"{parts.get('region')}仓库存 **{parts.get('stock')}** 件，"
                f"单价 {parts.get('price_cny')} 元。"
            )

        if results:
            lines.append("\n### 依据")
            for item in results[:4]:
                page = f"p.{item['page']}" if item.get("page") else ""
                lines.append(
                    f"- {item.get('title', '')} {item.get('section', '')} "
                    f"{page}（{item.get('doc_id', '')}）"
                )

        if draft:
            lines.append(
                f"\n> 已生成工单草稿 **{draft.get('draft_id')}**，"
                "请工程师在左侧「工单草稿」确认后创建。"
            )
        return "\n".join(lines)

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        query = self._text(messages)
        tool_messages = self._tool_messages(messages)
        done = {message.name for message in tool_messages}
        serial = _extract_serial(query)
        lower = query.lower()
        is_e204 = any(key in query for key in ["E-204", "e-204", "高温", "风扇", "停机"])

        # First turn: pick the tools that the scenario needs.
        if not tool_messages:
            calls: list[dict[str, Any]] = []
            if "保修" in query or is_e204:
                call = self._call("check_warranty", {"serial": serial})
                if call:
                    calls.append(call)
            if "库存" in query or "备件" in query or is_e204:
                call = self._call(
                    "check_parts", {"part_no": "FAN-12038", "region": "上海"}
                )
                if call:
                    calls.append(call)
            if is_e204 or "手册" in query or "步骤" in query or "故障" in query:
                call = self._call(
                    "search_knowledge",
                    {"query": query[:300]},
                )
                if call:
                    calls.append(call)
            if is_e204 or "工况" in query or "温度" in query:
                call = self._call("get_telemetry", {"asset_id": serial, "minutes": 30})
                if call:
                    calls.append(call)

            if calls:
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(content="", tool_calls=calls)
                        )
                    ]
                )

            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content=(
                                "我可以帮你查设备工况、保修、备件和维修手册。"
                                "请提供设备序列号，或直接描述故障现象。"
                            )
                        )
                    )
                ]
            )

        # After diagnosis tools, create one draft (only once).
        draft: dict[str, Any] = {}
        if "draft_work_order" not in done and is_e204:
            call = self._call(
                "draft_work_order",
                {
                    "asset_id": serial,
                    "title": "E-204 高温保护 / 冷却风扇异常",
                    "description": (
                        "出水温度 96°C，风扇转速 0 rpm，控制指令 100%。"
                        "按手册 §7.3 检查 F3 保险与风扇接插件 XF3；"
                        "必要时更换风扇组件 FAN-12038。"
                    ),
                    "priority": "P2",
                    "parts": ["FAN-12038", "FUSE-5A"],
                    "scheduled_at": "2026-10-31 10:00",
                },
            )
            if call:
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(content="", tool_calls=[call])
                        )
                    ]
                )

        draft = self._latest(messages, "draft_work_order")
        return ChatResult(
            generations=[
                ChatGeneration(
                    message=AIMessage(
                        content=self._final_answer(messages, draft, is_e204)
                    )
                )
            ]
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
