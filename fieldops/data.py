"""Small JSON data-access layer for the demo.

In production this would be replaced by the IoT / ERP / CRM APIs.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from fieldops.config import DATA_DIR, MANUAL_DIR


@lru_cache(maxsize=1)
def _devices() -> dict[str, dict[str, Any]]:
    return json.loads((DATA_DIR / "devices.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _parts() -> dict[str, dict[str, Any]]:
    return json.loads((DATA_DIR / "parts.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _telemetry() -> dict[str, dict[str, Any]]:
    return json.loads((DATA_DIR / "telemetry.json").read_text(encoding="utf-8"))


def get_device(serial: str) -> dict[str, Any] | None:
    return _devices().get(serial.strip().upper())


def get_part(part_no: str) -> dict[str, Any] | None:
    return _parts().get(part_no.strip().upper())


def get_telemetry(asset_id: str, minutes: int = 30) -> dict[str, Any] | None:
    data = _telemetry().get(asset_id.strip().upper())
    if not data:
        return None
    return {**data, "window_minutes": minutes}


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Parse the small YAML subset used by the sample manuals.

    Avoids a PyYAML dependency for a handful of scalar fields.
    """

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


def load_manuals() -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for path in sorted(MANUAL_DIR.glob("*.md")):
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        metadata.setdefault("doc_id", path.stem)
        metadata["source_path"] = str(path.relative_to(DATA_DIR.parent))
        documents.append(
            {
                "id": metadata["doc_id"],
                "text": body,
                "metadata": metadata,
            }
        )
    return documents
