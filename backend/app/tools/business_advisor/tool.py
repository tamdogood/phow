"""Business Advisor Tool implementation."""

from typing import AsyncIterator

from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_business_advisor_agent


class BusinessAdvisorTool(BaseTool):
    """Tool for helping users discover which PHOW tools to use."""

    tool_id = "business_advisor"
    name = "Business Advisor"
    description = "Not sure where to start? Tell us about your business situation and we'll recommend the best tools for you."
    icon = "🧭"
    hints = [
        "I don't know where to start",
        "Help me figure out what I need",
        "I have a business idea but not sure what to do next",
        "What can PHOW help me with?",
    ]
    capabilities = [
        "Understand your business stage",
        "Identify your biggest challenges",
        "Recommend the right tools",
        "Guide you through your first analysis",
    ]

    def __init__(self):
        self.agent = get_business_advisor_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a request using the agent."""
        response = await self.agent.process(
            query=query,
            conversation_history=context.conversation_history,
            business_profile=context.business_profile,
        )
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Would you like me to explain any of these tools in more detail?",
                "Should we start with the first recommendation?",
            ],
        )

    async def process_stream(self, query: str, context: ToolContext) -> AsyncIterator[str]:
        """Process a request with streaming using the agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            conversation_history=context.conversation_history,
            business_profile=context.business_profile,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
