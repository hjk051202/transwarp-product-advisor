"""Compare pure vector retrieval with hybrid (vector + BM25 + RRF)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fieldops.rag import search, vector_only_search

QUESTIONS = Path(__file__).resolve().parent / "questions.jsonl"


def recall(hits: list, expected_doc: str | None) -> bool:
    return expected_doc is None or any(doc.doc_id == expected_doc for doc in hits)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=QUESTIONS)
    args = parser.parse_args()
    rows = [
        json.loads(line)
        for line in args.questions.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    vector_hits = 0
    hybrid_hits = 0
    print(f"{'id':4} {'vector':8} {'hybrid':8}  question")
    for row in rows:
        expected = row.get("expected_doc")
        vector = vector_only_search(row["question"], k=4)
        hybrid = search(row["question"], k=4)
        v_hit = recall(vector, expected)
        h_hit = recall(hybrid, expected)
        vector_hits += int(v_hit)
        hybrid_hits += int(h_hit)
        print(
            f"{row['id']:4} {str(v_hit):8} {str(h_hit):8}  {row['question']}"
        )

    total = len(rows)
    print()
    print(f"vector Recall@4 = {vector_hits}/{total} = {vector_hits / total:.2%}")
    print(f"hybrid Recall@4 = {hybrid_hits}/{total} = {hybrid_hits / total:.2%}")


if __name__ == "__main__":
    main()
