from __future__ import annotations

from fieldops.rag import search


def test_search_finds_argodb_product_doc() -> None:
    docs = search("ArgoDB 数据仓库 实时分析 HTAP", k=4)
    assert docs
    assert any(doc.doc_id == "tw-argodb" for doc in docs)
    assert any(doc.product == "ArgoDB" for doc in docs)


def test_search_has_citation_metadata() -> None:
    docs = search("StellarDB 图数据库 反欺诈", k=3)
    assert docs
    for doc in docs:
        assert doc.doc_id
        assert doc.title
        assert doc.section
