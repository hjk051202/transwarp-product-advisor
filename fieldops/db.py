"""SQLite persistence for draft and approved work orders."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from fieldops.config import DB_PATH


@contextmanager
def connect(db_path: Path | str = DB_PATH) -> Iterator[sqlite3.Connection]:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Path | str = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS work_orders (
                draft_id TEXT PRIMARY KEY,
                work_order_id TEXT,
                asset_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                parts_json TEXT NOT NULL,
                safety_json TEXT NOT NULL,
                scheduled_at TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                approved_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                detail_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def create_draft(
    *,
    draft_id: str,
    asset_id: str,
    title: str,
    description: str,
    priority: str,
    parts: list[str],
    safety: list[str],
    scheduled_at: str | None,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO work_orders
            (draft_id, work_order_id, asset_id, title, description, priority,
             parts_json, safety_json, scheduled_at, status, created_at, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft_id,
                None,
                asset_id,
                title,
                description,
                priority,
                json.dumps(parts, ensure_ascii=False),
                json.dumps(safety, ensure_ascii=False),
                scheduled_at,
                "draft",
                now,
                None,
            ),
        )
        conn.commit()
    return get_draft(draft_id, db_path=db_path)  # type: ignore[return-value]


def get_draft(draft_id: str, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM work_orders WHERE draft_id = ?", (draft_id,)
        ).fetchone()
    return _row_to_dict(row)


def list_drafts(db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM work_orders ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


def approve_draft(
    draft_id: str,
    work_order_id: str,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE work_orders
            SET status = 'approved', work_order_id = ?, approved_at = ?
            WHERE draft_id = ? AND status = 'draft'
            """,
            (work_order_id, now, draft_id),
        )
        conn.commit()
    return get_draft(draft_id, db_path=db_path)


def get_by_work_order_id(
    work_order_id: str, db_path: Path | str = DB_PATH
) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM work_orders WHERE work_order_id = ?", (work_order_id,)
        ).fetchone()
    return _row_to_dict(row)


def log_audit(
    *,
    request_id: str,
    actor: str,
    action: str,
    resource: str,
    detail: dict[str, Any] | None = None,
    db_path: Path | str = DB_PATH,
) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO audit_log
            (request_id, actor, action, resource, detail_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                actor,
                action,
                resource,
                json.dumps(detail or {}, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()


def list_audit(limit: int = 50, db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["detail"] = json.loads(item.pop("detail_json"))
        result.append(item)
    return result


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    data = dict(row)
    data["parts"] = json.loads(data.pop("parts_json"))
    data["safety"] = json.loads(data.pop("safety_json"))
    return data
