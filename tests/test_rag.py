from __future__ import annotations

import json

from fieldops.rag import search, search_json


def test_search_finds_argodb_product_doc() -> None:
    docs = search("ArgoDB 数据仓库 实时分析 HTAP", k=4)
    assert docs
    assert any(doc.doc_id == "tw-argodb" for doc in docs)
    assert any(doc.product == "ArgoDB" for doc in docs)


def test_hybrid_recovers_product_chunk_missed_by_vector_only() -> None:
    query = "ArgoDB 适合什么业务场景？"
    hybrid_ids = {doc.doc_id for doc in search(query, k=4)}
    assert "tw-argodb" in hybrid_ids


def test_search_exposes_rrf_and_vector_scores() -> None:
    docs = search("TDH 支持多少种存储模型？", k=4)
    assert docs
    assert all(doc.score > 0 for doc in docs)
    assert any(doc.vector_score > 0 for doc in docs)


def test_out_of_domain_query_abstains() -> None:
    payload = json.loads(search_json("今天天气怎么样？", k=4))
    assert payload["abstained"] is True
    assert payload["results"] == []


def test_domain_query_does_not_abstain() -> None:
    payload = json.loads(search_json("星环产品有哪些常见组合？", k=4))
    assert payload["abstained"] is False
    assert payload["results"]
