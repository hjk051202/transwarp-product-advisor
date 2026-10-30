"""API and internal schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    serial: str | None = None


class Citation(BaseModel):
    doc_id: str
    title: str
    section: str
    page: int | None = None
    version: str | None = None
    snippet: str


class ToolTrace(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class WorkOrderDraft(BaseModel):
    draft_id: str
    asset_id: str
    title: str
    description: str
    priority: str
    parts: list[str] = Field(default_factory=list)
    safety: list[str] = Field(default_factory=list)
    scheduled_at: str | None = None
    status: str = "draft"


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
    draft: WorkOrderDraft | None = None
    mode: str = "offline"


class ApproveResponse(BaseModel):
    draft_id: str
    work_order_id: str
    status: str
