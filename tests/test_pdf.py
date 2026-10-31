from __future__ import annotations

from fieldops.data import load_pdf_knowledge
from fieldops.ingest import corpus_stats


def test_pdf_knowledge_is_parsed() -> None:
    pdfs = load_pdf_knowledge()
    assert len(pdfs) >= 2
    ids = {item["id"] for item in pdfs}
    assert "pdf-argodb" in ids
    manual = next(item for item in pdfs if item["id"] == "pdf-argodb")
    assert manual["metadata"]["product"] == "ArgoDB"
    assert "HTAP" in manual["text"]


def test_corpus_stats() -> None:
    stats = corpus_stats()
    assert stats["markdown_docs"] >= 9
    assert stats["pdf_docs"] >= 2
    assert stats["total_docs"] == stats["markdown_docs"] + stats["pdf_docs"]
