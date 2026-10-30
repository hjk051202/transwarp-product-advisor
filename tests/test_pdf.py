from __future__ import annotations

from fieldops.data import load_pdf_manuals
from fieldops.ingest import corpus_stats


def test_pdf_manuals_are_indexable() -> None:
    pdfs = load_pdf_manuals()
    assert len(pdfs) >= 3
    ids = {item["id"] for item in pdfs}
    assert "pdf-x100-manual-7-3" in ids
    manual = next(item for item in pdfs if item["id"] == "pdf-x100-manual-7-3")
    assert manual["metadata"]["page"] == 84
    assert "F3" in manual["text"]


def test_corpus_stats() -> None:
    stats = corpus_stats()
    assert stats["markdown_docs"] >= 6
    assert stats["pdf_docs"] >= 3
    assert stats["total_docs"] == stats["markdown_docs"] + stats["pdf_docs"]
