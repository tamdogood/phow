"""Review Responder Tool implementation."""

from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_review_responder_agent


class ReviewResponderTool(BaseTool):
    """Tool for generating responses to customer reviews."""

    tool_id = "review_responder"
    name = "Review Responder"
    description = "Get AI-generated response drafts for customer reviews. Analyzes sentiment, identifies key issues, and provides multiple tone options."
    icon = "⭐"
    hints = [
        "Help me respond to this 2-star review: 'The food was cold and we waited 45 minutes'",
        "How should I respond to: 'Great service but the portions were small'",
        "Draft a response for: 'Best coffee in town! Will definitely be back!'",
    ]
    capabilities = [
        "Sentiment analysis",
        "Multiple tone options",
        "Key issues extraction",
        "Response templates",
    ]

    def __init__(self):
        self.agent = get_review_responder_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a review response request using the agent."""
        response = await self.agent.process(query)
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Would you like me to adjust the tone of any response?",
                "Should I create a response for a different review?",
                "Would you like tips for handling similar reviews in the future?",
            ],
        )

    async def process_stream(self, query: str, context: ToolContext) -> AsyncIterator[str]:
        """Process a review response request with streaming using the agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
