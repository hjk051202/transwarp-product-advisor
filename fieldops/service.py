"""Application service: product-advisor chat and conversation persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from fieldops import audit
from fieldops.agent import get_agent
from fieldops.data import list_products, search_cases
from fieldops.integrations import build_history_adapter
from fieldops.rag import search
from fieldops.schemas import ChatResponse, Citation, ToolTrace


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


def _extract(result: dict[str, Any]) -> tuple[str, list[Citation], list[ToolTrace]]:
    messages = result.get("messages", [])
    citations: list[Citation] = []
    traces: list[ToolTrace] = []
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
                        product=str(item.get("product", "")),
                        section=str(item.get("section", "")),
                        page=item.get("page"),
                        version=item.get("version"),
                        snippet=str(item.get("snippet", ""))[:700],
                    )
                )

    final = ""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            final = _content_text(message.content)
            break

    selected_products: set[str] = set()
    for trace in traces:
        if trace.name != "list_products":
            continue
        payload = trace.result if isinstance(trace.result, dict) else {}
        items = payload.get("result") or payload.get("items") or []
        if isinstance(items, list):
            selected_products = {
                str(item.get("product", ""))
                for item in items
                if isinstance(item, dict) and item.get("product")
            }

    if selected_products:
        citations = [
            citation
            for citation in citations
            if citation.product in selected_products
            or citation.product in {"", "all"}
        ]

    return final, citations, traces


def _fallback_advice(message: str, industry: str) -> tuple[str, list[Citation], list[ToolTrace]]:
    docs = search(message[:200], k=4)
    products = list_products()
    cases = search_cases(industry=industry) if industry else []
    citations = [
        Citation(
            doc_id=doc.doc_id,
            title=doc.title,
            product=doc.product,
            section=doc.section,
            page=doc.page,
            version=doc.version,
            snippet=doc.text[:700],
        )
        for doc in docs
    ]

    lines = ["### 需求判断", "先根据你的描述做初步判断。"]
    if products:
        lines.append("\n### 可选产品")
        for product in products[:6]:
            lines.append(f"- **{product['key']}**：{product['one_liner']}")
    if cases:
        lines.append("\n### 相关案例")
        for case in cases[:2]:
            lines.append(
                f"- {case['industry']} · {case['scenario']}（{'、'.join(case['products'])}）"
            )
    if docs:
        lines.append("\n### 依据")
        for doc in docs[:4]:
            lines.append(f"- {doc.title} {doc.section}（{doc.doc_id}）")
    return "\n".join(lines), citations, [ToolTrace(name="fallback_advice")]


async def chat(
    message: str,
    session_id: str | None = None,
    company: str | None = None,
    industry: str | None = None,
) -> ChatResponse:
    session_id = session_id or f"SESS-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid4().hex[:4]}"
    prompt = (
        f"{message}\n\n"
        f"客户公司：{company or '未提供'}\n"
        f"行业：{industry or '未提供'}"
    )
    error = ""
    try:
        agent, mode = await get_agent()
        result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        answer, citations, traces = _extract(result)
        if not answer:
            answer, citations, traces = _fallback_advice(message, industry or "")
            mode = "offline-fallback"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        answer, citations, traces = _fallback_advice(message, industry or "")
        mode = "offline-fallback"

    conversation_id = ""
    try:
        saved = await build_history_adapter().save_conversation(
            {
                "session_id": session_id,
                "user_message": message,
                "assistant_message": answer,
                "citations": [item.model_dump() for item in citations],
                "tool_trace": [item.model_dump() for item in traces],
                "mode": mode,
            }
        )
        conversation_id = str(saved.get("conversation_id", ""))
    except Exception as exc:
        error = f"{error}; history_save: {type(exc).__name__}: {exc}".strip("; ")

    audit.log(
        "chat.request",
        resource=f"session:{session_id}",
        detail={
            "message": message[:160],
            "industry": industry or "",
            "mode": mode,
            "citations": len(citations),
            "tools": [trace.name for trace in traces],
            "conversation_id": conversation_id,
            "error": error,
        },
    )
    return ChatResponse(
        answer=answer,
        citations=citations,
        tool_trace=traces,
        conversation_id=conversation_id,
        mode=mode,
    )


async def list_history(limit: int = 20) -> list[dict[str, Any]]:
    return await build_history_adapter().list_conversations(limit=limit)


async def get_history(conversation_id: str) -> dict[str, Any] | None:
    return await build_history_adapter().get_conversation(conversation_id)
