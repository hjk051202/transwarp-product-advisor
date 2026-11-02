"""Check the configured embedding backend without touching the vector index."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fieldops.rag import build_embeddings, embedding_signature


def main() -> None:
    embeddings = build_embeddings()
    vector = embeddings.embed_query("ArgoDB 产品选型测试")
    print(f"backend: {type(embeddings).__name__}")
    print(f"signature: {embedding_signature()}")
    print(f"dimension: {len(vector)}")


if __name__ == "__main__":
    main()
