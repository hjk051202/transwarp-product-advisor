"""Offline-friendly RAG over public Transwarp product materials.

The retrieval path is intentionally explicit:
  Markdown/PDF -> chunks -> HashingEmbeddings -> Chroma
  query -> vector recall + BM25 recall -> RRF fusion -> optional rerank
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from fieldops.config import (
    CHROMA_DIR,
    EMBEDDING_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    EMBEDDING_PROVIDER,
    OPENAI_API_KEY,
)
from fieldops.data import all_knowledge
from fieldops.reranker import RERANK_CANDIDATES, RerankService, is_enabled as rerank_enabled
from fieldops.retrieval import HybridRetriever, doc_key, tokenize

SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.30"))
DOMAIN_TERMS = [
    "星环",
    "产品",
    "选型",
    "数据库",
    "数据仓库",
    "数据湖",
    "报表",
    "分析",
    "实时",
    "交易",
    "oltp",
    "htap",
    "图",
    "知识图谱",
    "ai",
    "机器学习",
    "国产化",
    "信创",
    "麒麟",
    "统信",
    "鲲鹏",
    "海光",
    "兼容",
    "案例",
    "报价",
    "poc",
    "试用",
    "argodb",
    "tdh",
    "tdc",
    "sophon",
    "stellardb",
    "kundb",
]


def is_domain_query(query: str) -> bool:
    lowered = query.lower()
    return any(term in lowered for term in DOMAIN_TERMS)


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


def _embedding_key() -> str:
    if EMBEDDING_PROVIDER == "openai":
        return EMBEDDING_API_KEY or OPENAI_API_KEY
    return EMBEDDING_API_KEY


def _embedding_base_url() -> str:
    if EMBEDDING_BASE_URL:
        return EMBEDDING_BASE_URL
    if EMBEDDING_PROVIDER == "openai":
        return "https://api.openai.com/v1"
    return "https://api.siliconflow.cn/v1"


def _embedding_model() -> str:
    if EMBEDDING_MODEL:
        return EMBEDDING_MODEL
    if EMBEDDING_PROVIDER == "openai":
        return "text-embedding-3-small"
    return "BAAI/bge-m3"


def external_embeddings_enabled() -> bool:
    if EMBEDDING_PROVIDER == "hashing":
        return False
    if EMBEDDING_PROVIDER in {"auto", "openai", "openai-compatible"}:
        return bool(_embedding_key())
    return False


def embedding_signature() -> str:
    if external_embeddings_enabled():
        dimensions = EMBEDDING_DIMENSIONS or "native"
        return f"openai:{_embedding_model()}:{_embedding_base_url()}:{dimensions}"
    return "hashing:512"


def build_embeddings() -> Embeddings:
    """Select external OpenAI-compatible embeddings or offline hashing."""

    if (
        EMBEDDING_PROVIDER in {"openai", "openai-compatible"}
        and not external_embeddings_enabled()
    ):
        raise RuntimeError(
            "EMBEDDING_PROVIDER is external but "
            "EMBEDDING_API_KEY/OPENAI_API_KEY is empty"
        )

    if not external_embeddings_enabled():
        return HashingEmbeddings()

    kwargs: dict[str, Any] = {
        "model": _embedding_model(),
        "api_key": _embedding_key(),
        "base_url": _embedding_base_url(),
        # BGE / DashScope compatible endpoints are not tiktoken models.
        "check_embedding_ctx_length": False,
        "chunk_size": 64,
    }
    if EMBEDDING_DIMENSIONS:
        kwargs["dimensions"] = int(EMBEDDING_DIMENSIONS)
    return OpenAIEmbeddings(**kwargs)


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
    vector_score: float = 0.0
    rerank_score: float | None = None

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
            "vector_score": round(self.vector_score, 4),
            "rerank_score": (
                round(self.rerank_score, 4) if self.rerank_score is not None else None
            ),
        }


def _manifest() -> str:
    ids = sorted(item["id"] for item in all_knowledge())
    payload = {"docs": ids, "embedding": embedding_signature()}
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


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
        embedding_function=build_embeddings(),
        persist_directory=str(CHROMA_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
    if store._collection.count() == 0:
        chunks = _make_chunks()
        ids = [f"{c.metadata['doc_id']}-{c.metadata['chunk_index']}" for c in chunks]
        store.add_documents(chunks, ids=ids)
        manifest_path.write_text(current, encoding="utf-8")
    return store


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    return HybridRetriever(get_vectorstore())


@lru_cache(maxsize=1)
def get_reranker() -> RerankService | None:
    if not rerank_enabled():
        return None
    try:
        return RerankService()
    except Exception:
        return None


def _to_retrieved(
    doc: Document,
    *,
    score: float,
    vector_score: float = 0.0,
    rerank_score: float | None = None,
) -> RetrievedDoc:
    metadata = doc.metadata or {}
    return RetrievedDoc(
        doc_id=str(metadata.get("doc_id", "")),
        title=str(metadata.get("title", "")),
        product=str(metadata.get("product", "")),
        section=str(metadata.get("section", "")),
        page=metadata.get("page") if isinstance(metadata.get("page"), int) else None,
        version=str(metadata.get("version")) if metadata.get("version") else None,
        text=doc.page_content,
        score=score,
        vector_score=vector_score,
        rerank_score=rerank_score,
    )


def search_with_meta(query: str, k: int = 4) -> tuple[list[RetrievedDoc], float, bool]:
    """Return (documents, best vector relevance, abstained)."""

    retriever = get_retriever()
    reranker = get_reranker()
    candidates = max(k, RERANK_CANDIDATES) if reranker is not None else max(k * 3, 12)
    hits, best_vector_score = retriever.search(query, k=candidates)

    if reranker is not None and hits:
        reranked = reranker.rerank(query, [hit.doc for hit in hits], top_n=k)
        vector_scores = {doc_key(hit.doc): hit.vector_score for hit in hits}
        docs = [
            _to_retrieved(
                doc,
                score=rerank_score,
                vector_score=vector_scores.get(doc_key(doc), 0.0),
                rerank_score=rerank_score,
            )
            for doc, rerank_score in reranked
        ]
    else:
        docs = [
            _to_retrieved(
                hit.doc,
                score=hit.score,
                vector_score=hit.vector_score,
            )
            for hit in hits[:k]
        ]

    abstained = (not is_domain_query(query)) or best_vector_score < SCORE_THRESHOLD
    return docs, best_vector_score, abstained


def search(query: str, k: int = 4) -> list[RetrievedDoc]:
    docs, _, _ = search_with_meta(query, k=k)
    return docs


def vector_only_search(query: str, k: int = 4) -> list[RetrievedDoc]:
    """Baseline used by the retrieval comparison script."""

    raw = get_vectorstore().similarity_search_with_score(query, k=k)
    return [
        _to_retrieved(
            doc,
            score=max(0.0, 1.0 - float(distance) / 2.0),
            vector_score=max(0.0, 1.0 - float(distance) / 2.0),
        )
        for doc, distance in raw
    ]


def search_json(query: str, k: int = 4) -> str:
    docs, best_vector_score, abstained = search_with_meta(query, k=k)
    return json.dumps(
        {
            "query": query,
            "abstained": abstained,
            "best_vector_score": round(best_vector_score, 4),
            "results": [] if abstained else [doc.to_dict() for doc in docs],
        },
        ensure_ascii=False,
    )
