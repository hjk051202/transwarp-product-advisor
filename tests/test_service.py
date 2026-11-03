from __future__ import annotations

import pytest

from fieldops.service import chat, get_history, list_history


@pytest.mark.asyncio
async def test_bank_reporting_answers_directly() -> None:
    response = await chat(
        "我是一个银行的，搞报表，数据量GB，无国产要求",
        session_id="SESS-bank",
        company="某银行",
        industry="金融",
    )
    assert "先确认需求" not in response.answer
    assert "ArgoDB" in response.answer
    assert any(trace.name == "list_products" for trace in response.tool_trace)
    assert all(citation.doc_id != "tw-tdc" for citation in response.citations)


@pytest.mark.asyncio
async def test_chat_returns_citations_and_history() -> None:
    response = await chat(
        "我们是城商行，做报表和风控，ArgoDB 和 TDH 怎么选？",
        session_id="SESS-pytest",
        company="某城商行",
        industry="金融",
    )
    assert response.answer
    assert response.citations
    assert any(citation.doc_id == "tw-argodb" for citation in response.citations)
    assert response.conversation_id.startswith("CONV-")

    items = await list_history(limit=10)
    assert any(item["conversation_id"] == response.conversation_id for item in items)

    detail = await get_history(response.conversation_id)
    assert detail is not None
    assert detail["session_id"] == "SESS-pytest"
