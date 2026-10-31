from __future__ import annotations

import pytest

from fieldops.service import approve, chat


@pytest.mark.asyncio
async def test_chat_returns_citations_and_lead() -> None:
    response = await chat(
        "我们是城商行，做报表和风控，ArgoDB 和 TDH 怎么选？",
        company="某城商行",
        industry="金融",
        contact="demo@example.com",
    )
    assert response.answer
    assert response.citations
    assert any(citation.doc_id == "tw-argodb" for citation in response.citations)
    assert response.lead is not None
    assert response.lead.lead_id.startswith("LEAD-")


@pytest.mark.asyncio
async def test_approve_creates_crm_lead() -> None:
    response = await chat(
        "想申请 ArgoDB 试用，怎么联系？",
        company="某企业",
        industry="金融",
        contact="demo@example.com",
    )
    assert response.lead is not None
    approved = await approve(response.lead.lead_id)
    assert approved.crm_lead_id.startswith("CRM-")
    assert approved.status in {"approved", "approved_local_fallback"}
