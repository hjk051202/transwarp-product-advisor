"""FastAPI entrypoint for the FieldOps Copilot backend."""

from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fieldops import audit
from fieldops.agent import get_agent
from fieldops.config import APP_NAME
from fieldops.db import get_draft, init_db, list_audit
from fieldops.mcp_client import get_mcp_tools
from fieldops.schemas import ApproveResponse, ChatRequest, ChatResponse
from fieldops.service import approve, chat, drafts


def api_key() -> str:
    return os.getenv("FIELDOPS_API_KEY", "").strip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Build eagerly so MCP discovery problems show up at startup.
    await get_agent()
    yield


app = FastAPI(title=APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    actor = request.headers.get("X-User") or "api"
    audit.set_context(request_id, actor)

    key = api_key()
    if key and request.url.path not in PUBLIC_PATHS:
        provided = request.headers.get("X-API-Key", "")
        if not provided:
            auth = request.headers.get("Authorization", "")
            if auth.lower().startswith("bearer "):
                provided = auth[7:].strip()
        if not provided or not secrets.compare_digest(provided, key):
            return JSONResponse(
                status_code=401,
                content={"detail": "invalid or missing API key"},
                headers={"X-Request-ID": request_id},
            )

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
async def health() -> dict[str, Any]:
    tools = await get_mcp_tools()
    _, mode = await get_agent()
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": "1.0.0",
        "mode": mode,
        "auth_enabled": bool(api_key()),
        "mcp_url": os.getenv("CMMS_MCP_URL", "http://127.0.0.1:8765/mcp"),
        "mcp_tools": [tool.name for tool in tools],
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    return await chat(request.message, request.serial)


@app.get("/work-orders")
async def list_work_orders() -> list[dict[str, Any]]:
    return drafts()


@app.get("/work-orders/{draft_id}")
async def get_work_order(draft_id: str) -> dict[str, Any]:
    draft = get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="draft not found")
    return draft


@app.post("/work-orders/{draft_id}/approve", response_model=ApproveResponse)
async def approve_work_order(draft_id: str) -> ApproveResponse:
    try:
        return await approve(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/audit")
async def audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    return list_audit(limit=max(1, min(limit, 200)))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fieldops.main:app", host="127.0.0.1", port=8000, reload=False)
