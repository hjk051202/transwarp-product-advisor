"""Retrieval evaluation for the sample manual corpus."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fieldops.rag import search

QUESTIONS = Path(__file__).resolve().parent / "questions.jsonl"


def main() -> None:
    rows = [
        json.loads(line)
        for line in QUESTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    hits = 0
    page_hits = 0
    for row in rows:
        docs = search(row["question"], k=4)
        doc_ids = [doc.doc_id for doc in docs]
        hit = row["expected_doc"] in doc_ids
        page_hit = any(
            doc.doc_id == row["expected_doc"] and doc.page == row.get("expected_page")
            for doc in docs
        )
        hits += int(hit)
        page_hits += int(page_hit)
        print(
            f"{row['id']}  hit={hit!s:5}  page={page_hit!s:5}  "
            f"expected={row['expected_doc']}  got={doc_ids}"
        )

    total = len(rows)
    print()
    print(f"Recall@4 (doc)  = {hits}/{total} = {hits / total:.2%}")
    print(f"Page hit@4      = {page_hits}/{total} = {page_hits / total:.2%}")


if __name__ == "__main__":
    main()
