"""Offline-friendly RAG over public Transwarp product materials."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from fieldops.config import CHROMA_DIR
from fieldops.data import all_knowledge

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9\-_.]*|[\u4e00-\u9fff]")


def tokenize(text: str) -> list[str]:
    lowered = text.lower()
    tokens = _TOKEN_RE.findall(lowered)
    han = [t for t in tokens if len(t) == 1 and "\u4e00" <= t <= "\u9fff"]
    bigrams = [han[i] + han[i + 1] for i in range(len(han) - 1)]
    return tokens + bigrams


class HashingEmbeddings(Embeddings):
    """Deterministic offline embedding for demos and tests."""

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
    product: str
    section: str
    page: int | None
    version: str | None
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "product": self.product,
            "section": self.section,
            "page": self.page,
            "version": self.version,
            "snippet": self.text[:700],
            "score": round(self.score, 4),
        }


def _manifest() -> str:
    ids = sorted(item["id"] for item in all_knowledge())
    return hashlib.sha256(json.dumps(ids, ensure_ascii=False).encode("utf-8")).hexdigest()


def _make_chunks() -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=450,
        chunk_overlap=70,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", "；", " "],
    )
    chunks: list[Document] = []
    for document in all_knowledge():
        metadata = {
            key: value
            for key, value in document["metadata"].items()
            if isinstance(value, (str, int, float, bool))
        }
        for index, chunk in enumerate(splitter.split_text(document["text"])):
            chunks.append(
                Document(
                    page_content=chunk,
                    metadata={**metadata, "chunk_index": index, "doc_id": document["id"]},
                )
            )
    return chunks


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    manifest_path = CHROMA_DIR / "manifest.txt"
    current = _manifest()
    if not manifest_path.exists() or manifest_path.read_text(encoding="utf-8") != current:
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    store = Chroma(
        collection_name="transwarp_knowledge",
        embedding_function=HashingEmbeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
    if store._collection.count() == 0:
        chunks = _make_chunks()
        ids = [f"{c.metadata['doc_id']}-{c.metadata['chunk_index']}" for c in chunks]
        store.add_documents(chunks, ids=ids)
        manifest_path.write_text(current, encoding="utf-8")
    return store


def _keyword_score(query: str, text: str) -> float:
    q = set(tokenize(query))
    d = set(tokenize(text))
    if not q or not d:
        return 0.0
    coverage = len(q & d) / len(q)
    for term in ["argodb", "tdh", "tdc", "sophon", "stellardb", "kundb"]:
        if term in query.lower() and term in text.lower():
            coverage += 0.2
    return min(coverage, 1.0)


def search(query: str, k: int = 4) -> list[RetrievedDoc]:
    raw = get_vectorstore().similarity_search_with_score(query, k=max(k * 3, 12))
    results: list[RetrievedDoc] = []
    for document, distance in raw:
        vector_score = max(0.0, 1.0 - float(distance) / 2.0)
        metadata = document.metadata
        product = str(metadata.get("product", ""))
        product_bonus = 0.25 if product.lower() in query.lower() else 0.0
        combined = (
            0.6 * vector_score
            + 0.25 * _keyword_score(query, document.page_content)
            + product_bonus
        )
        results.append(
            RetrievedDoc(
                doc_id=str(metadata.get("doc_id", "")),
                title=str(metadata.get("title", "")),
                product=str(metadata.get("product", "")),
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
    return json.dumps(
        {"query": query, "results": [doc.to_dict() for doc in search(query, k=k)]},
        ensure_ascii=False,
    )
