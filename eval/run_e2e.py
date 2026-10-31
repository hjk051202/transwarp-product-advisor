"""End-to-end evaluation for the product advisor.

Metrics:
- citation_hit: expected document appears in returned citations
- answer_hit: at least one expected keyword appears in the answer
- lead_hit: lead presence matches expectation
- latency
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fieldops.service import chat

QUESTIONS = Path(__file__).resolve().parent / "e2e_questions.jsonl"


async def main() -> None:
    rows = [
        json.loads(line)
        for line in QUESTIONS.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    citation_hits = 0
    answer_hits = 0
    lead_hits = 0
    latencies: list[float] = []

    for row in rows:
        start = time.perf_counter()
        response = await chat(
            row["question"],
            company=row.get("company"),
            industry=row.get("industry"),
            contact=row.get("contact"),
        )
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)

        cited = {item.doc_id for item in response.citations}
        expected_doc = row.get("expected_doc")
        citation_hit = expected_doc is None or expected_doc in cited
        answer_hit = any(keyword in response.answer for keyword in row.get("keywords", []))
        lead_hit = (response.lead is not None) == bool(row.get("expect_lead"))

        citation_hits += int(citation_hit)
        answer_hits += int(answer_hit)
        lead_hits += int(lead_hit)
        print(
            f"{row['id']}  citation={citation_hit!s:5}  answer={answer_hit!s:5}  "
            f"lead={lead_hit!s:5}  {elapsed:6.0f}ms"
        )

    total = len(rows)
    latencies.sort()
    print()
    print(f"citation_hit@4  = {citation_hits}/{total} = {citation_hits / total:.2%}")
    print(f"answer_keyword  = {answer_hits}/{total} = {answer_hits / total:.2%}")
    print(f"lead_expect     = {lead_hits}/{total} = {lead_hits / total:.2%}")
    print(f"p50 latency     = {latencies[len(latencies) // 2]:.0f} ms")
    print(f"p95 latency     = {latencies[int(len(latencies) * 0.95) - 1]:.0f} ms")


if __name__ == "__main__":
    asyncio.run(main())
