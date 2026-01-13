import json
from fastapi import APIRouter, HTTPException, Depends
from sse_starlette.sse import EventSourceResponse
from ...models.chat import ChatRequest
from ...services import ChatService
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
    chat_service: ChatService = Depends(get_chat_service),
):
    """List all conversations for a session."""
    conversations = await chat_service.list_conversations(session_id)
    return {"conversations": conversations}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Get all messages in a conversation."""
    messages = await chat_service.get_messages(conversation_id)
    return {"messages": messages}
