"""Competitive Analysis Service - SWOT, Porter's Five Forces, market share, pricing intelligence."""

from typing import Any
from ..core.logging import get_logger

logger = get_logger("service.competitive_analysis")


# Market share estimation weights
MARKET_SHARE_WEIGHTS = {
    "review_count": 0.5,
    "rating": 0.3,
    "price_presence": 0.2,
}

# Porter's Five Forces indicators
PORTERS_INDICATORS = {
    "competitive_rivalry": {
        "high": {"competitor_count": 10, "avg_rating_spread": 0.5},
        "medium": {"competitor_count": 5, "avg_rating_spread": 1.0},
    },
    "buyer_power": {
        "high": {"avg_review_count": 100, "price_variance": 2},
        "medium": {"avg_review_count": 50, "price_variance": 1},
    },
}


class CompetitiveAnalysisService:
    """Service for advanced competitive intelligence analysis."""

    def __init__(self):
        self._llm_service = None

    @property
    def llm_service(self):
        """Lazy load LLM service."""
        if self._llm_service is None:
            from ..core.llm import get_llm_service
            self._llm_service = get_llm_service()
        return self._llm_service

    async def generate_swot(
        self,
        location: dict,
        business_type: str,
        market_data: dict,
    ) -> dict[str, Any]:
        """
        Generate SWOT analysis from gathered market data.

        Args:
            location: Location info with address, lat, lng
            business_type: Type of business
            market_data: Aggregated market data including competitors, demographics, trends

        Returns:
            SWOT analysis with strengths, weaknesses, opportunities, threats
        """
        logger.info("Generating SWOT analysis", business_type=business_type)

        competitors = market_data.get("competitors", [])
        demographics = market_data.get("demographics", {})
        economic = market_data.get("economic", {})
        trends = market_data.get("trends", {})

        # Analyze each SWOT dimension
        strengths = self._identify_strengths(location, business_type, market_data)
        weaknesses = self._identify_weaknesses(location, business_type, market_data)
        opportunities = self._identify_opportunities(location, business_type, market_data)
        threats = self._identify_threats(location, business_type, market_data)

        # Calculate overall assessment
        assessment = self._calculate_swot_assessment(
            strengths, weaknesses, opportunities, threats
        )

        return {
            "location": location.get("address") or f"{location.get('lat')}, {location.get('lng')}",
            "business_type": business_type,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunities": opportunities,
            "threats": threats,
            "assessment": assessment,
            "data_sources": list(market_data.keys()),
        }

    def _identify_strengths(
        self, location: dict, business_type: str, market_data: dict
    ) -> list[dict]:
        """Identify potential strengths from market data."""
        strengths = []
        demographics = market_data.get("demographics", {})
        competitors = market_data.get("competitors", [])
        foot_traffic = market_data.get("foot_traffic", {})

        # Population density strength
        population = demographics.get("total_population", 0)
        if population > 50000:
            strengths.append({
                "factor": "Large population base",
                "description": f"Area population of {population:,} provides substantial customer pool",
                "impact": "high",
                "data_source": "demographics",
            })
        elif population > 20000:
            strengths.append({
                "factor": "Moderate population base",
                "description": f"Area population of {population:,} supports business viability",
                "impact": "medium",
                "data_source": "demographics",
            })

        # Income level strength
        median_income = demographics.get("median_income", 0)
        if median_income > 80000:
            strengths.append({
                "factor": "High-income area",
                "description": f"Median income of ${median_income:,} suggests strong purchasing power",
                "impact": "high",
                "data_source": "demographics",
            })
        elif median_income > 60000:
            strengths.append({
                "factor": "Above-average income",
                "description": f"Median income of ${median_income:,} supports premium offerings",
                "impact": "medium",
                "data_source": "demographics",
            })

        # Low competition strength
        comp_count = len(competitors)
        if comp_count < 3:
            strengths.append({
                "factor": "Limited direct competition",
                "description": f"Only {comp_count} direct competitors in the area",
                "impact": "high",
                "data_source": "competitors",
            })
        elif comp_count < 6:
            strengths.append({
                "factor": "Manageable competition",
                "description": f"{comp_count} competitors - room for differentiation",
                "impact": "medium",
                "data_source": "competitors",
            })

        # Foot traffic strength
        traffic_score = foot_traffic.get("score", 0)
        if traffic_score > 70:
            strengths.append({
                "factor": "High foot traffic",
                "description": "Location benefits from strong pedestrian activity",
                "impact": "high",
                "data_source": "foot_traffic",
            })

        # Market gaps from positioning
        positioning = market_data.get("positioning", {})
        gaps = positioning.get("market_gaps", [])
        if gaps:
            strengths.append({
                "factor": "Market gaps available",
                "description": f"Identified gaps: {gaps[0] if gaps else 'multiple segments'}",
                "impact": "medium",
                "data_source": "positioning",
            })

        return strengths if strengths else [{
            "factor": "Location selected",
            "description": "Market research indicates viable location",
            "impact": "low",
            "data_source": "general",
        }]

    def _identify_weaknesses(
        self, location: dict, business_type: str, market_data: dict
    ) -> list[dict]:
        """Identify potential weaknesses from market data."""
        weaknesses = []
        demographics = market_data.get("demographics", {})
        competitors = market_data.get("competitors", [])
        labor = market_data.get("labor_market", {})

        # Population weakness
        population = demographics.get("total_population", 0)
        if population < 10000:
            weaknesses.append({
                "factor": "Limited population",
                "description": f"Small population of {population:,} may limit customer base",
                "impact": "high",
                "data_source": "demographics",
            })

        # High competition weakness
        comp_count = len(competitors)
        if comp_count > 15:
            weaknesses.append({
                "factor": "High competition density",
                "description": f"{comp_count} direct competitors creates market saturation",
                "impact": "high",
                "data_source": "competitors",
            })
        elif comp_count > 10:
            weaknesses.append({
                "factor": "Competitive market",
                "description": f"{comp_count} competitors - differentiation critical",
                "impact": "medium",
                "data_source": "competitors",
            })

        # Established competitors
        high_rated = [c for c in competitors if (c.get("rating") or 0) >= 4.5]
        if len(high_rated) >= 3:
            weaknesses.append({
                "factor": "Strong established competitors",
                "description": f"{len(high_rated)} competitors with 4.5+ ratings dominate market",
                "impact": "high",
                "data_source": "competitors",
            })

        # Labor market weakness
        hiring_difficulty = labor.get("hiring_difficulty", {}).get("score", 50)
        if hiring_difficulty > 70:
            weaknesses.append({
                "factor": "Tight labor market",
                "description": "High hiring difficulty may impact staffing",
                "impact": "medium",
                "data_source": "labor_market",
            })

        # Income weakness
        median_income = demographics.get("median_income", 0)
        if median_income < 40000:
            weaknesses.append({
                "factor": "Lower income area",
                "description": f"Median income of ${median_income:,} may limit pricing",
                "impact": "medium",
                "data_source": "demographics",
            })

        return weaknesses if weaknesses else [{
            "factor": "New market entrant",
            "description": "As new entrant, will need to build brand awareness",
            "impact": "low",
            "data_source": "general",
        }]

    def _identify_opportunities(
        self, location: dict, business_type: str, market_data: dict
    ) -> list[dict]:
        """Identify market opportunities from market data."""
        opportunities = []
        trends = market_data.get("trends", {})
        economic = market_data.get("economic", {})
        competitors = market_data.get("competitors", [])
        pain_points = market_data.get("pain_points", [])
        positioning = market_data.get("positioning", {})

        # Growing industry opportunity
        trend_direction = trends.get("trend_direction", "stable")
        if trend_direction in ["growing", "strongly_growing"]:
            growth_rate = trends.get("employment_growth_rate", 0)
            opportunities.append({
                "factor": "Growing industry",
                "description": f"Industry is {trend_direction} with {growth_rate:.1f}% growth",
                "impact": "high",
                "data_source": "trends",
            })

        # Favorable economic conditions
        outlook = economic.get("outlook", {})
        if outlook.get("level") == "favorable":
            opportunities.append({
                "factor": "Favorable economic conditions",
                "description": "Economic indicators support new business formation",
                "impact": "high",
                "data_source": "economic",
            })

        # Competitor pain points
        if pain_points:
            top_pain = pain_points[0] if isinstance(pain_points[0], str) else pain_points[0].get("issue", "")
            opportunities.append({
                "factor": "Unmet customer needs",
                "description": f"Competitor weakness: {top_pain}",
                "impact": "medium",
                "data_source": "pain_points",
            })

        # Market gaps from positioning
        gaps = positioning.get("market_gaps", [])
        for gap in gaps[:2]:
            opportunities.append({
                "factor": "Market gap",
                "description": gap,
                "impact": "medium",
                "data_source": "positioning",
            })

        # Low-rated competitors opportunity
        low_rated = [c for c in competitors if (c.get("rating") or 5) < 3.5]
        if len(low_rated) >= 2:
            opportunities.append({
                "factor": "Quality differentiation",
                "description": f"{len(low_rated)} competitors have low ratings - quality focus could win customers",
                "impact": "medium",
                "data_source": "competitors",
            })

        # Underserved segments
        demographics = market_data.get("demographics", {})
        age_distribution = demographics.get("age_distribution", {})
        if age_distribution:
            # Check for large demographic segments
            young_adults = age_distribution.get("18-34", 0)
            if young_adults > 30:
                opportunities.append({
                    "factor": "Young adult demographic",
                    "description": f"{young_adults:.0f}% of population is 18-34 - target with modern offerings",
                    "impact": "medium",
                    "data_source": "demographics",
                })

        return opportunities if opportunities else [{
            "factor": "Market entry",
            "description": "Opportunity to establish presence in the market",
            "impact": "low",
            "data_source": "general",
        }]

    def _identify_threats(
        self, location: dict, business_type: str, market_data: dict
    ) -> list[dict]:
        """Identify market threats from market data."""
        threats = []
        trends = market_data.get("trends", {})
        economic = market_data.get("economic", {})
        competitors = market_data.get("competitors", [])
        seasonality = market_data.get("seasonality", {})

        # Declining industry threat
        trend_direction = trends.get("trend_direction", "stable")
        if trend_direction == "declining":
            threats.append({
                "factor": "Declining industry",
                "description": "Industry trends show decline - differentiation critical",
                "impact": "high",
                "data_source": "trends",
            })

        # Economic headwinds
        outlook = economic.get("outlook", {})
        if outlook.get("level") == "challenging":
            threats.append({
                "factor": "Economic headwinds",
                "description": "Challenging economic conditions may impact consumer spending",
                "impact": "high",
                "data_source": "economic",
            })

        # Strong dominant competitor
        if competitors:
            top_comp = max(competitors, key=lambda x: x.get("review_count", 0), default={})
            if top_comp.get("review_count", 0) > 500 and top_comp.get("rating", 0) >= 4.5:
                threats.append({
                    "factor": "Dominant competitor",
                    "description": f"{top_comp.get('name', 'Competitor')} has strong market position",
                    "impact": "high",
                    "data_source": "competitors",
                })

        # New entrant threat (recent openings)
        recent_competitors = [c for c in competitors if c.get("review_count", 0) < 20]
        if len(recent_competitors) >= 3:
            threats.append({
                "factor": "New market entrants",
                "description": f"{len(recent_competitors)} recent competitors suggest attractive market",
                "impact": "medium",
                "data_source": "competitors",
            })

        # Seasonal volatility
        variability = seasonality.get("variability", 0)
        if variability > 0.3:
            threats.append({
                "factor": "Seasonal volatility",
                "description": "High seasonal variation requires cash flow management",
                "impact": "medium",
                "data_source": "seasonality",
            })

        # Price pressure from competitors
        price_levels = [c.get("price_level") or 0 for c in competitors if c.get("price_level")]
        if price_levels and sum(price_levels) / len(price_levels) < 2:
            threats.append({
                "factor": "Price pressure",
                "description": "Competitors compete on low prices - margin pressure",
                "impact": "medium",
                "data_source": "competitors",
            })

        return threats if threats else [{
            "factor": "Market competition",
            "description": "Standard competitive pressures in the market",
            "impact": "low",
            "data_source": "general",
        }]

    def _calculate_swot_assessment(
        self,
        strengths: list[dict],
        weaknesses: list[dict],
        opportunities: list[dict],
        threats: list[dict],
    ) -> dict:
        """Calculate overall SWOT assessment score and recommendation."""
        # Weight impacts
        impact_weights = {"high": 3, "medium": 2, "low": 1}

        positive_score = sum(
            impact_weights.get(s.get("impact", "low"), 1) for s in strengths
        ) + sum(
            impact_weights.get(o.get("impact", "low"), 1) for o in opportunities
        )

        negative_score = sum(
            impact_weights.get(w.get("impact", "low"), 1) for w in weaknesses
        ) + sum(
            impact_weights.get(t.get("impact", "low"), 1) for t in threats
        )

        # Normalize to 0-100 scale
        total = positive_score + negative_score
        score = int((positive_score / total) * 100) if total > 0 else 50

        # Determine recommendation
        if score >= 65:
            level = "favorable"
            recommendation = "Market conditions support business entry. Focus on leveraging strengths and capitalizing on opportunities."
        elif score >= 45:
            level = "neutral"
            recommendation = "Mixed market conditions. Develop strategies to mitigate weaknesses and threats while building on strengths."
        else:
            level = "challenging"
            recommendation = "Significant challenges present. Consider alternative locations or develop strong differentiation strategy."

        return {
            "score": score,
            "level": level,
            "recommendation": recommendation,
            "strength_count": len(strengths),
            "weakness_count": len(weaknesses),
            "opportunity_count": len(opportunities),
            "threat_count": len(threats),
        }

    async def analyze_five_forces(
        self,
        business_type: str,
        location: dict,
        market_data: dict,
    ) -> dict[str, Any]:
        """
        Analyze Porter's Five Forces for the market.

        Args:
            business_type: Type of business
            location: Location info
            market_data: Aggregated market data

        Returns:
            Five forces analysis with scores and rationale
        """
        logger.info("Analyzing Porter's Five Forces", business_type=business_type)

        competitors = market_data.get("competitors", [])
        demographics = market_data.get("demographics", {})
        trends = market_data.get("trends", {})

        forces = {
            "competitive_rivalry": self._analyze_competitive_rivalry(competitors, trends),
            "supplier_power": self._analyze_supplier_power(business_type, market_data),
            "buyer_power": self._analyze_buyer_power(competitors, demographics),
            "threat_of_substitutes": self._analyze_substitutes(business_type, market_data),
            "threat_of_new_entrants": self._analyze_new_entrants(business_type, market_data),
        }

        # Calculate overall industry attractiveness
        scores = [f["score"] for f in forces.values()]
        avg_threat = sum(scores) / len(scores)

        # Lower threat = more attractive
        attractiveness = 100 - avg_threat
        if attractiveness >= 65:
            level = "attractive"
            summary = "Industry structure is favorable for new entrants"
        elif attractiveness >= 45:
            level = "moderate"
            summary = "Industry has both opportunities and challenges"
        else:
            level = "challenging"
            summary = "Strong competitive forces - entry requires careful strategy"

        return {
            "location": location.get("address") or f"{location.get('lat')}, {location.get('lng')}",
            "business_type": business_type,
            "forces": forces,
            "overall": {
                "attractiveness_score": int(attractiveness),
                "level": level,
                "summary": summary,
            },
        }

    def _analyze_competitive_rivalry(self, competitors: list, trends: dict) -> dict:
        """Analyze competitive rivalry force."""
        comp_count = len(competitors)
        ratings = [c.get("rating", 0) for c in competitors if c.get("rating")]
        rating_spread = max(ratings) - min(ratings) if ratings else 0
        trend = trends.get("trend_direction", "stable")

        # Score: 0 = low rivalry, 100 = high rivalry
        score = min(100, (comp_count * 5) + (30 if rating_spread < 0.5 else 0))

        if trend == "declining":
            score = min(100, score + 20)  # Declining markets have fiercer competition

        if score >= 70:
            level = "high"
            rationale = f"Intense rivalry with {comp_count} competitors and tight rating spread"
        elif score >= 40:
            level = "medium"
            rationale = f"Moderate competition with {comp_count} competitors"
        else:
            level = "low"
            rationale = f"Limited rivalry - only {comp_count} direct competitors"

        return {
            "score": score,
            "level": level,
            "rationale": rationale,
            "factors": [
                f"{comp_count} direct competitors",
                f"Rating spread: {rating_spread:.1f}",
                f"Industry trend: {trend}",
            ],
        }

    def _analyze_supplier_power(self, business_type: str, market_data: dict) -> dict:
        """Analyze supplier bargaining power."""
        # Supplier power varies by business type
        high_supplier_power_types = ["restaurant", "coffee shop", "bakery", "food"]
        low_supplier_power_types = ["consulting", "services", "retail"]

        business_lower = business_type.lower()

        if any(t in business_lower for t in high_supplier_power_types):
            score = 60
            level = "medium"
            rationale = "Food/beverage businesses face moderate supplier power from distributors"
        elif any(t in business_lower for t in low_supplier_power_types):
            score = 30
            level = "low"
            rationale = "Service businesses typically have low supplier dependency"
        else:
            score = 45
            level = "medium"
            rationale = "Moderate supplier power - multiple supply options available"

        return {
            "score": score,
            "level": level,
            "rationale": rationale,
            "factors": [
                "Supplier concentration in industry",
                "Switching costs between suppliers",
                "Importance of volume to supplier",
            ],
        }

    def _analyze_buyer_power(self, competitors: list, demographics: dict) -> dict:
        """Analyze buyer bargaining power."""
        population = demographics.get("total_population", 0)
        comp_count = len(competitors)

        # More competitors = more buyer power (more choices)
        # Higher population = less buyer power per buyer
        if comp_count > 10 or population < 20000:
            score = 70
            level = "high"
            rationale = "Buyers have many alternatives and low switching costs"
        elif comp_count > 5:
            score = 50
            level = "medium"
            rationale = "Moderate buyer power with several alternatives available"
        else:
            score = 30
            level = "low"
            rationale = "Limited alternatives give less power to buyers"

        return {
            "score": score,
            "level": level,
            "rationale": rationale,
            "factors": [
                f"{comp_count} alternative providers",
                "Low switching costs for consumers",
                "Price transparency in market",
            ],
        }

    def _analyze_substitutes(self, business_type: str, market_data: dict) -> dict:
        """Analyze threat of substitutes."""
        # Substitutes vary by business type
        high_substitute_types = ["coffee shop", "fast food", "restaurant"]
        low_substitute_types = ["specialty", "unique", "custom"]

        business_lower = business_type.lower()

        if any(t in business_lower for t in high_substitute_types):
            score = 65
            level = "high"
            rationale = "Many substitute options available (home preparation, other venues)"
        elif any(t in business_lower for t in low_substitute_types):
            score = 30
            level = "low"
            rationale = "Specialized offering limits direct substitutes"
        else:
            score = 50
            level = "medium"
            rationale = "Moderate substitute availability"

        return {
            "score": score,
            "level": level,
            "rationale": rationale,
            "factors": [
                "Availability of alternative solutions",
                "Price-performance of substitutes",
                "Buyer switching costs",
            ],
        }

    def _analyze_new_entrants(self, business_type: str, market_data: dict) -> dict:
        """Analyze threat of new entrants."""
        competitors = market_data.get("competitors", [])
        trends = market_data.get("trends", {})

        trend = trends.get("trend_direction", "stable")
        comp_count = len(competitors)

        # Growing markets attract more entrants
        # More competitors suggest low barriers
        score = 40
        if trend in ["growing", "strongly_growing"]:
            score += 20
        if comp_count > 10:
            score += 15  # Many competitors suggest low barriers

        # Check for dominant players (creates barriers)
        if competitors:
            top_reviews = max(c.get("review_count", 0) for c in competitors)
            if top_reviews > 1000:
                score -= 15  # Dominant players create barriers

        score = max(0, min(100, score))

        if score >= 60:
            level = "high"
            rationale = "Low barriers to entry - expect new competitors"
        elif score >= 40:
            level = "medium"
            rationale = "Moderate barriers exist but entry is possible"
        else:
            level = "low"
            rationale = "Significant barriers protect existing businesses"

        return {
            "score": score,
            "level": level,
            "rationale": rationale,
            "factors": [
                "Capital requirements",
                "Brand loyalty of existing players",
                "Regulatory requirements",
                f"Industry trend: {trend}",
            ],
        }

    def estimate_market_shares(
        self,
        competitors: list[dict],
    ) -> dict[str, Any]:
        """
        Estimate relative market share distribution among competitors.

        Uses review counts, ratings, and price levels as proxies for market share.

        Args:
            competitors: List of competitor data

        Returns:
            Market share estimates with methodology
        """
        logger.info("Estimating market shares", competitor_count=len(competitors))

        if not competitors:
            return {"error": "No competitors provided for analysis"}

        # Calculate weighted scores for each competitor
        shares = []
        total_score = 0

        for comp in competitors:
            review_count = comp.get("review_count", 0) or comp.get("yelp_review_count", 0) or 0
            rating = comp.get("rating", 0) or comp.get("yelp_rating", 0) or 3.0
            has_price = 1 if (comp.get("price_level") or comp.get("yelp_price")) else 0.5

            # Weighted score
            score = (
                (review_count ** 0.7) * MARKET_SHARE_WEIGHTS["review_count"]
                + (rating * 20) * MARKET_SHARE_WEIGHTS["rating"]
                + (has_price * 50) * MARKET_SHARE_WEIGHTS["price_presence"]
            )

            shares.append({
                "name": comp.get("name", "Unknown"),
                "score": score,
                "review_count": review_count,
                "rating": rating,
            })
            total_score += score

        # Convert to percentages
        for share in shares:
            share["share_percent"] = round((share["score"] / total_score) * 100, 1) if total_score > 0 else 0
            del share["score"]

        # Sort by share
        shares.sort(key=lambda x: x["share_percent"], reverse=True)

        # Identify leader
        leader = shares[0] if shares else None
        concentration = sum(s["share_percent"] for s in shares[:3]) if len(shares) >= 3 else 100

        return {
            "shares": shares,
            "market_leader": leader,
            "concentration": {
                "top_3_share": round(concentration, 1),
                "level": "concentrated" if concentration > 70 else "moderate" if concentration > 50 else "fragmented",
            },
            "methodology": {
                "description": "Market share estimated using review volume, ratings, and price presence as proxies",
                "weights": MARKET_SHARE_WEIGHTS,
                "confidence": "medium" if len(competitors) >= 5 else "low",
            },
        }

    def identify_market_leader(self, competitors: list[dict]) -> dict[str, Any]:
        """Identify the market leader from competitors."""
        shares = self.estimate_market_shares(competitors)
        return shares.get("market_leader", {"error": "No competitors found"})

    def analyze_pricing_landscape(
        self,
        competitors: list[dict],
    ) -> dict[str, Any]:
        """
        Analyze competitor pricing strategies and identify gaps.

        Args:
            competitors: List of competitor data with pricing info

        Returns:
            Pricing analysis with distribution and recommendations
        """
        logger.info("Analyzing pricing landscape", competitor_count=len(competitors))

        if not competitors:
            return {"error": "No competitors provided for analysis"}

        # Extract pricing data
        pricing_data = []
        for comp in competitors:
            price_level = comp.get("price_level") or self._price_string_to_level(comp.get("yelp_price"))
            if price_level:
                pricing_data.append({
                    "name": comp.get("name", "Unknown"),
                    "price_level": price_level,
                    "rating": comp.get("rating") or comp.get("yelp_rating") or 0,
                    "review_count": comp.get("review_count") or comp.get("yelp_review_count") or 0,
                })

        if not pricing_data:
            return {
                "distribution": {},
                "analysis": "Insufficient pricing data available",
                "recommendation": "Gather more pricing information before setting strategy",
            }

        # Analyze distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0}
        for p in pricing_data:
            level = min(4, max(1, p["price_level"]))
            distribution[level] += 1

        # Price-quality correlation
        price_quality_pairs = [(p["price_level"], p["rating"]) for p in pricing_data if p["rating"] > 0]

        # Find gaps
        gaps = []
        total = len(pricing_data)
        if distribution.get(1, 0) / total < 0.15 if total > 0 else False:
            gaps.append("Budget segment ($ - $15-20) is underserved")
        if distribution.get(2, 0) / total < 0.15 if total > 0 else False:
            gaps.append("Value segment ($$ - $20-35) has room for entry")
        if distribution.get(3, 0) / total < 0.15 if total > 0 else False:
            gaps.append("Premium segment ($$$ - $35-60) has opportunity")
        if distribution.get(4, 0) / total < 0.1 if total > 0 else False:
            gaps.append("Luxury segment ($$$$ - $60+) is underrepresented")

        # Determine dominant tier
        dominant_tier = max(distribution, key=distribution.get)
        tier_names = {1: "budget", 2: "value", 3: "premium", 4: "luxury"}

        # Price-quality analysis
        high_value = [p for p in pricing_data if p["price_level"] <= 2 and p["rating"] >= 4.0]
        premium_justified = [p for p in pricing_data if p["price_level"] >= 3 and p["rating"] >= 4.3]

        return {
            "distribution": {
                "$": distribution[1],
                "$$": distribution[2],
                "$$$": distribution[3],
                "$$$$": distribution[4],
            },
            "competitors_with_pricing": len(pricing_data),
            "dominant_tier": tier_names[dominant_tier],
            "pricing_gaps": gaps,
            "price_quality_insights": {
                "high_value_competitors": len(high_value),
                "premium_justified": len(premium_justified),
            },
            "recommendation": self._get_pricing_recommendation(distribution, gaps, pricing_data),
        }

    def _price_string_to_level(self, price_str: str | None) -> int | None:
        """Convert Yelp price string ($, $$, etc.) to numeric level."""
        if not price_str:
            return None
        return len(price_str)

    def _get_pricing_recommendation(
        self, distribution: dict, gaps: list, pricing_data: list
    ) -> str:
        """Generate pricing strategy recommendation."""
        total = sum(distribution.values())
        if total == 0:
            return "Insufficient data for pricing recommendation"

        # Find least competitive tier
        min_tier = min(distribution, key=distribution.get)
        tier_names = {1: "budget ($)", 2: "value ($$)", 3: "premium ($$$)", 4: "luxury ($$$$)"}

        if gaps:
            return f"Consider {tier_names[min_tier]} positioning - {gaps[0].lower()}"

        # Default to value if market is evenly distributed
        return "Value positioning ($$) typically offers best balance of volume and margin"

    def identify_pricing_gaps(self, competitors: list[dict]) -> list[str]:
        """Identify pricing segment gaps."""
        analysis = self.analyze_pricing_landscape(competitors)
        return analysis.get("pricing_gaps", [])

    def benchmark_against_competitors(
        self,
        business_profile: dict,
        competitors: list[dict],
    ) -> dict[str, Any]:
        """
        Benchmark potential business against top competitors.

        Args:
            business_profile: Profile of the planned business
            competitors: List of competitor data

        Returns:
            Benchmarking analysis with competitive advantages and gaps
        """
        logger.info("Benchmarking against competitors", competitor_count=len(competitors))

        if not competitors:
            return {"error": "No competitors provided for benchmarking"}

        # Calculate competitor averages
        ratings = [c.get("rating", 0) for c in competitors if c.get("rating")]
        review_counts = [c.get("review_count", 0) for c in competitors if c.get("review_count")]
        price_levels = [c.get("price_level") or self._price_string_to_level(c.get("yelp_price")) or 0 for c in competitors]
        price_levels = [p for p in price_levels if p > 0]

        benchmarks = {
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "avg_review_count": round(sum(review_counts) / len(review_counts)) if review_counts else 0,
            "avg_price_level": round(sum(price_levels) / len(price_levels), 1) if price_levels else 0,
            "top_rating": max(ratings) if ratings else 0,
            "top_review_count": max(review_counts) if review_counts else 0,
        }

        # Analyze business profile against benchmarks
        planned_price = business_profile.get("price_level", 2)
        planned_quality = business_profile.get("target_quality", "high")

        advantages = []
        gaps = []

        # Quality-based advantages
        if planned_quality == "high" and benchmarks["avg_rating"] < 4.0:
            advantages.append({
                "factor": "Quality differentiation",
                "description": f"Competitors average {benchmarks['avg_rating']} rating - room for quality leadership",
            })

        # Pricing-based analysis
        if planned_price < benchmarks["avg_price_level"]:
            advantages.append({
                "factor": "Price advantage",
                "description": f"Below average market price point of {benchmarks['avg_price_level']:.0f}",
            })
        elif planned_price > benchmarks["avg_price_level"]:
            gaps.append({
                "factor": "Premium pricing",
                "description": "Higher price point requires strong quality differentiation",
            })

        # Market penetration analysis
        if benchmarks["top_review_count"] > 500:
            gaps.append({
                "factor": "Established competitors",
                "description": f"Top competitor has {benchmarks['top_review_count']} reviews - brand building needed",
            })

        return {
            "benchmarks": benchmarks,
            "business_profile": business_profile,
            "competitive_advantages": advantages if advantages else [{"factor": "New entrant", "description": "Fresh perspective and modern approach"}],
            "competitive_gaps": gaps if gaps else [{"factor": "Market entry", "description": "Standard new business challenges"}],
            "recommendations": self._generate_benchmark_recommendations(advantages, gaps, benchmarks),
        }

    def _generate_benchmark_recommendations(
        self, advantages: list, gaps: list, benchmarks: dict
    ) -> list[str]:
        """Generate recommendations from benchmarking analysis."""
        recommendations = []

        if advantages:
            recommendations.append(f"Leverage identified advantages: {advantages[0]['factor']}")

        if gaps:
            recommendations.append(f"Address gaps through: focused differentiation on {gaps[0]['factor']}")

        if benchmarks.get("avg_rating", 0) < 4.0:
            recommendations.append("Target 4.5+ rating through exceptional service quality")

        if benchmarks.get("top_review_count", 0) > 500:
            recommendations.append("Invest in customer engagement to build reviews quickly")

        return recommendations if recommendations else ["Focus on consistent quality and customer experience"]


# Singleton instance
_service: CompetitiveAnalysisService | None = None


def get_competitive_analysis_service() -> CompetitiveAnalysisService:
    """Get or create the competitive analysis service singleton."""
    global _service
    if _service is None:
        _service = CompetitiveAnalysisService()
    return _service
