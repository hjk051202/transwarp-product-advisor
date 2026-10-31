"""API and internal schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str | None = None
    company: str | None = None
    industry: str | None = None


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


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
    conversation_id: str = ""
    mode: str = "offline"


class Conversation(BaseModel):
    conversation_id: str
    session_id: str
    user_message: str
    assistant_message: str
    citations: list[Citation] = Field(default_factory=list)
    tool_trace: list[ToolTrace] = Field(default_factory=list)
    mode: str = ""
    created_at: str = ""
