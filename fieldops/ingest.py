"""Batch ingestion helpers for the local demo corpus.

The normal app builds the index lazily. Use this module when you add/remove
Markdown or PDF files and want a deterministic rebuild.
"""

from __future__ import annotations

import shutil
from typing import Any

from fieldops.config import CHROMA_DIR
from fieldops.data import load_knowledge, load_pdf_knowledge
from fieldops.rag import get_retriever, get_vectorstore


def corpus_stats() -> dict[str, Any]:
    markdown = load_knowledge()
    pdfs = load_pdf_knowledge()
    return {
        "markdown_docs": len(markdown),
        "pdf_docs": len(pdfs),
        "total_docs": len(markdown) + len(pdfs),
        "ids": sorted([item["id"] for item in markdown + pdfs]),
    }


def rebuild_index() -> dict[str, Any]:
    get_retriever.cache_clear()
    get_vectorstore.cache_clear()
    shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    get_vectorstore()
    return corpus_stats()
