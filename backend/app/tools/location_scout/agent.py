"""Location Scout Agent using LangChain with tool calling capabilities."""

import json
import time
from typing import AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from .agent_tools import LOCATION_SCOUT_TOOLS
from ...core.llm import get_llm_service
from ...core.logging import get_logger

logger = get_logger("agent.location_scout")


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
            logger.info(
                "Creating new LangGraph ReAct agent", tools=[t.name for t in self.tools]
            )
            self._agent = create_react_agent(self.llm, self.tools)
        return self._agent

    def _build_messages(
        self, query: str, conversation_history: list[dict] | None = None
    ) -> list:
        """Build message list with system prompt."""
        messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)]
        if conversation_history:
            for msg in conversation_history:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=query))
        return messages

    async def process(
        self, query: str, conversation_history: list[dict] | None = None
    ) -> str:
        """Process a query using the agent with tools."""
        logger.info("Processing query", query=query[:100])
        agent = self._get_agent()
        messages = self._build_messages(query, conversation_history)
        logger.debug("Built messages", message_count=len(messages))

        result = await agent.ainvoke({"messages": messages})
        response = result["messages"][-1].content
        logger.info("Agent completed", response_length=len(response))
        return response

    async def process_stream(
        self,
        query: str,
        conversation_history: list[dict] | None = None,
        tracking_service: Any | None = None,
        session_id: str | None = None,
        conversation_id: str | None = None,
    ) -> AsyncIterator[str]:
        """Process a query using the agent with streaming."""
        logger.info("Processing query (streaming)", query=query[:100])
        agent = self._get_agent()
        messages = self._build_messages(query, conversation_history)
        logger.debug("Built messages", message_count=len(messages))

        last_ai_content = None
        tool_activities: dict[str, dict] = {}  # tool_name -> {id, start_time}

        try:
            async for chunk in agent.astream(
                {"messages": messages}, stream_mode="updates"
            ):
                for node_name, node_output in chunk.items():
                    logger.debug("Agent node update", node=node_name)

                    if "messages" not in node_output:
                        continue

                    for msg in node_output["messages"]:
                        if isinstance(msg, AIMessage):
                            if msg.tool_calls:
                                for tool_call in msg.tool_calls:
                                    tool_name = tool_call.get("name", "")
                                    tool_args = tool_call.get("args", {})
                                    logger.info(
                                        "Tool call started",
                                        tool=tool_name,
                                        args=tool_args,
                                    )

                                    # Track tool activity
                                    if tracking_service and session_id:
                                        activity_id = (
                                            await tracking_service.start_tool_activity(
                                                session_id=session_id,
                                                tool_id="location_scout",
                                                tool_name=tool_name,
                                                input_args=tool_args,
                                                conversation_id=conversation_id,
                                            )
                                        )
                                        tool_activities[tool_name] = {
                                            "id": activity_id,
                                            "start_time": time.time(),
                                        }

                                    if tool_name == "geocode_address":
                                        yield f"\n**Looking up address:** {tool_args.get('address', '')}\n"
                                    elif tool_name == "search_nearby_places":
                                        search_term = (
                                            tool_args.get("keyword")
                                            or tool_args.get("place_type")
                                            or "places"
                                        )
                                        yield f"\n**Searching for {search_term} nearby...**\n"
                                    elif tool_name == "get_place_details":
                                        yield "\n**Getting detailed information...**\n"
                                    elif tool_name == "discover_neighborhood":
                                        address = tool_args.get("address", "")
                                        business = tool_args.get("business_type", "")
                                        if business:
                                            yield f"\n**Analyzing neighborhood for {business} at {address}...**\n"
                                        else:
                                            yield f"\n**Discovering neighborhood: {address}...**\n"
                            elif msg.content:
                                logger.info(
                                    "Received final AI response",
                                    content_length=len(msg.content),
                                )
                                last_ai_content = msg.content

                        elif isinstance(msg, ToolMessage):
                            tool_name = msg.name
                            logger.info(
                                "Tool call completed",
                                tool=tool_name,
                                content_length=len(str(msg.content)),
                            )

                            # Extract location data for the frontend map
                            if tool_name == "discover_neighborhood":
                                try:
                                    tool_result = (
                                        msg.content
                                        if isinstance(msg.content, dict)
                                        else json.loads(msg.content)
                                    )
                                    if (
                                        "location" in tool_result
                                        and "error" not in tool_result
                                    ):
                                        location_data = {
                                            "type": "location_data",
                                            "location": tool_result["location"],
                                            "competitors": tool_result.get(
                                                "competitors", []
                                            )[:5],
                                            "transit_stations": tool_result.get(
                                                "transit_stations", []
                                            )[:3],
                                            "nearby_food": tool_result.get(
                                                "nearby_food", []
                                            )[:5],
                                            "nearby_retail": tool_result.get(
                                                "nearby_retail", []
                                            )[:5],
                                            "analysis_summary": tool_result.get(
                                                "analysis_summary", {}
                                            ),
                                        }
                                        yield f"\n<!--LOCATION_DATA:{json.dumps(location_data)}-->\n"
                                        logger.info(
                                            "Yielded location data for map",
                                            lat=tool_result["location"]["lat"],
                                        )
                                except (json.JSONDecodeError, TypeError, KeyError) as e:
                                    logger.warning(
                                        "Could not extract location data", error=str(e)
                                    )

                            # Complete tool activity tracking
                            if tracking_service and tool_name in tool_activities:
                                activity = tool_activities.pop(tool_name)
                                latency_ms = int(
                                    (time.time() - activity["start_time"]) * 1000
                                )
                                await tracking_service.complete_tool_activity(
                                    activity_id=activity["id"],
                                    output_data={
                                        "result_length": len(str(msg.content))
                                    },
                                    latency_ms=latency_ms,
                                )

            if last_ai_content:
                logger.debug("Streaming final response")
                yield "\n"
                yield last_ai_content
            else:
                logger.warning("No final AI content received")

        except Exception as e:
            # Mark any in-progress tool activities as failed
            if tracking_service:
                for tool_name, activity in tool_activities.items():
                    latency_ms = int((time.time() - activity["start_time"]) * 1000)
                    await tracking_service.fail_tool_activity(
                        activity_id=activity["id"],
                        error_message=str(e),
                        latency_ms=latency_ms,
                    )
            logger.error(
                "Error in agent stream", error=str(e), error_type=type(e).__name__
            )
            raise


def get_location_scout_agent() -> LocationScoutAgent:
    """Get a Location Scout agent instance."""
    return LocationScoutAgent()
