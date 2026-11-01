"""Hybrid retrieval: vector recall + BM25 exact-term recall, fused with RRF.

The BM25 implementation is intentionally small and dependency-free so the
offline demo can still run without downloading a tokenizer/model.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

RRF_K = 60
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-_.]*|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    """Tokenize English/number terms plus Chinese characters and bigrams."""

    lowered = text.lower()
    tokens = _TOKEN_RE.findall(lowered)
    han = [t for t in tokens if len(t) == 1 and "\u4e00" <= t <= "\u9fff"]
    bigrams = [han[i] + han[i + 1] for i in range(len(han) - 1)]
    return tokens + bigrams


class BM25:
    """Minimal BM25Okapi implementation for the local corpus."""

    def __init__(
        self, corpus: list[list[str]], *, k1: float = 1.5, b: float = 0.75
    ) -> None:
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.n = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.n if self.n else 0.0
        self.freqs: list[dict[str, int]] = []
        self.doc_freqs: dict[str, int] = {}
        for doc in corpus:
            freq: dict[str, int] = {}
            for token in doc:
                freq[token] = freq.get(token, 0) + 1
            self.freqs.append(freq)
            for token in freq:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

    def idf(self, token: str) -> float:
        df = self.doc_freqs.get(token, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def get_scores(self, query: list[str]) -> list[float]:
        scores = [0.0] * self.n
        for i, freq in enumerate(self.freqs):
            dl = len(self.corpus[i])
            for token in query:
                tf = freq.get(token, 0)
                if not tf:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
                scores[i] += self.idf(token) * tf * (self.k1 + 1) / denom
        return scores


def doc_key(doc: Document) -> str:
    metadata = doc.metadata or {}
    return "::".join(
        [
            str(metadata.get("doc_id", "")),
            str(metadata.get("chunk_index", "")),
            doc.page_content[:80],
        ]
    )


@dataclass
class HybridHit:
    doc: Document
    score: float
    vector_score: float = 0.0
    rerank_score: float | None = None


class HybridRetriever:
    """Run vector and BM25 retrieval, then fuse ranks with RRF.

    RRF only uses ranks, so the 0..1 cosine score and unbounded BM25 score
    do not need to be normalized onto the same scale.
    """

    def __init__(self, vector_store: Chroma, *, rrf_k: int = RRF_K) -> None:
        self.vector_store = vector_store
        self.rrf_k = rrf_k
        self._docs: list[Document] = []
        self._bm25: BM25 | None = None
        self._build_bm25()

    def _build_bm25(self) -> None:
        try:
            raw = self.vector_store.get(include=["documents", "metadatas"])
        except Exception:
            return

        texts: list[str] = raw.get("documents") or []
        metadatas: list[dict[str, Any]] = raw.get("metadatas") or [
            {} for _ in texts
        ]
        self._docs = [
            Document(page_content=text, metadata=meta or {})
            for text, meta in zip(texts, metadatas)
        ]
        if not self._docs:
            return
        self._bm25 = BM25([tokenize(doc.page_content) for doc in self._docs])

    @property
    def size(self) -> int:
        return len(self._docs)

    def search_vector(self, query: str, k: int) -> list[tuple[Document, float]]:
        raw = self.vector_store.similarity_search_with_score(query, k=k)
        results = []
        for doc, distance in raw:
            score = max(0.0, 1.0 - float(distance) / 2.0)
            results.append((doc, score))
        return results

    def search_bm25(self, query: str, k: int) -> list[Document]:
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self._docs[i] for i in ranked[:k] if scores[i] > 0]

    def search(self, query: str, k: int = 4) -> tuple[list[HybridHit], float]:
        candidates = max(k * 3, k + 5, 12)
        vector_pairs = self.search_vector(query, candidates)
        best_vector_score = vector_pairs[0][1] if vector_pairs else 0.0
        bm25_docs = self.search_bm25(query, candidates)

        ranked_lists = [
            [doc for doc, _ in vector_pairs],
            bm25_docs,
        ]
        fused: dict[str, float] = {}
        doc_by_key: dict[str, Document] = {}
        vector_scores: dict[str, float] = {}

        for docs in ranked_lists:
            for rank, doc in enumerate(docs):
                key = doc_key(doc)
                doc_by_key.setdefault(key, doc)
                fused[key] = fused.get(key, 0.0) + 1.0 / (self.rrf_k + rank + 1)

        # Product names are high-signal terms in this domain. A small bonus
        # keeps product-specific chunks ahead of generic FAQ/guide chunks.
        query_lower = query.lower()
        product_names = ["argodb", "tdh", "tdc", "sophon", "stellardb", "kundb"]
        product_count = sum(name in query_lower for name in product_names)
        guide_query = "组合" in query or "定位" in query or product_count >= 3
        for key, doc in doc_by_key.items():
            metadata = doc.metadata or {}
            product = str(metadata.get("product", "")).lower()
            if product and product in query_lower:
                fused[key] = fused.get(key, 0.0) + 0.006
            if guide_query and str(metadata.get("doc_id", "")) == "tw-selection-guide":
                fused[key] = fused.get(key, 0.0) + 0.008

        for doc, score in vector_pairs:
            vector_scores[doc_key(doc)] = score

        ordered = sorted(fused.items(), key=lambda item: item[1], reverse=True)[:k]
        return [
            HybridHit(
                doc=doc_by_key[key],
                score=score,
                vector_score=vector_scores.get(key, 0.0),
            )
            for key, score in ordered
        ], best_vector_score
