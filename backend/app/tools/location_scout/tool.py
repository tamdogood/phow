from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .agent import get_location_scout_agent, AGENT_SYSTEM_PROMPT


class LocationScoutTool(BaseTool):
    """Tool for analyzing business locations using an AI agent with Google Maps tools."""

    tool_id = "location_scout"
    name = "Location Scout"
    description = "Analyze if a location is good for your business. Get insights on competition, foot traffic, and accessibility using real Google Maps data."
    icon = "📍"
    hints = [
        "Analyze 100 Broadway, New York for a coffee shop",
        "What's near Pike Place Market in Seattle?",
        "Is there good transit access at 500 Market St, San Francisco?",
    ]
    capabilities = [
        "Competition density mapping",
        "Transit accessibility check",
        "Foot traffic indicators",
        "Neighborhood overview",
    ]

    def __init__(self):
        self.agent = get_location_scout_agent()

    def get_system_prompt(self) -> str:
        return AGENT_SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a location analysis request using the agent."""
        response = await self.agent.process(query)
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Would you like me to analyze a different location?",
                "Should I look at a wider or narrower area?",
                "Would you like more details about the competitors?",
            ],
        )

    async def process_stream(
        self, query: str, context: ToolContext
    ) -> AsyncIterator[str]:
        """Process a location analysis request with streaming using the agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
