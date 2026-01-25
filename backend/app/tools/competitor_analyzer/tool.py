"""Competitor Analyzer Tool implementation."""

from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_competitor_analyzer_agent


class CompetitorAnalyzerTool(BaseTool):
    """Tool for deep competitive intelligence analysis."""

    tool_id = "competitor_analyzer"
    name = "Competitor Analyzer"
    description = "Deep dive into your competition. Find competitors, analyze their reviews, understand their positioning, and discover opportunities to differentiate."
    icon = "🔍"
    hints = [
        "Find restaurant competitors near Times Square",
        "Analyze coffee shop competition in Capitol Hill, Seattle",
        "Show me the market positioning for gyms in Miami Beach",
    ]
    capabilities = [
        "Competitor discovery",
        "Review sentiment analysis",
        "Price vs quality positioning",
        "Market gap identification",
    ]

    def __init__(self):
        self.agent = get_competitor_analyzer_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a competitor analysis request using the agent."""
        response = await self.agent.process(query)
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Want me to analyze a specific competitor in detail?",
                "Should I look at competitor reviews to find weaknesses?",
                "Would you like to see how competitors are positioned on price vs. quality?",
            ],
        )

    async def process_stream(self, query: str, context: ToolContext) -> AsyncIterator[str]:
        """Process a competitor analysis request with streaming using the agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            conversation_history=context.conversation_history,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
