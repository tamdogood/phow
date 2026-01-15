from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict
from typing import AsyncIterator, Any


class ToolContext(BaseModel):
    """Context passed to tools during processing."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    session_id: str
    conversation_id: str
    business_type: str | None = None
    business_profile: dict | None = None  # Full business profile data
    tracking_service: Any | None = None  # TrackingService, avoid circular import


class ToolResponse(BaseModel):
    """Response from a tool."""

    message: str
    data: dict | None = None
    follow_up_questions: list[str] | None = None


class BaseTool(ABC):
    """Base class for all tools."""

    tool_id: str
    name: str
    description: str
    icon: str = "🔧"
    hints: list[str] = []  # Example queries for this tool
    capabilities: list[str] = []  # What this tool can do

    @abstractmethod
    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a user query and return a response."""
        pass

    @abstractmethod
    async def process_stream(self, query: str, context: ToolContext) -> AsyncIterator[str]:
        """Process a user query and stream the response."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this tool."""
        pass
