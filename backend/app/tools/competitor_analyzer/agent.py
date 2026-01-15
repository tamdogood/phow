"""Competitor Analyzer Agent using LangChain with tool calling capabilities."""

import json
import time
from typing import AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from .agent_tools import COMPETITOR_ANALYZER_TOOLS
from ...core.llm import get_llm_service
from ...core.logging import get_logger

logger = get_logger("agent.competitor_analyzer")


AGENT_SYSTEM_PROMPT = """You are a competitive intelligence expert helping small business owners understand their competition and find ways to differentiate their business.

Your available tools are:
1. **find_competitors**: Discover all competitors near a location
2. **get_competitor_details**: Get detailed info about a specific competitor
3. **analyze_competitor_reviews**: Analyze reviews to find strengths/weaknesses
4. **create_positioning_map**: Create a price vs. quality positioning analysis

**How to help users:**

1. When asked about competitors, start with `find_competitors` to get an overview.

2. For deeper analysis, use:
   - `analyze_competitor_reviews` to understand what customers like/dislike
   - `create_positioning_map` to visualize the competitive landscape
   - `get_competitor_details` for specific competitor deep-dives

3. Always provide actionable insights:
   - How can they differentiate from competitors?
   - What gaps exist in the market?
   - What are competitors doing well that they should learn from?
   - What are competitors doing poorly that creates opportunity?

4. Format your analysis with clear sections:
   - **Competitive Landscape**: Overview of competitors found (total count)
   - **Top Competitors Analysis**: Detailed breakdown of the TOP 5-10 competitors by review count/ratings
   - **Market Gaps**: Opportunities for differentiation
   - **Recommendations**: Specific strategic advice

5. Be specific and data-driven:
   - Quote actual ratings and review counts
   - Reference specific themes from reviews
   - Provide concrete positioning suggestions

**CRITICAL - Multi-Competitor Analysis:**
- When `find_competitors` returns multiple competitors, you MUST analyze ALL of the top 5-10 competitors in your response, not just 1
- For each top competitor, provide: name, rating, review count, price level (if available), and key observations
- Compare and contrast competitors to identify patterns
- The user expects a comprehensive competitive landscape view, not a single competitor spotlight

**Important:**
- Always use tools to gather real data
- Be honest about competitive threats
- Focus on actionable differentiation strategies
- Help users understand HOW to compete, not just WHO they're competing against
"""


class CompetitorAnalyzerAgent:
    """Agent that analyzes competitors for business locations."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.get_llm()
        self.tools = COMPETITOR_ANALYZER_TOOLS
        self._agent = None

    def _get_agent(self):
        """Create or return the LangGraph ReAct agent."""
        if self._agent is None:
            logger.info(
                "Creating new Competitor Analyzer agent",
                tools=[t.name for t in self.tools],
            )
            self._agent = create_react_agent(self.llm, self.tools)
        return self._agent

    def _build_messages(self, query: str, conversation_history: list[dict] | None = None) -> list:
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

    async def process(self, query: str, conversation_history: list[dict] | None = None) -> str:
        """Process a query using the agent with tools."""
        logger.info("Processing competitor analysis query", query=query[:100])
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
        logger.info("Processing competitor analysis query (streaming)", query=query[:100])
        agent = self._get_agent()
        messages = self._build_messages(query, conversation_history)

        last_ai_content = None
        tool_activities: dict[str, dict] = {}

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
                                    logger.info(
                                        "Tool call started",
                                        tool=tool_name,
                                        args=tool_args,
                                    )

                                    # Track tool activity
                                    if tracking_service and session_id:
                                        activity_id = await tracking_service.start_tool_activity(
                                            session_id=session_id,
                                            tool_id="competitor_analyzer",
                                            tool_name=tool_name,
                                            input_args=tool_args,
                                            conversation_id=conversation_id,
                                        )
                                        tool_activities[tool_name] = {
                                            "id": activity_id,
                                            "start_time": time.time(),
                                        }

                                    # Log tool activity (status messages removed from user-facing output)
                                    logger.debug(
                                        "Tool execution started",
                                        tool=tool_name,
                                        args=tool_args,
                                    )

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

                            # Extract competitor data for the frontend widget
                            if tool_name == "find_competitors":
                                try:
                                    tool_result = (
                                        msg.content
                                        if isinstance(msg.content, dict)
                                        else json.loads(msg.content)
                                    )
                                    if "competitors" in tool_result and "error" not in tool_result:
                                        competitor_data = {
                                            "type": "competitor_data",
                                            "location": tool_result.get("location"),
                                            "business_type": tool_result.get("business_type"),
                                            "total_found": tool_result.get("total_found"),
                                            "competitors": tool_result.get("competitors", [])[:10],
                                            "sources": tool_result.get("sources", {}),
                                        }
                                        yield f"\n<!--COMPETITOR_DATA:{json.dumps(competitor_data)}-->\n"
                                        logger.info(
                                            "Yielded competitor data for widget",
                                            count=len(competitor_data["competitors"]),
                                        )
                                except (json.JSONDecodeError, TypeError, KeyError) as e:
                                    logger.warning(
                                        "Could not extract competitor data",
                                        error=str(e),
                                    )

                            # Extract positioning data for the frontend widget
                            elif tool_name == "create_positioning_map":
                                try:
                                    tool_result = (
                                        msg.content
                                        if isinstance(msg.content, dict)
                                        else json.loads(msg.content)
                                    )
                                    if (
                                        "positioning_data" in tool_result
                                        and "error" not in tool_result
                                    ):
                                        positioning_data = {
                                            "type": "positioning_data",
                                            "location": tool_result.get("location"),
                                            "business_type": tool_result.get("business_type"),
                                            "positioning_data": tool_result.get(
                                                "positioning_data", []
                                            ),
                                            "quadrant_analysis": tool_result.get(
                                                "quadrant_analysis", {}
                                            ),
                                            "market_gaps": tool_result.get("market_gaps", []),
                                            "recommendation": tool_result.get("recommendation"),
                                        }
                                        yield f"\n<!--POSITIONING_DATA:{json.dumps(positioning_data)}-->\n"
                                        logger.info("Yielded positioning data for widget")
                                except (json.JSONDecodeError, TypeError, KeyError) as e:
                                    logger.warning(
                                        "Could not extract positioning data",
                                        error=str(e),
                                    )

                            # Complete tool activity tracking
                            if tracking_service and tool_name in tool_activities:
                                activity = tool_activities.pop(tool_name)
                                latency_ms = int((time.time() - activity["start_time"]) * 1000)
                                await tracking_service.complete_tool_activity(
                                    activity_id=activity["id"],
                                    output_data={"result_length": len(str(msg.content))},
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
            logger.error("Error in agent stream", error=str(e), error_type=type(e).__name__)
            raise


def get_competitor_analyzer_agent() -> CompetitorAnalyzerAgent:
    """Get a Competitor Analyzer agent instance."""
    return CompetitorAnalyzerAgent()
