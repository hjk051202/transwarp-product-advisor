"""SQLite persistence for leads and audit logs."""

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
            CREATE TABLE IF NOT EXISTS leads (
                lead_id TEXT PRIMARY KEY,
                crm_lead_id TEXT,
                company TEXT NOT NULL,
                industry TEXT NOT NULL,
                contact TEXT NOT NULL,
                need TEXT NOT NULL,
                products_json TEXT NOT NULL,
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


def create_lead(
    *,
    lead_id: str,
    company: str,
    industry: str,
    contact: str,
    need: str,
    products: list[str],
    status: str = "draft",
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO leads
            (lead_id, crm_lead_id, company, industry, contact, need,
             products_json, status, created_at, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                None,
                company,
                industry,
                contact,
                need,
                json.dumps(products, ensure_ascii=False),
                status,
                now,
                None,
            ),
        )
        conn.commit()
    return get_lead(lead_id, db_path=db_path)  # type: ignore[return-value]


def get_lead(lead_id: str, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    return _row_to_dict(row)


def list_leads(db_path: Path | str = DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT 30"
        ).fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


def approve_lead(
    lead_id: str, crm_lead_id: str, db_path: Path | str = DB_PATH
) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            UPDATE leads
            SET status = 'approved', crm_lead_id = ?, approved_at = ?
            WHERE lead_id = ? AND status = 'draft'
            """,
            (crm_lead_id, now, lead_id),
        )
        conn.commit()
    return get_lead(lead_id, db_path=db_path)


def get_by_crm_lead_id(
    crm_lead_id: str, db_path: Path | str = DB_PATH
) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE crm_lead_id = ?", (crm_lead_id,)
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
    init_db(db_path)
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
    init_db(db_path)
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
    data["products"] = json.loads(data.pop("products_json"))
    return data
