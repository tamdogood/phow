"""Market Research Agent - Unified LangGraph agent with all market research tools."""

import json
import time
from typing import AsyncIterator, Any
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from .prompts import AGENT_SYSTEM_PROMPT
from .market_sizing_tools import MARKET_SIZING_TOOLS
from .economic_tools import ECONOMIC_TOOLS
from .competitive_intelligence_tools import COMPETITIVE_INTELLIGENCE_TOOLS
from .consumer_insights_tools import CONSUMER_INSIGHTS_TOOLS
from .financial_tools import FINANCIAL_TOOLS
from .report_tools import REPORT_TOOLS
from .widget_extractor import (
    create_market_size_widget,
    create_industry_widget,
    create_labor_market_widget,
    create_growth_projection_widget,
    create_economic_snapshot_widget,
    create_industry_trend_widget,
    create_seasonality_widget,
    create_entry_timing_widget,
    create_swot_widget,
    create_five_forces_widget,
    create_pricing_widget,
    create_market_share_widget,
    create_sentiment_widget,
    create_pain_points_widget,
    create_journey_widget,
    create_profile_widget,
    create_financial_projection_widget,
    create_break_even_widget,
    create_scenario_widget,
    create_viability_widget,
    create_executive_summary_widget,
    create_recommendations_widget,
)
from ..location_scout.agent_tools import LOCATION_SCOUT_TOOLS
from ..market_validator.agent_tools import MARKET_VALIDATOR_TOOLS
from ..competitor_analyzer.agent_tools import COMPETITOR_ANALYZER_TOOLS
from ...core.llm import get_llm_service
from ...core.logging import get_logger

logger = get_logger("agent.market_research")

# Combine all tools from all domains (44 tools across 9 domains)
MARKET_RESEARCH_TOOLS = (
    LOCATION_SCOUT_TOOLS
    + MARKET_VALIDATOR_TOOLS
    + COMPETITOR_ANALYZER_TOOLS
    + MARKET_SIZING_TOOLS
    + ECONOMIC_TOOLS
    + COMPETITIVE_INTELLIGENCE_TOOLS
    + CONSUMER_INSIGHTS_TOOLS
    + FINANCIAL_TOOLS
    + REPORT_TOOLS
)


class MarketResearchAgent:
    """Unified agent with all market research tools (44 tools across 9 domains)."""

    def __init__(self):
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.get_llm()
        self.tools = MARKET_RESEARCH_TOOLS
        self._agent = None

    def _get_agent(self):
        """Create or return the LangGraph ReAct agent."""
        if self._agent is None:
            logger.info(
                "Creating Market Research agent",
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
        logger.info("Processing market research query", query=query[:100])
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
        logger.info("Processing market research query (streaming)", query=query[:100])
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
                                    logger.info("Tool call started", tool=tool_name, args=tool_args)

                                    # Track tool activity
                                    if tracking_service and session_id:
                                        activity_id = await tracking_service.start_tool_activity(
                                            session_id=session_id,
                                            tool_id="market_research",
                                            tool_name=tool_name,
                                            input_args=tool_args,
                                            conversation_id=conversation_id,
                                        )
                                        tool_activities[tool_name] = {
                                            "id": activity_id,
                                            "start_time": time.time(),
                                        }

                                    # Yield progress messages based on tool type
                                    yield self._get_progress_message(tool_name, tool_args)

                            elif msg.content:
                                logger.info(
                                    "Received final AI response", content_length=len(msg.content)
                                )
                                last_ai_content = msg.content

                        elif isinstance(msg, ToolMessage):
                            tool_name = msg.name
                            logger.info(
                                "Tool call completed",
                                tool=tool_name,
                                content_length=len(str(msg.content)),
                            )

                            # Extract widget data based on tool type
                            widget_data = self._extract_widget_data(tool_name, msg.content)
                            if widget_data:
                                yield widget_data

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

    def _get_progress_message(self, tool_name: str, tool_args: dict) -> str:
        """Generate progress message for a tool call."""
        address = tool_args.get("address", "location")
        business_type = tool_args.get("business_type", "business")

        messages = {
            # Location Scout tools
            "geocode_address": f"\n**Geocoding {address}...**\n",
            "search_nearby_places": "\n**Searching for nearby places...**\n",
            "get_place_details": "\n**Getting place details...**\n",
            "discover_neighborhood": f"\n**Discovering neighborhood around {address}...**\n",
            # Market Validator tools
            "get_location_demographics": f"\n**Analyzing demographics for {address}...**\n",
            "analyze_competition_density": f"\n**Scanning for {business_type} competitors...**\n",
            "assess_foot_traffic_potential": "\n**Evaluating foot traffic potential...**\n",
            "calculate_market_viability": f"\n**Calculating market viability for {business_type}...**\n",
            # Competitor Analyzer tools
            "find_competitors": f"\n**Finding {business_type} competitors...**\n",
            "get_competitor_details": "\n**Getting competitor details...**\n",
            "analyze_competitor_reviews": "\n**Analyzing competitor reviews...**\n",
            "create_positioning_map": "\n**Creating competitive positioning map...**\n",
            # Market Sizing tools
            "calculate_market_size": f"\n**Calculating TAM/SAM/SOM for {business_type}...**\n",
            "get_industry_profile": f"\n**Building industry profile...**\n",
            "analyze_labor_market": f"\n**Analyzing labor market conditions...**\n",
            "project_market_growth": "\n**Projecting market growth...**\n",
            "get_market_sizing_summary": f"\n**Generating comprehensive market analysis...**\n",
            # Economic Intelligence tools
            "get_economic_indicators": "\n**Fetching economic indicators...**\n",
            "analyze_industry_trends": f"\n**Analyzing industry trends for {business_type}...**\n",
            "get_seasonality_pattern": f"\n**Analyzing seasonal patterns...**\n",
            "analyze_entry_timing": f"\n**Analyzing optimal entry timing...**\n",
            "get_consumer_spending_trends": "\n**Analyzing consumer spending trends...**\n",
            "get_economic_summary": f"\n**Generating economic intelligence summary...**\n",
            # Competitive Intelligence tools
            "generate_swot_analysis": f"\n**Generating SWOT analysis for {business_type}...**\n",
            "analyze_competitive_forces": f"\n**Analyzing Porter's Five Forces...**\n",
            "estimate_market_shares": f"\n**Estimating market share distribution...**\n",
            "analyze_pricing_landscape": f"\n**Analyzing pricing landscape...**\n",
            "benchmark_competitors": f"\n**Benchmarking against competitors...**\n",
            "get_competitive_intelligence_summary": f"\n**Generating competitive intelligence summary...**\n",
            # Consumer Insights tools
            "analyze_customer_sentiment": f"\n**Analyzing customer sentiment...**\n",
            "extract_customer_themes": f"\n**Extracting themes from reviews...**\n",
            "identify_customer_pain_points": f"\n**Identifying customer pain points...**\n",
            "map_customer_journey": f"\n**Mapping customer journey for {business_type}...**\n",
            "build_customer_profile": f"\n**Building customer profile...**\n",
            "get_consumer_insights_summary": f"\n**Generating consumer insights summary...**\n",
            # Financial tools
            "project_revenue": f"\n**Projecting revenue for {business_type}...**\n",
            "calculate_break_even": f"\n**Calculating break-even analysis...**\n",
            "run_financial_scenario": f"\n**Running financial scenario analysis...**\n",
            "assess_financial_viability": f"\n**Assessing financial viability...**\n",
            "get_financial_summary": f"\n**Generating financial summary...**\n",
            "get_industry_benchmarks": f"\n**Fetching industry benchmarks...**\n",
            # Report tools
            "generate_market_report": f"\n**Generating market report for {business_type}...**\n",
            "get_executive_summary": f"\n**Creating executive summary...**\n",
            "get_key_recommendations": f"\n**Generating key recommendations...**\n",
        }
        return messages.get(tool_name, f"\n**Running {tool_name}...**\n")

    def _extract_widget_data(self, tool_name: str, content: Any) -> str | None:
        """Extract and format widget data from tool results."""
        try:
            tool_result = content if isinstance(content, dict) else json.loads(content)
            if "error" in tool_result:
                return None

            # Location data (discover_neighborhood)
            if tool_name == "discover_neighborhood" and "location" in tool_result:
                location_data = {
                    "type": "location_data",
                    "location": tool_result.get("location"),
                    "competitors": tool_result.get("competitors", [])[:10],
                    "transit_stations": tool_result.get("transit_stations", [])[:5],
                    "nearby_food": tool_result.get("nearby_food", [])[:10],
                    "nearby_retail": tool_result.get("nearby_retail", [])[:10],
                    "analysis_summary": tool_result.get("analysis_summary", {}),
                }
                logger.info("Yielded location data", lat=tool_result["location"]["lat"])
                return f"\n<!--LOCATION_DATA:{json.dumps(location_data)}-->\n"

            # Market viability data
            if tool_name == "calculate_market_viability" and "viability_score" in tool_result:
                market_data = {
                    "type": "market_data",
                    "location": tool_result.get("location"),
                    "business_type": tool_result.get("business_type"),
                    "viability_score": tool_result.get("viability_score"),
                    "viability_level": tool_result.get("viability_level"),
                    "score_breakdown": tool_result.get("score_breakdown"),
                    "demographics_summary": tool_result.get("demographics_summary"),
                    "competition_summary": tool_result.get("competition_summary"),
                    "foot_traffic_summary": tool_result.get("foot_traffic_summary"),
                    "risk_factors": tool_result.get("risk_factors", []),
                    "opportunities": tool_result.get("opportunities", []),
                    "recommendations": tool_result.get("recommendations", []),
                    "top_competitors": tool_result.get("top_competitors", [])[:5],
                }
                logger.info("Yielded market data", score=tool_result["viability_score"])
                return f"\n<!--MARKET_DATA:{json.dumps(market_data)}-->\n"

            # Competitor data (find_competitors)
            if tool_name == "find_competitors" and "competitors" in tool_result:
                competitor_data = {
                    "type": "competitor_data",
                    "location": tool_result.get("location"),
                    "business_type": tool_result.get("business_type"),
                    "total_found": tool_result.get("total_found", 0),
                    "competitors": tool_result.get("competitors", [])[:10],
                    "sources": tool_result.get("sources", {}),
                }
                logger.info("Yielded competitor data", count=len(competitor_data["competitors"]))
                return f"\n<!--COMPETITOR_DATA:{json.dumps(competitor_data)}-->\n"

            # Positioning map data
            if tool_name == "create_positioning_map" and "positioning_data" in tool_result:
                positioning_data = {
                    "type": "positioning_data",
                    "location": tool_result.get("location"),
                    "business_type": tool_result.get("business_type"),
                    "total_competitors": tool_result.get("total_competitors", 0),
                    "positioning_data": tool_result.get("positioning_data", []),
                    "quadrant_analysis": tool_result.get("quadrant_analysis", {}),
                    "market_gaps": tool_result.get("market_gaps", []),
                    "recommendation": tool_result.get("recommendation", ""),
                }
                logger.info("Yielded positioning data", count=tool_result.get("total_competitors"))
                return f"\n<!--POSITIONING_DATA:{json.dumps(positioning_data)}-->\n"

            # Market size data (TAM/SAM/SOM)
            if tool_name in ["calculate_market_size", "get_market_sizing_summary"] and "tam" in tool_result:
                widget = create_market_size_widget(
                    tool_result.get("market_size", tool_result)
                )
                logger.info("Yielded market size data")
                return f"\n{widget}\n"

            # Industry profile data
            if tool_name == "get_industry_profile" and "industry_name" in tool_result:
                widget = create_industry_widget(tool_result)
                logger.info("Yielded industry profile data")
                return f"\n{widget}\n"

            # Labor market data
            if tool_name == "analyze_labor_market" and "workforce" in tool_result:
                widget = create_labor_market_widget(tool_result)
                logger.info("Yielded labor market data")
                return f"\n{widget}\n"

            # Growth projection data
            if tool_name == "project_market_growth" and "projections" in tool_result:
                widget = create_growth_projection_widget(tool_result)
                logger.info("Yielded growth projection data")
                return f"\n{widget}\n"

            # Economic snapshot data
            if tool_name in ["get_economic_indicators", "get_economic_summary"] and "indicators" in tool_result:
                widget = create_economic_snapshot_widget(
                    tool_result.get("economic_conditions", tool_result)
                )
                logger.info("Yielded economic data")
                return f"\n{widget}\n"

            # Industry trend data
            if tool_name == "analyze_industry_trends" and "trend_direction" in tool_result:
                widget = create_industry_trend_widget(tool_result)
                logger.info("Yielded industry trend data")
                return f"\n{widget}\n"

            # Seasonality data
            if tool_name == "get_seasonality_pattern" and "monthly_indices" in tool_result:
                widget = create_seasonality_widget(tool_result)
                logger.info("Yielded seasonality data")
                return f"\n{widget}\n"

            # Entry timing data
            if tool_name == "analyze_entry_timing" and "timing_score" in tool_result:
                widget = create_entry_timing_widget(tool_result)
                logger.info("Yielded entry timing data")
                return f"\n{widget}\n"

            # SWOT analysis data
            if tool_name == "generate_swot_analysis" and "strengths" in tool_result:
                widget = create_swot_widget(tool_result)
                logger.info("Yielded SWOT data")
                return f"\n{widget}\n"

            # Porter's Five Forces data
            if tool_name == "analyze_competitive_forces" and "forces" in tool_result:
                widget = create_five_forces_widget(tool_result)
                logger.info("Yielded Five Forces data")
                return f"\n{widget}\n"

            # Pricing landscape data
            if tool_name == "analyze_pricing_landscape" and "distribution" in tool_result:
                widget = create_pricing_widget(tool_result)
                logger.info("Yielded pricing data")
                return f"\n{widget}\n"

            # Market share data
            if tool_name == "estimate_market_shares" and "shares" in tool_result:
                widget = create_market_share_widget(tool_result)
                logger.info("Yielded market share data")
                return f"\n{widget}\n"

            # Competitive intelligence summary - extract SWOT
            if tool_name == "get_competitive_intelligence_summary" and "full_swot" in tool_result:
                widget = create_swot_widget(tool_result["full_swot"])
                logger.info("Yielded competitive intelligence SWOT data")
                return f"\n{widget}\n"

            # Sentiment analysis data
            if tool_name == "analyze_customer_sentiment" and "sentiment_label" in tool_result:
                widget = create_sentiment_widget(tool_result)
                logger.info("Yielded sentiment data")
                return f"\n{widget}\n"

            # Pain points data
            if tool_name == "identify_customer_pain_points" and "pain_points" in tool_result:
                widget = create_pain_points_widget(tool_result)
                logger.info("Yielded pain points data")
                return f"\n{widget}\n"

            # Customer journey data
            if tool_name == "map_customer_journey" and "journey_stages" in tool_result:
                widget = create_journey_widget(tool_result)
                logger.info("Yielded journey data")
                return f"\n{widget}\n"

            # Customer profile data
            if tool_name == "build_customer_profile" and "primary_persona" in tool_result:
                widget = create_profile_widget(tool_result)
                logger.info("Yielded profile data")
                return f"\n{widget}\n"

            # Consumer insights summary - extract sentiment
            if tool_name == "get_consumer_insights_summary" and "full_sentiment" in tool_result:
                widget = create_sentiment_widget(tool_result["full_sentiment"])
                logger.info("Yielded consumer insights sentiment data")
                return f"\n{widget}\n"

            # Revenue projection data
            if tool_name in ["project_revenue", "get_financial_summary"] and "projections" in tool_result or "revenue_scenarios" in tool_result:
                widget = create_financial_projection_widget(tool_result)
                logger.info("Yielded financial projection data")
                return f"\n{widget}\n"

            # Break-even data
            if tool_name == "calculate_break_even" and "break_even_revenue" in tool_result:
                widget = create_break_even_widget(tool_result)
                logger.info("Yielded break-even data")
                return f"\n{widget}\n"

            # Scenario comparison data
            if tool_name == "run_financial_scenario" and "impact" in tool_result:
                widget = create_scenario_widget(tool_result)
                logger.info("Yielded scenario data")
                return f"\n{widget}\n"

            # Financial viability data
            if tool_name == "assess_financial_viability" and "viability_score" in tool_result:
                widget = create_viability_widget(tool_result)
                logger.info("Yielded viability data")
                return f"\n{widget}\n"

            # Executive summary data
            if tool_name == "get_executive_summary" and "summary_paragraphs" in tool_result:
                widget = create_executive_summary_widget(tool_result)
                logger.info("Yielded executive summary data")
                return f"\n{widget}\n"

            # Recommendations data
            if tool_name == "get_key_recommendations" and "recommendations" in tool_result:
                widget = create_recommendations_widget(tool_result)
                logger.info("Yielded recommendations data")
                return f"\n{widget}\n"

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning("Could not extract widget data", tool=tool_name, error=str(e))

        return None


def get_market_research_agent() -> MarketResearchAgent:
    """Get a Market Research agent instance."""
    return MarketResearchAgent()
