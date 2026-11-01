"""Optional cross-encoder reranking with graceful fallback.

The default path is disabled so no API key is required for local demos.
Set RERANK_ENABLED=1 and RERANK_API_KEY (or OPENAI_API_KEY) to use a
/v1/rerank endpoint such as SiliconFlow's bge-reranker-v2-m3.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from langchain_core.documents import Document

RERANK_ENABLED = os.getenv("RERANK_ENABLED", "0").strip() == "1"
RERANK_MODEL = os.getenv("RERANK_MODEL", "BAAI/bge-reranker-v2-m3").strip()
RERANK_BASE_URL = os.getenv("RERANK_BASE_URL", "https://api.siliconflow.cn/v1").strip()
RERANK_API_KEY = (
    os.getenv("RERANK_API_KEY")
    or os.getenv("OPENAI_API_KEY")
    or os.getenv("DEEPSEEK_API_KEY")
)
RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES", "20"))
RERANK_TIMEOUT = float(os.getenv("RERANK_TIMEOUT", "20"))


class RerankService:
    def __init__(self) -> None:
        if not RERANK_API_KEY:
            raise RuntimeError(
                "RERANK_ENABLED=1 but no RERANK_API_KEY/OPENAI_API_KEY/DEEPSEEK_API_KEY"
            )
        self._url = RERANK_BASE_URL.rstrip("/") + "/rerank"
        self._headers = {
            "Authorization": f"Bearer {RERANK_API_KEY}",
            "Content-Type": "application/json",
        }

    def rerank(
        self, query: str, docs: list[Document], top_n: int = 5
    ) -> list[tuple[Document, float]]:
        if not docs:
            return []

        payload: dict[str, Any] = {
            "model": RERANK_MODEL,
            "query": query,
            "documents": [doc.page_content for doc in docs],
            "top_n": min(top_n, len(docs)),
        }
        try:
            with httpx.Client(timeout=RERANK_TIMEOUT) as client:
                response = client.post(self._url, json=payload, headers=self._headers)
                response.raise_for_status()
                body = response.json()
        except Exception:
            return [(doc, 0.0) for doc in docs[:top_n]]

        results = body.get("results") or []
        ranked: list[tuple[Document, float]] = []
        for item in results:
            index = item.get("index")
            if not isinstance(index, int) or not (0 <= index < len(docs)):
                continue
            ranked.append((docs[index], float(item.get("relevance_score", 0.0))))
        if not ranked:
            return [(doc, 0.0) for doc in docs[:top_n]]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:top_n]


def is_enabled() -> bool:
    return RERANK_ENABLED
