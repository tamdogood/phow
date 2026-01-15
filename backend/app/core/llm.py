from enum import Enum
from typing import AsyncIterator
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from .config import get_settings


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMService:
    """LangChain-based LLM service with provider abstraction."""

    def __init__(self, provider: LLMProvider | None = None):
        settings = get_settings()
        self.provider = provider or LLMProvider(settings.llm_provider)
        self.llm = self._create_llm()

    def _create_llm(self) -> BaseChatModel:
        """Create LangChain LLM instance based on provider."""
        settings = get_settings()

        if self.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key,
                temperature=0.4,  # Lower for more deterministic tool calling
                max_tokens=4096,  # Prevent runaway responses
                streaming=True,
            )
        else:  # ANTHROPIC
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=settings.anthropic_api_key,
                temperature=0.4,  # Lower for more deterministic tool calling
                max_tokens=4096,
            )

    def _format_messages(self, messages: list[dict], system: str | None = None) -> list:
        """Convert dict messages to LangChain message objects."""
        lc_messages = []

        if system:
            lc_messages.append(SystemMessage(content=system))

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        return lc_messages

    async def chat(self, messages: list[dict], system: str | None = None) -> str:
        """Generate a chat completion."""
        lc_messages = self._format_messages(messages, system)
        response = await self.llm.ainvoke(lc_messages)
        return response.content

    async def chat_stream(
        self, messages: list[dict], system: str | None = None
    ) -> AsyncIterator[str]:
        """Generate a streaming chat completion."""
        lc_messages = self._format_messages(messages, system)

        async for chunk in self.llm.astream(lc_messages):
            if chunk.content:
                yield chunk.content

    def get_llm(self) -> BaseChatModel:
        """Get the underlying LangChain LLM for advanced usage."""
        return self.llm


def get_llm_service(provider: LLMProvider | None = None) -> LLMService:
    """Get an LLM service instance."""
    return LLMService(provider)
