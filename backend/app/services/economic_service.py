"""Economic intelligence service for indicators, trends, and timing analysis."""

from typing import Any
from ..core.cache import cached
from ..core.logging import get_logger
from ..tools.market_research.fred_client import get_fred_client
from ..tools.market_research.gdelt_client import get_gdelt_client

logger = get_logger("economic_service")

# Regional economic indicators mapping
REGIONAL_SERIES = {
    "unemployment": "{state}UR",  # State unemployment rate
    "personal_income": "{state}OTOT",  # State total personal income
}

# Seasonality patterns by industry (monthly index, 1.0 = average)
# Based on typical retail/service industry patterns
INDUSTRY_SEASONALITY = {
    "722515": {  # Coffee shops
        1: 0.85, 2: 0.85, 3: 0.90, 4: 0.95, 5: 1.00, 6: 1.05,
        7: 1.00, 8: 1.00, 9: 1.10, 10: 1.10, 11: 1.05, 12: 1.15,
    },
    "722511": {  # Full-service restaurants
        1: 0.80, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.10, 6: 1.10,
        7: 1.05, 8: 1.05, 9: 0.95, 10: 1.00, 11: 1.05, 12: 1.10,
    },
    "722513": {  # Fast food
        1: 0.90, 2: 0.90, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.10,
        7: 1.10, 8: 1.05, 9: 0.95, 10: 1.00, 11: 1.00, 12: 0.95,
    },
    "713940": {  # Fitness centers
        1: 1.25, 2: 1.15, 3: 1.05, 4: 1.00, 5: 1.00, 6: 0.90,
        7: 0.85, 8: 0.85, 9: 1.00, 10: 1.00, 11: 0.95, 12: 0.90,
    },
    "812112": {  # Beauty salons
        1: 0.85, 2: 0.90, 3: 1.00, 4: 1.10, 5: 1.15, 6: 1.10,
        7: 0.95, 8: 0.90, 9: 1.00, 10: 1.05, 11: 1.05, 12: 0.95,
    },
    "445110": {  # Grocery stores
        1: 0.95, 2: 0.95, 3: 1.00, 4: 1.00, 5: 1.00, 6: 1.00,
        7: 1.05, 8: 1.05, 9: 1.00, 10: 1.00, 11: 1.00, 12: 1.05,
    },
    "default": {
        1: 0.90, 2: 0.90, 3: 0.95, 4: 1.00, 5: 1.05, 6: 1.05,
        7: 1.00, 8: 1.00, 9: 1.00, 10: 1.05, 11: 1.05, 12: 1.05,
    },
}


class EconomicService:
    """Service for economic indicators, trends, and timing intelligence."""

    def __init__(self):
        self.fred_client = get_fred_client()
        self.gdelt_client = get_gdelt_client()

    @cached(ttl=86400, key_prefix="economic_snapshot")
    async def get_economic_snapshot(self, region: str | None = None) -> dict[str, Any]:
        """
        Get current economic snapshot with key indicators.

        Args:
            region: Optional state code (e.g., "TX", "CA") for regional data

        Returns:
            Economic indicators with interpretations
        """
        # Get national indicators
        indicators = await self.fred_client.get_economic_indicators()

        snapshot = {
            "scope": region or "national",
            "indicators": {},
            "interpretation": {},
            "outlook": None,
        }

        # Process key indicators
        for name in ["gdp", "unemployment", "cpi", "consumer_confidence", "retail_sales"]:
            if name in indicators and "error" not in indicators[name]:
                ind_data = indicators[name]
                snapshot["indicators"][name] = {
                    "value": ind_data.get("value"),
                    "date": ind_data.get("date"),
                    "title": ind_data.get("title"),
                    "units": ind_data.get("units"),
                }

        # Add interpretations
        snapshot["interpretation"] = indicators.get("_interpretation", {})

        # Get regional unemployment if state specified
        if region:
            regional_data = await self._get_regional_indicators(region)
            snapshot["regional"] = regional_data

        # Generate overall outlook
        snapshot["outlook"] = self._generate_outlook(snapshot["indicators"])

        return snapshot

    async def _get_regional_indicators(self, state: str) -> dict[str, Any]:
        """Get regional economic indicators for a state."""
        regional = {}

        # State unemployment
        series_id = f"{state.upper()}UR"
        try:
            data = await self.fred_client.get_series(series_id, limit=12)
            if "error" not in data:
                regional["unemployment"] = {
                    "value": data.get("latest_value"),
                    "date": data.get("latest_date"),
                    "title": f"{state} Unemployment Rate",
                }
        except Exception as e:
            logger.warning(f"Failed to get regional unemployment for {state}", error=str(e))

        return regional

    def _generate_outlook(self, indicators: dict) -> dict[str, Any]:
        """Generate overall economic outlook from indicators."""
        score = 50  # Neutral baseline
        signals = []

        # Unemployment
        if "unemployment" in indicators:
            rate = indicators["unemployment"].get("value", 5)
            if rate < 4:
                score += 15
                signals.append("Low unemployment - strong labor market")
            elif rate < 5:
                score += 5
                signals.append("Healthy employment conditions")
            elif rate > 6:
                score -= 10
                signals.append("Elevated unemployment - economic headwinds")

        # Consumer confidence
        if "consumer_confidence" in indicators:
            conf = indicators["consumer_confidence"].get("value", 80)
            if conf > 100:
                score += 15
                signals.append("High consumer confidence - favorable for new businesses")
            elif conf > 80:
                score += 5
                signals.append("Moderate consumer confidence")
            else:
                score -= 10
                signals.append("Low consumer confidence - cautious spending")

        # Retail sales (growth indicator)
        if "retail_sales" in indicators:
            signals.append("Monitor retail sales trends for spending patterns")

        level = "favorable" if score >= 65 else "neutral" if score >= 45 else "challenging"

        return {
            "score": score,
            "level": level,
            "signals": signals,
            "summary": self._get_outlook_summary(level),
        }

    def _get_outlook_summary(self, level: str) -> str:
        """Get text summary for outlook level."""
        summaries = {
            "favorable": "Economic conditions are favorable for business growth. Consumer spending is healthy and labor market conditions are positive.",
            "neutral": "Economic conditions are stable. Monitor key indicators for signs of change. Standard business planning approaches apply.",
            "challenging": "Economic headwinds present challenges. Consider conservative projections and focus on essential offerings.",
        }
        return summaries.get(level, summaries["neutral"])

    @cached(ttl=86400, key_prefix="spending_trends")
    async def get_consumer_spending_trends(self, category: str | None = None) -> dict[str, Any]:
        """
        Get consumer spending trends.

        Args:
            category: Optional spending category

        Returns:
            Spending trends data
        """
        # Get retail sales data
        retail_data = await self.fred_client.get_series("RSXFS", limit=24)

        if "error" in retail_data:
            return {"error": retail_data["error"]}

        observations = retail_data.get("observations", [])

        # Calculate trend
        if len(observations) >= 12:
            recent_avg = sum(
                o["value"] for o in observations[:6] if o["value"]
            ) / 6
            older_avg = sum(
                o["value"] for o in observations[6:12] if o["value"]
            ) / 6
            change_pct = ((recent_avg - older_avg) / older_avg) * 100 if older_avg else 0
            trend = "growing" if change_pct > 2 else "stable" if change_pct > -2 else "declining"
        else:
            change_pct = 0
            trend = "stable"

        return {
            "category": category or "retail",
            "latest_value": retail_data.get("latest_value"),
            "latest_date": retail_data.get("latest_date"),
            "trend": trend,
            "change_percent": round(change_pct, 2),
            "interpretation": self._interpret_spending_trend(trend, change_pct),
        }

    def _interpret_spending_trend(self, trend: str, change_pct: float) -> str:
        """Interpret spending trend for business planning."""
        if trend == "growing":
            return f"Consumer spending is up {change_pct:.1f}% - favorable environment for new businesses"
        elif trend == "declining":
            return f"Consumer spending is down {abs(change_pct):.1f}% - consider value positioning"
        return "Consumer spending is stable - steady market conditions"

    def get_seasonality_pattern(self, naics_code: str) -> dict[str, Any]:
        """
        Get seasonality pattern for an industry.

        Args:
            naics_code: NAICS industry code

        Returns:
            Monthly seasonality indices and recommendations
        """
        pattern = INDUSTRY_SEASONALITY.get(naics_code, INDUSTRY_SEASONALITY["default"])

        # Find peak and low months
        peak_month = max(pattern.items(), key=lambda x: x[1])
        low_month = min(pattern.items(), key=lambda x: x[1])

        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        recommendations = []
        if peak_month[1] > 1.1:
            recommendations.append(f"Plan for peak demand in {month_names[peak_month[0]]}")
        if low_month[1] < 0.9:
            recommendations.append(f"Prepare for slower period in {month_names[low_month[0]]}")

        return {
            "naics_code": naics_code,
            "monthly_indices": {month_names[k]: v for k, v in pattern.items()},
            "peak_month": month_names[peak_month[0]],
            "peak_index": peak_month[1],
            "low_month": month_names[low_month[0]],
            "low_index": low_month[1],
            "variability": max(pattern.values()) - min(pattern.values()),
            "recommendations": recommendations,
        }

    async def analyze_entry_timing(
        self, business_type: str, location: dict | None = None
    ) -> dict[str, Any]:
        """
        Analyze optimal timing for market entry.

        Args:
            business_type: Type of business
            location: Optional location dict with state info

        Returns:
            Entry timing analysis with recommendations
        """
        from .market_analysis_service import get_market_analysis_service
        market_service = get_market_analysis_service()

        # Get NAICS code
        naics_codes = market_service.naics_service.map_business_type(business_type)
        naics_code = naics_codes[0] if naics_codes else "722515"

        # Get economic snapshot
        state = location.get("state") if location else None
        economic_snapshot = await self.get_economic_snapshot(state)

        # Get seasonality
        seasonality = self.get_seasonality_pattern(naics_code)

        # Get industry trend
        growth_data = await market_service.calculate_growth_rate(naics_code)

        # Determine optimal months (avoid low season, prefer lead-up to peak)
        monthly_indices = INDUSTRY_SEASONALITY.get(naics_code, INDUSTRY_SEASONALITY["default"])

        # Find months before peak (good for ramp-up)
        peak_month = max(monthly_indices.items(), key=lambda x: x[1])[0]
        optimal_months = [(peak_month - 2) % 12 or 12, (peak_month - 1) % 12 or 12]

        # Avoid months below 0.9 index
        avoid_months = [m for m, v in monthly_indices.items() if v < 0.9]

        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        # Generate timing recommendation
        economic_outlook = economic_snapshot.get("outlook", {}).get("level", "neutral")
        industry_trend = growth_data.get("blended_growth_rate", 0)

        if economic_outlook == "favorable" and industry_trend > 2:
            timing_score = 85
            timing_advice = "Conditions are favorable - consider entering market soon"
        elif economic_outlook == "challenging" or industry_trend < 0:
            timing_score = 45
            timing_advice = "Consider waiting for improved conditions or focus on defensive positioning"
        else:
            timing_score = 65
            timing_advice = "Conditions are stable - proceed with standard planning timeline"

        return {
            "business_type": business_type,
            "naics_code": naics_code,
            "timing_score": timing_score,
            "optimal_months": [month_names[m] for m in optimal_months],
            "avoid_months": [month_names[m] for m in avoid_months],
            "economic_context": {
                "outlook": economic_outlook,
                "unemployment": economic_snapshot.get("indicators", {}).get("unemployment", {}).get("value"),
                "consumer_confidence": economic_snapshot.get("indicators", {}).get("consumer_confidence", {}).get("value"),
            },
            "industry_context": {
                "growth_rate": industry_trend,
                "trend": "growing" if industry_trend > 0 else "declining",
            },
            "seasonality": {
                "peak_month": seasonality["peak_month"],
                "low_month": seasonality["low_month"],
            },
            "recommendation": timing_advice,
            "rationale": [
                f"Economic outlook: {economic_outlook}",
                f"Industry growth: {industry_trend:.1f}%",
                f"Peak season: {seasonality['peak_month']}",
            ],
        }


# Singleton instance
_economic_service: EconomicService | None = None


def get_economic_service() -> EconomicService:
    global _economic_service
    if _economic_service is None:
        _economic_service = EconomicService()
    return _economic_service
