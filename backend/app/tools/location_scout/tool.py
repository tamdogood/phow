import json
import re
from typing import AsyncIterator
from langchain_core.prompts import ChatPromptTemplate
from ..base import BaseTool, ToolContext, ToolResponse
from .prompts import SYSTEM_PROMPT, ANALYSIS_TEMPLATE
from ...core.llm import get_llm_service
from ...services.location_service import LocationService


class LocationScoutTool(BaseTool):
    """Tool for analyzing business locations with LangChain integration."""

    tool_id = "location_scout"
    name = "Location Scout"
    description = "Analyze if a location is good for your business. Get insights on competition, foot traffic, and accessibility."
    icon = "📍"

    def __init__(self):
        self.location_service = LocationService()
        self.llm_service = get_llm_service()

    def get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def _extract_location_and_business(
        self, query: str
    ) -> tuple[str | None, str | None]:
        """Extract location and business type from user query using LLM."""
        # Use a simple LLM call to extract structured data
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract the address and business type from the user's query.
Return JSON with keys 'address' and 'business_type'.
If either is not found, use null for that key.

Examples:
Query: "Is 123 Main St, Austin TX good for a coffee shop?"
Output: {{"address": "123 Main St, Austin TX", "business_type": "coffee shop"}}

Query: "Should I open a bakery at 456 Oak Ave, Seattle WA?"
Output: {{"address": "456 Oak Ave, Seattle WA", "business_type": "bakery"}}"""),
            ("user", "{query}")
        ])

        # Fallback to regex if LLM extraction fails
        query_lower = query.lower()
        business_patterns = [
            r"(?:for|open|start|run)\s+(?:a|an|my)\s+([a-zA-Z\s]+?)(?:\s+at|\s+in|\s+on|\?|$)",
            r"([a-zA-Z\s]+?)\s+(?:at|in|on)\s+",
        ]

        business_type = None
        for pattern in business_patterns:
            match = re.search(pattern, query_lower)
            if match:
                business_type = match.group(1).strip()
                break

        address_patterns = [
            r"(\d+\s+[a-zA-Z\s]+(?:street|st|avenue|ave|road|rd|blvd|boulevard|drive|dr|lane|ln|way)[,\s]+[a-zA-Z\s]+)",
            r"(?:at|in|on)\s+([^?]+?)(?:\s+good|\s+for|\?|$)",
        ]

        address = None
        for pattern in address_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                address = match.group(1).strip().rstrip(",. ")
                break

        return address, business_type

    def _format_places_list(self, places: list[dict]) -> str:
        """Format a list of places for the prompt."""
        if not places:
            return "None found"

        lines = []
        for place in places[:10]:
            rating = f"Rating: {place.get('rating', 'N/A')}" if place.get('rating') else ""
            reviews = f"({place.get('user_ratings_total', 0)} reviews)" if place.get('user_ratings_total') else ""
            lines.append(f"- {place['name']} {rating} {reviews}".strip())
        return "\n".join(lines)

    async def process(self, query: str, context: ToolContext) -> ToolResponse:
        """Process a location analysis request."""
        # Extract location and business type
        address, business_type = self._extract_location_and_business(query)

        # Use context business type if not extracted
        if not business_type and context.business_type:
            business_type = context.business_type

        # If we couldn't extract necessary info, ask for clarification
        if not address:
            return ToolResponse(
                message="I'd be happy to analyze a location for you! Could you please provide the address you'd like me to analyze? For example: 'Is 123 Main St, Austin TX good for a coffee shop?'",
                follow_up_questions=[
                    "What address would you like me to analyze?",
                    "What type of business are you considering?",
                ],
            )

        if not business_type:
            return ToolResponse(
                message=f"I found the address: {address}. What type of business are you considering opening there?",
                follow_up_questions=[
                    "What type of business are you planning?",
                ],
            )

        # Get location data using the service layer (with caching)
        location_data = await self.location_service.analyze_location(
            address, business_type
        )

        if "error" in location_data:
            return ToolResponse(
                message=f"I couldn't find that address. Please check the address and try again. Error: {location_data['error']}",
            )

        # Format the prompt
        prompt = ANALYSIS_TEMPLATE.format(
            business_type=business_type,
            address=location_data["location"]["formatted_address"],
            location_data=json.dumps(location_data["location"], indent=2),
            competitor_count=location_data["analysis_summary"]["competitor_count"],
            competitors=self._format_places_list(location_data["competitors"]),
            transit="Yes - " + self._format_places_list(location_data["transit_stations"])
            if location_data["transit_stations"]
            else "No nearby transit stations found",
            foot_traffic_count=location_data["analysis_summary"]["foot_traffic_indicators"],
            foot_traffic=self._format_places_list(
                location_data["nearby_food"][:5] + location_data["nearby_retail"][:5]
            ),
        )

        # Get LLM analysis using LangChain
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm_service.chat(messages, system=self.get_system_prompt())

        return ToolResponse(
            message=response,
            data={
                "location": location_data["location"],
                "competitor_count": location_data["analysis_summary"]["competitor_count"],
                "has_transit": location_data["analysis_summary"]["transit_access"],
                "foot_traffic_score": min(
                    10, location_data["analysis_summary"]["foot_traffic_indicators"]
                ),
            },
            follow_up_questions=[
                "Would you like me to analyze a different location?",
                "Should I look at a wider or narrower area?",
                "Would you like more details about the competitors?",
            ],
        )

    async def process_stream(
        self, query: str, context: ToolContext
    ) -> AsyncIterator[str]:
        """Process a location analysis request with streaming."""
        # Extract location and business type
        address, business_type = self._extract_location_and_business(query)

        if not business_type and context.business_type:
            business_type = context.business_type

        if not address:
            yield "I'd be happy to analyze a location for you! Could you please provide the address you'd like me to analyze? For example: 'Is 123 Main St, Austin TX good for a coffee shop?'"
            return

        if not business_type:
            yield f"I found the address: {address}. What type of business are you considering opening there?"
            return

        yield f"Analyzing {address} for a {business_type}...\n\n"

        # Get location data using service layer (with caching)
        location_data = await self.location_service.analyze_location(
            address, business_type
        )

        if "error" in location_data:
            yield f"I couldn't find that address. Please check and try again."
            return

        yield f"Found location: {location_data['location']['formatted_address']}\n"
        yield f"Gathering data on competitors, transit, and foot traffic...\n\n"

        # Format prompt
        prompt = ANALYSIS_TEMPLATE.format(
            business_type=business_type,
            address=location_data["location"]["formatted_address"],
            location_data=json.dumps(location_data["location"], indent=2),
            competitor_count=location_data["analysis_summary"]["competitor_count"],
            competitors=self._format_places_list(location_data["competitors"]),
            transit="Yes - " + self._format_places_list(location_data["transit_stations"])
            if location_data["transit_stations"]
            else "No nearby transit stations found",
            foot_traffic_count=location_data["analysis_summary"]["foot_traffic_indicators"],
            foot_traffic=self._format_places_list(
                location_data["nearby_food"][:5] + location_data["nearby_retail"][:5]
            ),
        )

        # Stream LLM response using LangChain
        messages = [{"role": "user", "content": prompt}]
        async for chunk in self.llm_service.chat_stream(
            messages, system=self.get_system_prompt()
        ):
            yield chunk
