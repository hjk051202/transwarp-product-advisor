"""SQLite persistence for conversation history and audit logs."""

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
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_message TEXT NOT NULL,
                citations_json TEXT NOT NULL,
                tool_trace_json TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT NOT NULL
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


def create_conversation(
    *,
    conversation_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
    citations: list[dict[str, Any]],
    tool_trace: list[dict[str, Any]],
    mode: str,
    db_path: Path | str = DB_PATH,
) -> dict[str, Any]:
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO conversations
            (conversation_id, session_id, user_message, assistant_message,
             citations_json, tool_trace_json, mode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                conversation_id,
                session_id,
                user_message,
                assistant_message,
                json.dumps(citations, ensure_ascii=False),
                json.dumps(tool_trace, ensure_ascii=False),
                mode,
                now,
            ),
        )
        conn.commit()
    return get_conversation(conversation_id, db_path=db_path)  # type: ignore[return-value]


def get_conversation(
    conversation_id: str, db_path: Path | str = DB_PATH
) -> dict[str, Any] | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?",
            (conversation_id,),
        ).fetchone()
    return _row_to_dict(row)


def list_conversations(
    limit: int = 20, session_id: str | None = None, db_path: Path | str = DB_PATH
) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        if session_id:
            rows = conn.execute(
                "SELECT * FROM conversations WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [_row_to_dict(row) for row in rows if row is not None]


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
    data["citations"] = json.loads(data.pop("citations_json"))
    data["tool_trace"] = json.loads(data.pop("tool_trace_json"))
    return data
