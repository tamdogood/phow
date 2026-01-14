"""Market Validator Tool implementation."""

from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_market_validator_agent


class MarketValidatorTool(BaseTool):
    """Tool for validating market potential for business locations."""

    tool_id = "market_validator"
    name = "Market Validator"
    description = "Validate if your business idea is viable at a specific location. Get insights on demographics, competition, and foot traffic with a comprehensive viability score."
    icon = "📊"
    hints = [
        "Is a gym viable at 200 Main St, Austin TX?",
        "Validate a bakery concept for downtown Portland",
        "What demographics support a pet store in Brooklyn?",
    ]
    capabilities = [
        "Demographics analysis",
        "Market size estimation",
        "Competition saturation scoring",
        "Risk & opportunity assessment",
    ]

    def __init__(self):
        self.agent = get_market_validator_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a market validation request using the agent."""
        response = await self.agent.process(query)
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Would you like me to analyze a different location?",
                "Want more details on the competition in this area?",
                "Should I compare this with another location?",
            ],
        )

    async def process_stream(
        self, query: str, context: ToolContext
    ) -> AsyncIterator[str]:
        """Process a market validation request with streaming using the agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
