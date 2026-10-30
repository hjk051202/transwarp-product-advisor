from __future__ import annotations

import json

from fieldops.tools import check_parts, check_warranty, draft_work_order, get_telemetry


def test_telemetry_tool() -> None:
    data = json.loads(get_telemetry.invoke({"asset_id": "8F2-1042", "minutes": 30}))
    assert data["latest"]["fan_rpm"] == 0
    assert data["latest"]["error_code"] == "E-204"


def test_warranty_and_parts_tools() -> None:
    warranty = json.loads(check_warranty.invoke({"serial": "8F2-1042"}))
    assert warranty["warranty"] == "在保"

    parts = json.loads(check_parts.invoke({"part_no": "FAN-12038", "region": "上海"}))
    assert parts["stock"] == 3


def test_draft_tool_creates_draft() -> None:
    draft = json.loads(
        draft_work_order.invoke(
            {
                "asset_id": "8F2-1042",
                "title": "pytest draft",
                "description": "test",
                "parts": ["FAN-12038"],
            }
        )
    )
    assert draft["draft_id"].startswith("DRF-")
    assert draft["status"] == "draft"
    assert draft["parts"] == ["FAN-12038"]
