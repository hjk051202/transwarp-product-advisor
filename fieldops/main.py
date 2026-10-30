"""FastAPI entrypoint for the FieldOps Copilot backend."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from fieldops.agent import get_agent
from fieldops.config import APP_NAME
from fieldops.db import get_draft, init_db
from fieldops.mcp_client import get_mcp_tools
from fieldops.schemas import ApproveResponse, ChatRequest, ChatResponse
from fieldops.service import approve, chat, drafts


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Build eagerly so MCP discovery problems show up at startup.
    await get_agent()
    yield


app = FastAPI(title=APP_NAME, version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    tools = await get_mcp_tools()
    _, mode = await get_agent()
    return {
        "status": "ok",
        "app": APP_NAME,
        "mode": mode,
        "mcp_url": "http://127.0.0.1:8765/mcp",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fieldops.main:app", host="127.0.0.1", port=8000, reload=False)
