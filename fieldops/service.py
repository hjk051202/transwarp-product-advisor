"""Application service: product-advisor chat and lead approval."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from fieldops import audit
from fieldops.agent import get_agent
from fieldops.data import list_products, search_cases
from fieldops.db import create_lead, get_lead, list_leads
from fieldops.integrations import build_crm_adapter
from fieldops.rag import search
from fieldops.schemas import (
    ApproveResponse,
    ChatResponse,
    Citation,
    LeadDraft,
    ToolTrace,
)

BUY_TERMS = ["选型", "怎么选", "试用", "报价", "方案", "联系", "咨询", "采购", "落地", "POC"]


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


def _extract(
    result: dict[str, Any],
) -> tuple[str, list[Citation], list[ToolTrace], LeadDraft | None]:
    messages = result.get("messages", [])
    citations: list[Citation] = []
    traces: list[ToolTrace] = []
    lead: LeadDraft | None = None
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
        elif message.name == "draft_lead" and payload.get("lead_id"):
            lead = LeadDraft(**payload)

    final = ""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            final = _content_text(message.content)
            break
    return final, citations, traces, lead


def _fallback_advice(
    message: str, company: str, industry: str, contact: str
) -> ChatResponse:
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

    lines = ["### 需求判断", "根据你的描述，先从产品定位和适用场景做初步判断。"]
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

    lead = None
    if any(term in message for term in BUY_TERMS):
        lead_id = f"LEAD-{datetime.now():%Y%m%d%H%M%S}-fallback"
        payload = create_lead(
            lead_id=lead_id,
            company=company or "某企业客户",
            industry=industry or "待补充",
            contact=contact or "待补充",
            need=message[:300],
            products=[product["key"] for product in products[:2]],
        )
        lead = LeadDraft(**payload)
        lines.append("\n> 已生成线索草稿，请在「线索草稿」确认后写入 CRM。")

    return ChatResponse(
        answer="\n".join(lines),
        citations=citations,
        tool_trace=[ToolTrace(name="fallback_advice", result={"docs": len(docs)})],
        lead=lead,
        mode="offline-fallback",
    )


async def chat(
    message: str,
    company: str | None = None,
    industry: str | None = None,
    contact: str | None = None,
) -> ChatResponse:
    company = company or "某企业客户"
    industry = industry or ""
    contact = contact or "待补充"
    prompt = (
        f"{message}\n\n"
        f"客户公司：{company}\n"
        f"行业：{industry or '未提供'}\n"
        f"联系方式：{contact}"
    )
    error = ""
    try:
        agent, mode = await get_agent()
        result = await agent.ainvoke({"messages": [HumanMessage(content=prompt)]})
        answer, citations, traces, lead = _extract(result)
        if not answer:
            response = _fallback_advice(message, company, industry, contact)
        else:
            response = ChatResponse(
                answer=answer,
                citations=citations,
                tool_trace=traces,
                lead=lead,
                mode=mode,
            )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        response = _fallback_advice(message, company, industry, contact)

    audit.log(
        "chat.request",
        resource=f"company:{company}",
        detail={
            "message": message[:160],
            "industry": industry,
            "mode": response.mode,
            "citations": len(response.citations),
            "tools": [trace.name for trace in response.tool_trace],
            "lead_id": response.lead.lead_id if response.lead else None,
            "error": error,
        },
    )
    return response


async def approve(lead_id: str) -> ApproveResponse:
    lead = get_lead(lead_id)
    if not lead:
        audit.log("lead.approve", resource=lead_id, detail={"status": "not_found"})
        raise ValueError(f"lead {lead_id} not found")
    if lead.get("status") == "approved" and lead.get("crm_lead_id"):
        audit.log(
            "lead.approve",
            resource=lead_id,
            detail={"status": "already_approved", "crm_lead_id": lead["crm_lead_id"]},
        )
        return ApproveResponse(
            lead_id=lead_id,
            crm_lead_id=lead["crm_lead_id"],
            status="approved",
        )

    result = await build_crm_adapter().create_lead(lead)
    crm_lead_id = result.get("crm_lead_id")
    if not crm_lead_id:
        audit.log("lead.approve", resource=lead_id, detail={"status": "failed"})
        raise ValueError("CRM did not return a crm_lead_id")
    audit.log(
        "lead.approve",
        resource=lead_id,
        detail={"status": result.get("status"), "crm_lead_id": crm_lead_id},
    )
    return ApproveResponse(
        lead_id=lead_id,
        crm_lead_id=crm_lead_id,
        status=str(result.get("status", "approved")),
    )


def leads() -> list[dict[str, Any]]:
    return list_leads()
