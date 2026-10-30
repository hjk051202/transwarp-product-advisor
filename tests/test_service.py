from __future__ import annotations

import pytest

from fieldops.service import approve, chat


@pytest.mark.asyncio
async def test_chat_returns_citations_and_draft() -> None:
    response = await chat("X100 报 E-204，出水温度高，客户已停机。", "8F2-1042")
    assert response.answer
    assert response.citations
    assert any(citation.doc_id == "x100-manual-7-3" for citation in response.citations)
    assert response.draft is not None
    assert response.draft.draft_id.startswith("DRF-")


@pytest.mark.asyncio
async def test_approve_creates_work_order() -> None:
    response = await chat("X100 报 E-204，出水温度高。", "8F2-1042")
    assert response.draft is not None
    approved = await approve(response.draft.draft_id)
    assert approved.work_order_id.startswith("WO-")
    assert approved.status in {"approved", "approved_local_fallback"}
