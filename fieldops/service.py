"""Application service: chat orchestration and work-order approval."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from fieldops.agent import get_agent
from fieldops.data import get_device, get_part, get_telemetry as load_telemetry
from fieldops.db import create_draft, get_draft, list_drafts
from fieldops.mcp_client import create_work_order_via_mcp
from fieldops.rag import search
from fieldops.schemas import (
    ApproveResponse,
    ChatResponse,
    Citation,
    ToolTrace,
    WorkOrderDraft,
)


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return str(content)


def _payload(message: ToolMessage) -> dict[str, Any]:
    content = _content_text(message.content)
    try:
        value = json.loads(content)
        return value if isinstance(value, dict) else {"result": value}
    except json.JSONDecodeError:
        return {"result": content}


def _extract(result: dict[str, Any]) -> tuple[str, list[Citation], list[ToolTrace], WorkOrderDraft | None]:
    messages = result.get("messages", [])
    citations: list[Citation] = []
    traces: list[ToolTrace] = []
    draft: WorkOrderDraft | None = None
    call_args: dict[str, dict[str, Any]] = {}

    for message in messages:
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                call_args[call.get("id", "")] = call.get("args", {})

    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        payload = _payload(message)
        traces.append(
            ToolTrace(
                name=message.name or "unknown",
                args=call_args.get(message.tool_call_id or "", {}),
                result=payload,
            )
        )
        if message.name == "search_knowledge":
            for item in payload.get("results", []):
                citations.append(
                    Citation(
                        doc_id=str(item.get("doc_id", "")),
                        title=str(item.get("title", "")),
                        section=str(item.get("section", "")),
                        page=item.get("page"),
                        version=item.get("version"),
                        snippet=str(item.get("snippet", ""))[:700],
                    )
                )
        elif message.name == "draft_work_order" and payload.get("draft_id"):
            draft = WorkOrderDraft(**payload)

    final = ""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            final = _content_text(message.content)
            break

    return final, citations, traces, draft


def _fallback_diagnosis(message: str, serial: str) -> ChatResponse:
    """Deterministic path used if the agent/model/MCP is unavailable."""

    device = get_device(serial)
    telemetry = load_telemetry(serial, 30) or {}
    latest = telemetry.get("latest", {})
    docs = search("X100 E-204 高温 风扇 转速 0 手册", k=4)
    parts = get_part("FAN-12038") or {}
    citations = [
        Citation(
            doc_id=doc.doc_id,
            title=doc.title,
            section=doc.section,
            page=doc.page,
            version=doc.version,
            snippet=doc.text[:700],
        )
        for doc in docs
    ]

    draft_payload = create_draft(
        draft_id=f"DRF-{datetime.now():%Y%m%d%H%M%S}-fallback",
        asset_id=serial,
        title="E-204 高温保护 / 冷却风扇异常",
        description=(
            "出水温度 96°C，风扇转速 0 rpm，控制指令 100%。"
            "按手册 §7.3 检查 F3 保险与风扇接插件 XF3；必要时更换 FAN-12038。"
        ),
        priority="P2",
        parts=["FAN-12038", "FUSE-5A"],
        safety=[
            "执行 LOTO 断电并确认零能量",
            "禁止带电插拔风扇接插件",
            "更换风扇前确认叶轮完全停止",
        ],
        scheduled_at="2026-10-31 10:00",
    )

    answer = (
        "### 初步判断\n"
        f"E-204 是冷却风扇异常触发的**高温保护**。当前出水温度 "
        f"**{latest.get('outlet_temp_c')}°C**，风扇转速 **{latest.get('fan_rpm')} rpm**，"
        f"控制指令 **{latest.get('fan_command_pct')}%**。\n\n"
        "### 建议排查\n"
        "1. 按手册 §7.3 执行 **LOTO 断电**，确认设备完全停机。\n"
        "2. 检查 **F3 保险**与风扇接插件 XF3；若熔断，更换 5A 保险并检查线束。\n"
        "3. 若风扇卡死，更换风扇组件 **FAN-12038**。\n\n"
        f"### 保修\n{device.get('warranty') if device else '未知'}，"
        f"到期日 {device.get('warranty_end') if device else '未知'}。\n\n"
        f"### 备件\nFAN-12038 上海仓 {parts.get('stock', {}).get('上海', 0)} 件。\n\n"
        "> 已生成工单草稿，请在「工单草稿」确认。"
    )

    return ChatResponse(
        answer=answer,
        citations=citations,
        tool_trace=[ToolTrace(name="fallback_diagnosis", result={"serial": serial})],
        draft=WorkOrderDraft(**draft_payload),
        mode="offline-fallback",
    )


async def chat(message: str, serial: str | None = None) -> ChatResponse:
    serial = (serial or "8F2-1042").strip().upper()
    prompt = f"{message}\n\n设备序列号：{serial}"
    try:
        agent, mode = await get_agent()
        result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        answer, citations, traces, draft = _extract(result)
        if not answer:
            return _fallback_diagnosis(message, serial)
        return ChatResponse(
            answer=answer,
            citations=citations,
            tool_trace=traces,
            draft=draft,
            mode=mode,
        )
    except Exception:
        return _fallback_diagnosis(message, serial)


async def approve(draft_id: str) -> ApproveResponse:
    draft = get_draft(draft_id)
    if not draft:
        raise ValueError(f"draft {draft_id} not found")
    if draft.get("status") == "approved" and draft.get("work_order_id"):
        return ApproveResponse(
            draft_id=draft_id,
            work_order_id=draft["work_order_id"],
            status="approved",
        )

    result = await create_work_order_via_mcp(draft)
    work_order_id = result.get("work_order_id")
    if not work_order_id:
        raise ValueError("MCP did not return a work_order_id")
    return ApproveResponse(
        draft_id=draft_id,
        work_order_id=work_order_id,
        status=str(result.get("status", "approved")),
    )


def drafts() -> list[dict[str, Any]]:
    return list_drafts()
