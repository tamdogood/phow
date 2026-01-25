"""Market Research Tool - Unified BaseTool implementation."""

from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_market_research_agent


class MarketResearchTool(BaseTool):
    """Unified tool for comprehensive market research combining location, demographics, and competitor analysis."""

    tool_id = "market_research"
    name = "Market Research"
    description = "Comprehensive market research combining location analysis, demographics, and competitor intelligence. Get viability scores, neighborhood insights, and competitive positioning for any business location."
    icon = "🔬"
    hints = [
        "Is a coffee shop viable at 123 Main St, Seattle?",
        "Full market research for a gym in downtown Austin",
        "Who are my competitors for a bakery in Brooklyn?",
        "What's the foot traffic like near Times Square?",
    ]
    capabilities = [
        "Location & neighborhood analysis",
        "Demographics & market viability scoring",
        "Competitor discovery & analysis",
        "Competitive positioning maps",
        "Risk & opportunity assessment",
    ]

    def __init__(self):
        self.agent = get_market_research_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a market research request using the unified agent."""
        response = await self.agent.process(query)
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Would you like me to analyze a different location?",
                "Want more details on specific competitors?",
                "Should I create a positioning map for this market?",
            ],
        )

    async def process_stream(self, query: str, context: ToolContext) -> AsyncIterator[str]:
        """Process a market research request with streaming using the unified agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            conversation_history=context.conversation_history,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
