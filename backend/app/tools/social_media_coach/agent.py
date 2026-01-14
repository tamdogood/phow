"""Social Media Coach Agent using LangChain with tool calling capabilities."""

import json
import time
from typing import AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from .agent_tools import SOCIAL_MEDIA_COACH_TOOLS
from .prompts import SYSTEM_PROMPT
from ...core.llm import get_llm_service
from ...core.logging import get_logger

logger = get_logger("agent.social_media_coach")


class SocialMediaCoachAgent:
    """Agent that helps small business owners create social media content."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.get_llm()
        self.tools = SOCIAL_MEDIA_COACH_TOOLS
        self._agent = None

    def _get_agent(self):
        """Create or return the LangGraph ReAct agent."""
        if self._agent is None:
            logger.info("Creating new Social Media Coach agent", tools=[t.name for t in self.tools])
            self._agent = create_react_agent(self.llm, self.tools)
        return self._agent

    def _build_messages(
        self, query: str, conversation_history: list[dict] | None = None
    ) -> list:
        """Build message list with system prompt."""
        messages = [SystemMessage(content=SYSTEM_PROMPT)]
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
        logger.info("Processing social media coach query", query=query[:100])
        agent = self._get_agent()
        messages = self._build_messages(query, conversation_history)

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
        logger.info("Processing social media coach query (streaming)", query=query[:100])
        agent = self._get_agent()
        messages = self._build_messages(query, conversation_history)

        last_ai_content = None
        tool_activities: dict[str, dict] = {}
        collected_data = {
            "location": None,
            "weather": None,
            "events": None,
            "hashtags": None,
            "posting_times": None,
        }

        try:
            async for chunk in agent.astream({"messages": messages}, stream_mode="updates"):
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
                                    logger.info("Tool call started", tool=tool_name, args=tool_args)

                                    # Track tool activity
                                    if tracking_service and session_id:
                                        activity_id = await tracking_service.start_tool_activity(
                                            session_id=session_id,
                                            tool_id="social_media_coach",
                                            tool_name=tool_name,
                                            input_args=tool_args,
                                            conversation_id=conversation_id,
                                        )
                                        tool_activities[tool_name] = {"id": activity_id, "start_time": time.time()}

                            elif msg.content:
                                logger.info("Received final AI response", content_length=len(msg.content))
                                last_ai_content = msg.content

                        elif isinstance(msg, ToolMessage):
                            tool_name = msg.name
                            logger.info("Tool call completed", tool=tool_name, content_length=len(str(msg.content)))

                            # Collect data from tool results
                            try:
                                tool_result = msg.content if isinstance(msg.content, dict) else json.loads(msg.content)

                                if tool_name == "get_location_context" and "error" not in tool_result:
                                    collected_data["location"] = tool_result
                                elif tool_name == "get_weather_and_impact" and "error" not in tool_result:
                                    collected_data["weather"] = tool_result
                                elif tool_name == "get_upcoming_events_and_holidays" and "error" not in tool_result:
                                    collected_data["events"] = tool_result
                                elif tool_name == "get_trending_hashtags":
                                    collected_data["hashtags"] = tool_result
                                elif tool_name == "get_best_posting_times":
                                    collected_data["posting_times"] = tool_result

                            except (json.JSONDecodeError, TypeError) as e:
                                logger.warning("Could not parse tool result", tool=tool_name, error=str(e))

                            # Complete tool activity tracking
                            if tracking_service and tool_name in tool_activities:
                                activity = tool_activities.pop(tool_name)
                                latency_ms = int((time.time() - activity["start_time"]) * 1000)
                                await tracking_service.complete_tool_activity(
                                    activity_id=activity["id"],
                                    output_data={"result_length": len(str(msg.content))},
                                    latency_ms=latency_ms,
                                )

            # Emit widget data if we have enough context
            if collected_data["location"] or collected_data["weather"]:
                widget_data = {
                    "type": "social_content",
                    "location": collected_data["location"],
                    "weather": collected_data["weather"],
                    "events": collected_data["events"],
                    "hashtags": collected_data["hashtags"],
                    "posting_times": collected_data["posting_times"],
                }
                yield f"\n<!--SOCIAL_CONTENT_DATA:{json.dumps(widget_data)}-->\n"
                logger.info("Yielded social content data for widget")

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
            logger.error("Error in agent stream", error=str(e), error_type=type(e).__name__)
            raise


def get_social_media_coach_agent() -> SocialMediaCoachAgent:
    """Get a Social Media Coach agent instance."""
    return SocialMediaCoachAgent()
