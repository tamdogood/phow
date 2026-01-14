"""Social Media Coach Tool implementation."""

from typing import AsyncIterator
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT
from .agent import get_social_media_coach_agent


class SocialMediaCoachTool(BaseTool):
    """Tool for generating social media content ideas for small businesses."""

    tool_id = "social_media_coach"
    name = "Social Media Coach"
    description = "Get daily social media content ideas tailored to your business, location, and current events. Weather-aware suggestions with ready-to-post captions."
    icon = "📱"
    hints = [
        "What should I post today for my coffee shop in Austin?",
        "Give me content ideas for my restaurant this week",
        "What hashtags should I use for my bakery in Seattle?",
    ]
    capabilities = [
        "Daily content ideas",
        "Weather-aware suggestions",
        "Trending hashtags",
        "Best posting times",
    ]

    def __init__(self):
        self.agent = get_social_media_coach_agent()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a social media content request using the agent."""
        response = await self.agent.process(query)
        return ToolResponse(
            message=response,
            follow_up_questions=[
                "Want me to create more post ideas for a different day?",
                "Should I suggest captions in a different tone?",
                "Would you like content ideas for a specific platform?",
            ],
        )

    async def process_stream(
        self, query: str, context: ToolContext
    ) -> AsyncIterator[str]:
        """Process a social media content request with streaming using the agent."""
        async for chunk in self.agent.process_stream(
            query=query,
            tracking_service=context.tracking_service,
            session_id=context.session_id,
            conversation_id=context.conversation_id,
        ):
            yield chunk
