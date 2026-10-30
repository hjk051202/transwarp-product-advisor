from __future__ import annotations

import pytest

from fieldops.db import create_draft
from fieldops.integrations import build_cmms_adapter, build_erp_adapter


def test_json_erp_adapter() -> None:
    erp = build_erp_adapter()
    warranty = erp.get_warranty("8F2-1042")
    assert warranty is not None
    assert warranty["warranty"] == "在保"

    part = erp.get_part("FAN-12038")
    assert part is not None
    assert part["stock"] == 3

    telemetry = erp.get_telemetry("8F2-1042")
    assert telemetry is not None
    assert telemetry["latest"]["fan_rpm"] == 0


@pytest.mark.asyncio
async def test_local_cmms_adapter(monkeypatch) -> None:
    monkeypatch.setenv("CMMS_ADAPTER", "local")
    draft = create_draft(
        draft_id="DRF-adapter-test",
        asset_id="8F2-1042",
        title="adapter test",
        description="test",
        priority="P2",
        parts=["FAN-12038"],
        safety=["LOTO"],
        scheduled_at="2026-10-31 10:00",
    )
    adapter = build_cmms_adapter()
    result = await adapter.create_work_order(draft)
    assert result["work_order_id"].startswith("WO-")
    fetched = await adapter.get_work_order(result["work_order_id"])
    assert fetched is not None
    assert fetched["draft_id"] == "DRF-adapter-test"
