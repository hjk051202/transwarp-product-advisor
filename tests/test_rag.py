from __future__ import annotations

from fieldops.rag import search


def test_search_finds_e204_manual() -> None:
    docs = search("X100 E-204 高温 风扇 转速 0", k=4)
    assert docs
    assert any(doc.doc_id == "x100-manual-7-3" for doc in docs)
    assert all(doc.page for doc in docs if doc.doc_id == "x100-manual-7-3")


def test_search_has_citation_metadata() -> None:
    docs = search("F3 保险 规格", k=3)
    assert docs
    for doc in docs:
        assert doc.doc_id
        assert doc.title
        assert doc.section
