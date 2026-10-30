"""Adapter contracts for external systems."""

from __future__ import annotations

from typing import Any, Protocol


class CMMSAdapter(Protocol):
    async def create_work_order(self, draft: dict[str, Any]) -> dict[str, Any]: ...

    async def get_work_order(self, work_order_id: str) -> dict[str, Any] | None: ...


class ERPAdapter(Protocol):
    def get_warranty(self, serial: str) -> dict[str, Any] | None: ...

    def get_part(self, part_no: str, region: str = "上海") -> dict[str, Any] | None: ...

    def get_telemetry(self, asset_id: str, minutes: int = 30) -> dict[str, Any] | None: ...
