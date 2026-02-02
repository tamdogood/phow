"""Business Advisor agent for guiding new users."""

from typing import AsyncIterator, Any

from ...core.llm import get_llm_service
from ...core.logging import get_logger
from .prompts import SYSTEM_PROMPT

logger = get_logger("agent.business_advisor")


class BusinessAdvisorAgent:
    """Agent that helps users discover which tools to use."""

    def __init__(self):
        self.llm_service = get_llm_service()

    async def process(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
        business_profile: dict | None = None,
    ) -> str:
        """Process query and return response."""
        messages = self._build_messages(query, conversation_history, business_profile)
        return await self.llm_service.chat(messages, system=SYSTEM_PROMPT)

    async def process_stream(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
        business_profile: dict | None = None,
        **kwargs,  # Accept tracking_service, session_id, conversation_id but don't use
    ) -> AsyncIterator[str]:
        """Stream response chunks."""
        logger.info("Processing business advisor query (streaming)", query=query[:100])
        messages = self._build_messages(query, conversation_history, business_profile)
        async for chunk in self.llm_service.chat_stream(messages, system=SYSTEM_PROMPT):
            yield chunk

    def _build_messages(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
        business_profile: dict | None = None,
    ) -> list[dict]:
        """Build message list for LLM."""
        messages = []

        # Add business profile context if available
        if business_profile:
            profile_context = self._format_profile(business_profile)
            messages.append(
                {"role": "system", "content": f"User's business profile:\n{profile_context}"}
            )

        # Add conversation history (last 6 messages for context)
        if conversation_history:
            for msg in conversation_history[-6:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current query
        messages.append({"role": "user", "content": query})
        return messages

    def _format_profile(self, profile: dict) -> str:
        """Format business profile for context."""
        parts = []
        if profile.get("business_name"):
            parts.append(f"Business: {profile['business_name']}")
        if profile.get("business_type"):
            parts.append(f"Type: {profile['business_type']}")
        if profile.get("address"):
            parts.append(f"Location: {profile['address']}")
        if profile.get("description"):
            parts.append(f"Description: {profile['description']}")
        return "\n".join(parts) if parts else "No profile set up yet."


def get_business_advisor_agent() -> BusinessAdvisorAgent:
    """Factory function for BusinessAdvisorAgent."""
    return BusinessAdvisorAgent()
