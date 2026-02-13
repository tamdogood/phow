import json
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from ...models.chat import ChatRequest
from ...services.chat_service import ChatService
from ..deps import get_chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Handle chat request with streaming response."""

    async def generate():
        try:
            async for content, event_type in chat_service.process_message(
                session_id=request.session_id,
                tool_id=request.tool_id,
                message=request.message,
                conversation_id=request.conversation_id,
                user_id=request.user_id,
            ):
                if event_type == "chunk":
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"content": content}),
                    }
                elif event_type == "done":
                    yield {
                        "event": "done",
                        "data": json.dumps({"conversation_id": content}),
                    }
                elif event_type == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"error": content}),
                    }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(generate())


@router.get("/conversations")
async def list_conversations(
    session_id: str,
    user_id: str | None = None,
    chat_service: ChatService = Depends(get_chat_service),
):
    """List conversations for a session or user."""
    conversations = await chat_service.list_conversations(session_id, user_id)
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get all messages in a conversation."""
    messages = await chat_service.get_messages(conversation_id)
    return {"messages": messages}


@router.patch("/conversations/{conversation_id}/title")
async def update_conversation_title(
    conversation_id: str,
    title: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Update conversation title."""
    conversation = await chat_service.update_conversation_title(conversation_id, title)
    return {"conversation": conversation}
