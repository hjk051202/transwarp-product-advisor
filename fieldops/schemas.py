"""API and internal schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    company: str | None = None
    industry: str | None = None
    contact: str | None = None


class Citation(BaseModel):
    doc_id: str
    title: str
    product: str = ""
    section: str
    page: int | None = None
    version: str | None = None
    snippet: str


class ToolTrace(BaseModel):
    name: str
    args: dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class LeadDraft(BaseModel):
    lead_id: str
    company: str
    industry: str
    contact: str
    need: str
    products: list[str] = Field(default_factory=list)
    status: str = "draft"


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
    lead: LeadDraft | None = None
    mode: str = "offline"


class ApproveResponse(BaseModel):
    lead_id: str
    crm_lead_id: str
    status: str
