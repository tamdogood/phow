from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_location_scout_agent


class LocationScoutTool(BaseTool):
    """Tool for analyzing business locations using an AI agent with Google Maps tools."""

    tool_id = "location_scout"
    name = "Location Scout"
    description = "Analyze if a location is good for your business. Get insights on competition, foot traffic, and accessibility using real Google Maps data."
    icon = "📍"

    def __init__(self):
        self.agent = get_location_scout_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a location analysis request using the agent."""
        # Use the agent to process the query
        response = await self.agent.process(query)

        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Would you like me to analyze a different location?",
                "Should I look at a wider or narrower area?",
                "Would you like more details about the competitors?",
            ],
        )

    async def process_stream(self, query: str, context: ToolContext) -> AsyncIterator[str]:
        """Process a location analysis request with streaming using the agent."""
        # Stream the agent's response
        async for chunk in self.agent.process_stream(query):
            yield chunk
