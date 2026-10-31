"""Adapter contracts for conversation history and product catalog."""

from __future__ import annotations

from typing import Any, Protocol


class HistoryAdapter(Protocol):
    async def save_conversation(self, payload: dict[str, Any]) -> dict[str, Any]: ...

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None: ...

    async def list_conversations(self, limit: int = 20) -> list[dict[str, Any]]: ...


class CatalogAdapter(Protocol):
    def get_product(self, name: str) -> dict[str, Any] | None: ...

    def list_products(
        self, workload: str | None = None, industry: str | None = None
    ) -> list[dict[str, Any]]: ...

    def search_cases(
        self, industry: str | None = None, scenario: str = ""
    ) -> list[dict[str, Any]]: ...

    def check_compatibility(self, os_name: str, cpu: str) -> dict[str, Any]: ...
