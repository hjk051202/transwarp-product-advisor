"""Catalog adapters: local JSON (default) and a real HTTP skeleton."""

from __future__ import annotations

import os
from typing import Any

import httpx

from fieldops.data import (
    check_compatibility as json_compatibility,
    get_product as json_get_product,
    list_products as json_list_products,
    search_cases as json_search_cases,
)
from fieldops.integrations.base import CatalogAdapter


class JsonCatalogAdapter:
    def get_product(self, name: str) -> dict[str, Any] | None:
        return json_get_product(name)

    def list_products(
        self, workload: str | None = None, industry: str | None = None
    ) -> list[dict[str, Any]]:
        return json_list_products(workload=workload, industry=industry)

    def search_cases(
        self, industry: str | None = None, scenario: str = ""
    ) -> list[dict[str, Any]]:
        return json_search_cases(industry=industry, scenario=scenario)

    def check_compatibility(self, os_name: str, cpu: str) -> dict[str, Any]:
        return json_compatibility(os_name, cpu)


class HttpCatalogAdapter:
    """Skeleton adapter for a real product catalog API."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key} if api_key else {}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(
                    f"{self.base_url}{path}", params=params, headers=self.headers
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except Exception:
            return None

    def get_product(self, name: str) -> dict[str, Any] | None:
        return self._get(f"/products/{name}")

    def list_products(
        self, workload: str | None = None, industry: str | None = None
    ) -> list[dict[str, Any]]:
        data = self._get("/products", {"workload": workload, "industry": industry})
        return data if isinstance(data, list) else []

    def search_cases(
        self, industry: str | None = None, scenario: str = ""
    ) -> list[dict[str, Any]]:
        data = self._get("/cases", {"industry": industry, "scenario": scenario})
        return data if isinstance(data, list) else []

    def check_compatibility(self, os_name: str, cpu: str) -> dict[str, Any]:
        data = self._get("/compatibility", {"os": os_name, "cpu": cpu})
        return data if isinstance(data, dict) else {}


def build_catalog_adapter() -> CatalogAdapter:
    if os.getenv("CATALOG_ADAPTER", "json").lower() == "http":
        return HttpCatalogAdapter(
            base_url=os.getenv("CATALOG_HTTP_URL", "http://127.0.0.1:9100"),
            api_key=os.getenv("CATALOG_HTTP_API_KEY", ""),
        )
    return JsonCatalogAdapter()
