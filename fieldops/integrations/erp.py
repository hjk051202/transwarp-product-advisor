"""ERP adapters: JSON demo data (default) and a real HTTP skeleton."""

from __future__ import annotations

import os
from typing import Any

import httpx

from fieldops.data import get_device, get_part, get_telemetry
from fieldops.integrations.base import ERPAdapter


class JsonERPAdapter:
    def get_warranty(self, serial: str) -> dict[str, Any] | None:
        return get_device(serial)

    def get_part(self, part_no: str, region: str = "上海") -> dict[str, Any] | None:
        part = get_part(part_no)
        if not part:
            return None
        return {
            "part_no": part["part_no"],
            "name": part["name"],
            "spec": part["spec"],
            "region": region,
            "stock": part["stock"].get(region, 0),
            "all_stock": part["stock"],
            "price_cny": part["price_cny"],
            "warranty_covered": part["warranty_covered"],
        }

    def get_telemetry(self, asset_id: str, minutes: int = 30) -> dict[str, Any] | None:
        return get_telemetry(asset_id, minutes)


class HttpERPAdapter:
    """Skeleton adapter for a real ERP/IoT API."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key} if api_key else {}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(
                    f"{self.base_url}{path}", params=params, headers=self.headers
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                return data if isinstance(data, dict) else None
        except Exception:
            return None

    def get_warranty(self, serial: str) -> dict[str, Any] | None:
        return self._get(f"/warranty/{serial}")

    def get_part(self, part_no: str, region: str = "上海") -> dict[str, Any] | None:
        return self._get(f"/parts/{part_no}", {"region": region})

    def get_telemetry(self, asset_id: str, minutes: int = 30) -> dict[str, Any] | None:
        return self._get(f"/telemetry/{asset_id}", {"minutes": minutes})


def build_erp_adapter() -> ERPAdapter:
    kind = os.getenv("ERP_ADAPTER", "json").lower()
    if kind == "http":
        return HttpERPAdapter(
            base_url=os.getenv("ERP_HTTP_URL", "http://127.0.0.1:9100"),
            api_key=os.getenv("ERP_HTTP_API_KEY", ""),
        )
    return JsonERPAdapter()
