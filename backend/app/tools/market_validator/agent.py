"""Market Validator Agent using LangChain with tool calling capabilities."""

import json
import time
from typing import AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from .agent_tools import MARKET_VALIDATOR_TOOLS
from ...core.llm import get_llm_service
from ...core.logging import get_logger

logger = get_logger("agent.market_validator")


AGENT_SYSTEM_PROMPT = """You are a market validation expert helping small business owners assess the viability of their business ideas at specific locations. You have access to tools that gather real demographic, competition, and foot traffic data.

Your available tools are:
1. **get_location_demographics**: Get Census demographic data (population, income, age, education)
2. **analyze_competition_density**: Find and analyze competitors in the area
3. **assess_foot_traffic_potential**: Evaluate foot traffic based on nearby businesses and transit
4. **calculate_market_viability**: Get comprehensive viability score combining all factors

**How to help users:**

1. When a user asks about market viability for a location, use the `calculate_market_viability` tool first - it provides a comprehensive analysis.

2. If the user wants more details on specific aspects:
   - Demographics questions → use `get_location_demographics`
   - Competition questions → use `analyze_competition_density`
   - Foot traffic questions → use `assess_foot_traffic_potential`

3. Always explain your findings in business terms:
   - What does the viability score mean for their business?
   - Are the demographics a good fit for their target customers?
   - How should they think about the competition level?
   - What opportunities and risks should they consider?

4. Provide actionable advice:
   - If the score is high, explain why it's a good opportunity
   - If the score is low, suggest what they might do differently or alternative approaches
   - Always mention the key factors driving the score

5. Format your responses with clear sections:
   - **Viability Score**: X/100 (Level)
   - **Key Findings**: Bullet points of main insights
   - **Demographics**: Brief summary
   - **Competition**: Brief summary
   - **Foot Traffic**: Brief summary
   - **Recommendation**: Clear guidance

**Important:**
- Always use tools to get real data - don't make assumptions
- Be honest about limitations (e.g., if an area has limited data)
- Balance optimism with realism - help users make informed decisions
"""


class MarketValidatorAgent:
    """Agent that uses tools to validate market potential for business locations."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.get_llm()
        self.tools = MARKET_VALIDATOR_TOOLS
        self._agent = None

    def _get_agent(self):
        """Create or return the LangGraph ReAct agent."""
        if self._agent is None:
            logger.info(
                "Creating new Market Validator agent",
                tools=[t.name for t in self.tools],
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
        logger.info("Processing market validation query", query=query[:100])
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
        logger.info("Processing market validation query (streaming)", query=query[:100])
        agent = self._get_agent()
        messages = self._build_messages(query, conversation_history)

        last_ai_content = None
        tool_activities: dict[str, dict] = {}

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
                                                tool_id="market_validator",
                                                tool_name=tool_name,
                                                input_args=tool_args,
                                                conversation_id=conversation_id,
                                            )
                                        )
                                        tool_activities[tool_name] = {
                                            "id": activity_id,
                                            "start_time": time.time(),
                                        }

                                    # Yield progress messages
                                    if tool_name == "get_location_demographics":
                                        address = tool_args.get("address", "location")
                                        yield f"\n**Analyzing demographics for {address}...**\n"
                                    elif tool_name == "analyze_competition_density":
                                        business_type = tool_args.get(
                                            "business_type", "business"
                                        )
                                        yield f"\n**Scanning for {business_type} competitors...**\n"
                                    elif tool_name == "assess_foot_traffic_potential":
                                        yield "\n**Evaluating foot traffic potential...**\n"
                                    elif tool_name == "calculate_market_viability":
                                        business_type = tool_args.get(
                                            "business_type", "business"
                                        )
                                        address = tool_args.get("address", "")
                                        yield f"\n**Calculating market viability for {business_type} at {address}...**\n"

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

                            # Extract market data for the frontend widget
                            if tool_name == "calculate_market_viability":
                                try:
                                    tool_result = (
                                        msg.content
                                        if isinstance(msg.content, dict)
                                        else json.loads(msg.content)
                                    )
                                    if (
                                        "viability_score" in tool_result
                                        and "error" not in tool_result
                                    ):
                                        market_data = {
                                            "type": "market_data",
                                            "location": tool_result.get("location"),
                                            "business_type": tool_result.get(
                                                "business_type"
                                            ),
                                            "viability_score": tool_result.get(
                                                "viability_score"
                                            ),
                                            "viability_level": tool_result.get(
                                                "viability_level"
                                            ),
                                            "score_breakdown": tool_result.get(
                                                "score_breakdown"
                                            ),
                                            "demographics_summary": tool_result.get(
                                                "demographics_summary"
                                            ),
                                            "competition_summary": tool_result.get(
                                                "competition_summary"
                                            ),
                                            "foot_traffic_summary": tool_result.get(
                                                "foot_traffic_summary"
                                            ),
                                            "risk_factors": tool_result.get(
                                                "risk_factors", []
                                            ),
                                            "opportunities": tool_result.get(
                                                "opportunities", []
                                            ),
                                            "recommendations": tool_result.get(
                                                "recommendations", []
                                            ),
                                            "top_competitors": tool_result.get(
                                                "top_competitors", []
                                            )[:5],
                                        }
                                        yield f"\n<!--MARKET_DATA:{json.dumps(market_data)}-->\n"
                                        logger.info(
                                            "Yielded market data for widget",
                                            score=tool_result["viability_score"],
                                        )
                                except (json.JSONDecodeError, TypeError, KeyError) as e:
                                    logger.warning(
                                        "Could not extract market data", error=str(e)
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


def get_market_validator_agent() -> MarketValidatorAgent:
    """Get a Market Validator agent instance."""
    return MarketValidatorAgent()
