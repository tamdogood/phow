from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    session_id: str
    conversation_id: str | None = None
    tool_id: str
    message: str
    user_id: str | None = None


class Message(BaseModel):
    """A chat message."""

    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    metadata: dict[str, Any] | None = None
    created_at: datetime


class Conversation(BaseModel):
    """A conversation."""

    id: str
    session_id: str
    tool_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatResponse(BaseModel):
    """Non-streaming chat response."""

    message: str
    conversation_id: str
    data: dict[str, Any] | None = None
