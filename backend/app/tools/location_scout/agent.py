"""Location Scout Agent using LangChain with tool calling capabilities."""

import json
from typing import AsyncIterator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.prebuilt import create_react_agent

from .agent_tools import LOCATION_SCOUT_TOOLS
from .prompts import SYSTEM_PROMPT
from ...core.llm import get_llm_service


AGENT_SYSTEM_PROMPT = """You are a location analysis expert helping small business owners evaluate potential locations for their business. You have access to Google Maps tools to gather real data about locations.

Your available tools are:
1. **geocode_address**: Convert addresses to coordinates and verify addresses
2. **search_nearby_places**: Find specific types of places near a location
3. **get_place_details**: Get detailed info about a specific place
4. **discover_neighborhood**: Get comprehensive neighborhood analysis (competitors, transit, foot traffic)

**How to help users:**

1. When a user asks about a location for their business, use the `discover_neighborhood` tool first to get comprehensive data.

2. If the user asks about specific aspects (e.g., "what restaurants are nearby?"), use the appropriate specific tool.

3. Always analyze the data you receive and provide actionable insights:
   - Competition level and quality
   - Foot traffic potential
   - Transit accessibility
   - Overall recommendation

4. Be honest and balanced. If a location has concerns, communicate them clearly while remaining constructive.

5. Format your responses clearly with sections when providing analysis.

**Important:**
- Always use tools to get real data rather than making assumptions
- If you need coordinates for a location, geocode it first
- Provide a score from 1-10 when giving location recommendations
"""


class LocationScoutAgent:
    """Agent that uses LangChain tools to analyze business locations."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.get_llm()
        self.tools = LOCATION_SCOUT_TOOLS
        self._agent = None

    def _get_agent(self):
        """Create or return the LangGraph ReAct agent."""
        if self._agent is None:
            # Create the agent with tools
            self._agent = create_react_agent(
                model=self.llm,
                tools=self.tools,
                state_modifier=AGENT_SYSTEM_PROMPT,
            )
        return self._agent

    async def process(self, query: str, conversation_history: list[dict] | None = None) -> str:
        """Process a query using the agent with tools."""
        agent = self._get_agent()

        # Build message history
        messages = []
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Add current query
        messages.append(HumanMessage(content=query))

        # Run the agent
        result = await agent.ainvoke({"messages": messages})

        # Extract the final response
        final_message = result["messages"][-1]
        return final_message.content

    async def process_stream(
        self, query: str, conversation_history: list[dict] | None = None
    ) -> AsyncIterator[str]:
        """Process a query using the agent with streaming."""
        agent = self._get_agent()

        # Build message history
        messages = []
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Add current query
        messages.append(HumanMessage(content=query))

        # Track what we've yielded
        current_tool_call = None
        streamed_content = []

        # Stream the agent execution
        async for event in agent.astream_events(
            {"messages": messages},
            version="v2",
        ):
            kind = event["event"]

            # Handle tool calls - show the user what tool is being called
            if kind == "on_tool_start":
                tool_name = event["name"]
                tool_input = event.get("data", {}).get("input", {})
                current_tool_call = tool_name

                # Format a nice message about what tool is being used
                if tool_name == "geocode_address":
                    address = tool_input.get("address", "")
                    yield f"\n**Looking up address:** {address}\n"
                elif tool_name == "search_nearby_places":
                    keyword = tool_input.get("keyword", "")
                    place_type = tool_input.get("place_type", "")
                    search_term = keyword or place_type or "places"
                    yield f"\n**Searching for {search_term} nearby...**\n"
                elif tool_name == "get_place_details":
                    yield f"\n**Getting detailed information...**\n"
                elif tool_name == "discover_neighborhood":
                    address = tool_input.get("address", "")
                    business = tool_input.get("business_type", "")
                    if business:
                        yield f"\n**Analyzing neighborhood for {business} at {address}...**\n"
                    else:
                        yield f"\n**Discovering neighborhood: {address}...**\n"

            # Handle tool results - summarize the results
            elif kind == "on_tool_end":
                tool_output = event.get("data", {}).get("output", "")
                if isinstance(tool_output, dict):
                    # Provide a brief summary of what was found
                    if (
                        current_tool_call == "discover_neighborhood"
                        and "analysis_summary" in tool_output
                    ):
                        summary = tool_output["analysis_summary"]
                        yield f"\n*Found {summary.get('competitor_count', 0)} competitors, "
                        yield f"transit access: {'Yes' if summary.get('transit_access') else 'No'}, "
                        yield f"foot traffic indicators: {summary.get('foot_traffic_indicators', 0)}*\n\n"
                    elif current_tool_call == "search_nearby_places" and isinstance(
                        tool_output, list
                    ):
                        yield f"\n*Found {len(tool_output)} places*\n\n"
                    elif "error" in tool_output:
                        yield f"\n*Error: {tool_output['error']}*\n\n"
                current_tool_call = None

            # Stream the LLM's response
            elif kind == "on_chat_model_stream":
                content = event.get("data", {}).get("chunk", {})
                if hasattr(content, "content") and content.content:
                    # Only yield if it's actual text content (not tool calls)
                    if isinstance(content.content, str):
                        streamed_content.append(content.content)
                        yield content.content


def get_location_scout_agent() -> LocationScoutAgent:
    """Get a Location Scout agent instance."""
    return LocationScoutAgent()
