from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tools.base import BaseTool


class ToolRegistry:
    """Registry for managing available tools."""

    _tools: dict[str, "BaseTool"] = {}

    @classmethod
    def register(cls, tool: "BaseTool") -> None:
        """Register a tool with the registry."""
        cls._tools[tool.tool_id] = tool

    @classmethod
    def get(cls, tool_id: str) -> "BaseTool | None":
        """Get a tool by its ID."""
        return cls._tools.get(tool_id)

    @classmethod
    def list_tools(cls) -> list[dict]:
        """List all registered tools."""
        return [
            {
                "id": tool.tool_id,
                "name": tool.name,
                "description": tool.description,
                "icon": tool.icon,
            }
            for tool in cls._tools.values()
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear all registered tools (useful for testing)."""
        cls._tools = {}
