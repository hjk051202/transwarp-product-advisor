"""Data access for products, cases, compatibility and knowledge documents."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from fieldops.config import DATA_DIR, KNOWLEDGE_DIR


@lru_cache(maxsize=1)
def load_products() -> dict[str, dict[str, Any]]:
    return json.loads((DATA_DIR / "products.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_cases() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "cases.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_compatibility() -> dict[str, Any]:
    return json.loads((DATA_DIR / "compatibility.json").read_text(encoding="utf-8"))


def get_product(name: str) -> dict[str, Any] | None:
    wanted = name.strip().lower()
    for key, product in load_products().items():
        if key.lower() == wanted or product["name"].lower() == wanted:
            return {**product, "key": key}
    return None


def list_products(
    workload: str | None = None, industry: str | None = None
) -> list[dict[str, Any]]:
    result = []
    for key, product in load_products().items():
        if workload and not any(
            workload.lower() in item.lower() for item in product["workloads"]
        ):
            continue
        if industry and not any(
            industry.lower() in item.lower() for item in product["industries"]
        ):
            continue
        result.append({**product, "key": key})
    return result


def search_cases(industry: str | None = None, scenario: str = "") -> list[dict[str, Any]]:
    results = []
    for case in load_cases():
        if industry and industry not in case["industry"]:
            continue
        haystack = f"{case['scenario']} {case['summary']} {' '.join(case['products'])}"
        if scenario and not any(token in haystack for token in scenario.split()):
            continue
        results.append(case)
    return results


def check_compatibility(os_name: str, cpu: str) -> dict[str, Any]:
    data = load_compatibility()
    os_row = next(
        (value for key, value in data["os"].items() if key.lower() in os_name.lower()),
        None,
    )
    cpu_row = next(
        (value for key, value in data["cpu"].items() if key.lower() in cpu.lower()),
        None,
    )
    return {
        "os": os_name,
        "cpu": cpu,
        "os_support": os_row,
        "cpu_support": cpu_row,
        "note": data["note"],
    }


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the small YAML subset used by the demo knowledge files."""

    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata: dict[str, Any] = {}
    for line in parts[1].strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.isdigit():
            metadata[key] = int(value)
        elif value.lower() in {"true", "false"}:
            metadata[key] = value.lower() == "true"
        else:
            metadata[key] = value
    return metadata, parts[2].strip()


def load_knowledge() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.md")):
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        metadata.setdefault("doc_id", path.stem)
        metadata["source_path"] = str(path.relative_to(DATA_DIR.parent))
        documents.append({"id": metadata["doc_id"], "text": body, "metadata": metadata})
    return documents


def load_pdf_knowledge() -> list[dict[str, Any]]:
    pdf_dir = KNOWLEDGE_DIR / "pdf"
    if not pdf_dir.exists():
        return []
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    documents: list[dict[str, Any]] = []
    for path in sorted(pdf_dir.glob("*.pdf")):
        try:
            text = "\n".join(
                page.extract_text() or "" for page in PdfReader(str(path)).pages
            )
        except Exception:
            continue
        metadata, body = parse_frontmatter(text)
        metadata.setdefault("doc_id", f"pdf-{path.stem}")
        metadata.setdefault("title", path.stem)
        metadata.setdefault("product", "all")
        metadata.setdefault("doc_type", "pdf")
        metadata["source_path"] = str(path.relative_to(DATA_DIR.parent))
        documents.append({"id": metadata["doc_id"], "text": body, "metadata": metadata})
    return documents


def all_knowledge() -> list[dict[str, Any]]:
    return [*load_knowledge(), *load_pdf_knowledge()]
