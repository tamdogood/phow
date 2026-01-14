from fastapi import APIRouter
from ...core.tool_registry import ToolRegistry

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("")
async def list_tools():
    """List all available tools."""
    return ToolRegistry.list_tools()


@router.get("/{tool_id}")
async def get_tool(tool_id: str):
    """Get a specific tool by ID."""
    tool = ToolRegistry.get(tool_id)
    if not tool:
        return {"error": "Tool not found"}
    return {
        "id": tool.tool_id,
        "name": tool.name,
        "description": tool.description,
        "icon": tool.icon,
    }
