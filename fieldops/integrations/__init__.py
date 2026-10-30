"""Adapter factory exports."""

from __future__ import annotations

from fieldops.integrations.cmms import build_cmms_adapter
from fieldops.integrations.erp import build_erp_adapter

__all__ = ["build_cmms_adapter", "build_erp_adapter"]
