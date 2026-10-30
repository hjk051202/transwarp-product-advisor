"""Request-scoped audit helpers."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from fieldops.db import init_db, log_audit

_request_id: ContextVar[str] = ContextVar("fieldops_request_id", default="")
_actor: ContextVar[str] = ContextVar("fieldops_actor", default="api")


def set_context(request_id: str, actor: str = "api") -> None:
    _request_id.set(request_id)
    _actor.set(actor)


def request_id() -> str:
    return _request_id.get()


def actor() -> str:
    return _actor.get()


def log(action: str, resource: str = "", detail: dict[str, Any] | None = None) -> None:
    init_db()
    log_audit(
        request_id=request_id() or "internal",
        actor=actor(),
        action=action,
        resource=resource,
        detail=detail,
    )
