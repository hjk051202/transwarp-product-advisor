"""Offline-friendly RAG over the sample service manuals.

The demo deliberately avoids a hosted embedding API so it can run without any
API key. The hashing embedder is deterministic and good enough for a small,
keyword-rich corpus; swap it for BGE-M3 / OpenAI embeddings in production.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from fieldops.config import CHROMA_DIR
from fieldops.data import load_manuals

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-_.]*|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    """Latin words + Chinese characters + Chinese bigrams."""

    lowered = text.lower()
    tokens = _TOKEN_RE.findall(lowered)
    han = [t for t in tokens if len(t) == 1 and "\u4e00" <= t <= "\u9fff"]
    bigrams = [han[i] + han[i + 1] for i in range(len(han) - 1)]
    return tokens + bigrams


class HashingEmbeddings(Embeddings):
    """A small deterministic embedding model for offline demos/tests."""

    def __init__(self, dimension: int = 512) -> None:
        self.dimension = dimension

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in tokenize(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimension
            sign = 1.0 if (value >> 63) & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


@dataclass
class RetrievedDoc:
    doc_id: str
    title: str
    section: str
    page: int | None
    version: str | None
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "section": self.section,
            "page": self.page,
            "version": self.version,
            "snippet": self.text[:700],
            "score": round(self.score, 4),
        }


def _make_chunks() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=70,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", "；", " "],
    )
    chunks: list[Document] = []
    for manual in load_manuals():
        metadata = {
            key: value
            for key, value in manual["metadata"].items()
            if isinstance(value, (str, int, float, bool))
        }
        for index, chunk in enumerate(splitter.split_text(manual["text"])):
            chunks.append(
                Document(
                    page_content=chunk,
                    metadata={
                        **metadata,
                        "chunk_index": index,
                        "doc_id": manual["id"],
                    },
                )
            )
    return chunks


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    store = Chroma(
        collection_name="fieldops_manuals",
        embedding_function=HashingEmbeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
    if store._collection.count() == 0:  # small corpus, build once
        chunks = _make_chunks()
        ids = [f"{c.metadata['doc_id']}-{c.metadata['chunk_index']}" for c in chunks]
        store.add_documents(chunks, ids=ids)
    return store


def _keyword_score(query: str, text: str) -> float:
    q = set(tokenize(query))
    d = set(tokenize(text))
    if not q or not d:
        return 0.0
    coverage = len(q & d) / len(q)
    if "e-204" in query.lower() and "e-204" in text.lower():
        coverage += 0.35
    return min(coverage, 1.0)


def search(query: str, k: int = 4, model: str = "X100") -> list[RetrievedDoc]:
    store = get_vectorstore()
    raw = store.similarity_search_with_score(
        query,
        k=max(k * 3, 10),
        filter={"model": model},
    )
    results: list[RetrievedDoc] = []
    for document, distance in raw:
        # cosine distance in [0, 2] -> similarity in [0, 1]
        vector_score = max(0.0, 1.0 - float(distance) / 2.0)
        combined = 0.7 * vector_score + 0.3 * _keyword_score(query, document.page_content)
        metadata = document.metadata
        results.append(
            RetrievedDoc(
                doc_id=str(metadata.get("doc_id", "")),
                title=str(metadata.get("title", "")),
                section=str(metadata.get("section", "")),
                page=metadata.get("page") if isinstance(metadata.get("page"), int) else None,
                version=str(metadata.get("version")) if metadata.get("version") else None,
                text=document.page_content,
                score=combined,
            )
        )
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:k]


def search_json(query: str, k: int = 4) -> str:
    results = search(query, k=k)
    return json.dumps(
        {
            "query": query,
            "results": [doc.to_dict() for doc in results],
        },
        ensure_ascii=False,
    )
