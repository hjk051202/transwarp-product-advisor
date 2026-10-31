"""Adapter factory exports."""

from __future__ import annotations

from fieldops.integrations.catalog import build_catalog_adapter
from fieldops.integrations.history import build_history_adapter

__all__ = ["build_catalog_adapter", "build_history_adapter"]
