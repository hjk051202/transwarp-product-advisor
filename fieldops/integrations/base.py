"""Adapter contracts for CRM and product catalog systems."""

from __future__ import annotations

from typing import Any, Protocol


class CRMAdapter(Protocol):
    async def create_lead(self, lead: dict[str, Any]) -> dict[str, Any]: ...

    async def get_lead(self, crm_lead_id: str) -> dict[str, Any] | None: ...


class CatalogAdapter(Protocol):
    def get_product(self, name: str) -> dict[str, Any] | None: ...

    def list_products(
        self, workload: str | None = None, industry: str | None = None
    ) -> list[dict[str, Any]]: ...

    def search_cases(
        self, industry: str | None = None, scenario: str = ""
    ) -> list[dict[str, Any]]: ...

    def check_compatibility(self, os_name: str, cpu: str) -> dict[str, Any]: ...
