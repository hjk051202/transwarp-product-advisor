"""Adapter factory exports."""

from __future__ import annotations

from fieldops.integrations.catalog import build_catalog_adapter
from fieldops.integrations.crm import build_crm_adapter

__all__ = ["build_catalog_adapter", "build_crm_adapter"]
