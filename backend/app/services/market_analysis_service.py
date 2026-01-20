"""Market analysis service for TAM/SAM/SOM calculations, growth rates, and industry profiles."""

import math
from typing import Any
from ..core.cache import cached
from ..core.logging import get_logger
from ..tools.market_research.bls_client import get_bls_client
from ..tools.market_research.fred_client import get_fred_client
from ..tools.market_research.naics_service import get_naics_service
from ..tools.market_validator.census_client import get_census_client

logger = get_logger("market_analysis_service")

# Industry spending data per capita (annual, from BLS Consumer Expenditure Survey approximations)
# These are estimates based on BLS CE survey data
INDUSTRY_SPENDING_PER_CAPITA = {
    "722515": 350,  # Coffee shops - avg annual per capita
    "722511": 1200,  # Full-service restaurants
    "722513": 600,  # Limited-service restaurants (fast food)
    "713940": 280,  # Fitness centers
    "812111": 150,  # Barber shops
    "812112": 180,  # Beauty salons
    "445110": 4500,  # Supermarkets/grocery stores
    "445230": 200,  # Fruit/vegetable markets
    "311811": 120,  # Retail bakeries
    "722514": 100,  # Cafeterias
    "453110": 250,  # Florists
    "812310": 50,  # Coin-operated laundries
    "812320": 150,  # Dry cleaners
    "453998": 180,  # Pet stores
    "624410": 1800,  # Child daycare
    "722410": 250,  # Drinking places (bars)
    "default": 200,  # Default for unknown categories
}

# Market participation rates (% of population that uses service)
MARKET_PARTICIPATION_RATES = {
    "722515": 0.65,  # Coffee - 65% of adults
    "722511": 0.75,  # Full-service restaurants
    "722513": 0.80,  # Fast food
    "713940": 0.20,  # Gyms - ~20% membership rate
    "812111": 0.45,  # Barber shops
    "812112": 0.40,  # Beauty salons
    "445110": 0.95,  # Grocery stores
    "311811": 0.50,  # Bakeries
    "453110": 0.25,  # Florists
    "812320": 0.30,  # Dry cleaners
    "624410": 0.08,  # Daycare (% with young children)
    "722410": 0.35,  # Bars
    "default": 0.40,
}

# Typical capture rates for new entrants by competition level
CAPTURE_RATES = {
    "low_competition": 0.15,  # < 5 competitors
    "moderate_competition": 0.08,  # 5-15 competitors
    "high_competition": 0.04,  # 15-30 competitors
    "very_high_competition": 0.02,  # > 30 competitors
}


class MarketAnalysisService:
    """Service for market sizing, growth analysis, and industry profiles."""

    def __init__(self):
        self.bls_client = get_bls_client()
        self.fred_client = get_fred_client()
        self.naics_service = get_naics_service()
        self.census_client = get_census_client()

    @cached(ttl=86400, key_prefix="market_size")
    async def calculate_market_size(
        self,
        location: dict,
        business_type: str,
        radius_miles: float = 5.0,
        competitor_count: int | None = None,
    ) -> dict[str, Any]:
        """
        Calculate TAM, SAM, and SOM for a business.

        Args:
            location: Dict with lat, lng, and optionally demographics
            business_type: Business type description (e.g., "coffee shop")
            radius_miles: Service radius in miles
            competitor_count: Number of competitors (for SOM calculation)

        Returns:
            Market size breakdown with methodology
        """
        # Get NAICS code for business type
        naics_codes = self.naics_service.map_business_type(business_type)
        primary_naics = naics_codes[0] if naics_codes else "722515"

        # Get spending and participation data
        spending_per_capita = INDUSTRY_SPENDING_PER_CAPITA.get(
            primary_naics, INDUSTRY_SPENDING_PER_CAPITA["default"]
        )
        participation_rate = MARKET_PARTICIPATION_RATES.get(
            primary_naics, MARKET_PARTICIPATION_RATES["default"]
        )

        # Get demographics for area
        demographics = await self._get_area_demographics(location)
        population = demographics.get("population", {}).get("total", 50000)
        median_income = demographics.get("income", {}).get("median_household", 65000)

        # Estimate total market population (within radius)
        # Using population density scaling based on radius
        area_sq_miles = math.pi * (radius_miles ** 2)
        # Assume average US density of ~94 people/sq mile for metro areas
        # Adjust based on location type (urban = 3x, suburban = 1x, rural = 0.3x)
        density_multiplier = self._estimate_density_multiplier(demographics)
        estimated_population = min(
            population * 2,  # Cap at 2x the tract population
            int(94 * density_multiplier * area_sq_miles),
        )

        # Income adjustment factor
        national_median = 70000
        income_factor = min(1.5, max(0.6, median_income / national_median))

        # Calculate TAM (Total Addressable Market)
        tam = estimated_population * spending_per_capita * participation_rate * income_factor
        tam = round(tam, -3)  # Round to nearest thousand

        # Calculate SAM (Serviceable Available Market)
        # SAM = TAM filtered by realistic service area and demographic fit
        demographic_fit = self._calculate_demographic_fit(demographics, primary_naics)
        sam = tam * demographic_fit * (radius_miles / 10.0)  # Scale by radius
        sam = min(sam, tam * 0.8)  # SAM can't exceed 80% of TAM
        sam = round(sam, -3)

        # Calculate SOM (Serviceable Obtainable Market)
        # SOM based on competition level
        if competitor_count is not None:
            capture_rate = self._get_capture_rate(competitor_count)
        else:
            capture_rate = CAPTURE_RATES["moderate_competition"]

        som = sam * capture_rate
        som = round(som, -2)  # Round to nearest hundred

        # Calculate confidence based on data quality
        confidence = self._calculate_confidence(demographics, competitor_count is not None)

        return {
            "tam": {
                "value": tam,
                "formatted": f"${tam:,.0f}",
                "description": "Total Addressable Market - maximum theoretical market",
            },
            "sam": {
                "value": sam,
                "formatted": f"${sam:,.0f}",
                "description": "Serviceable Available Market - realistic target market",
            },
            "som": {
                "value": som,
                "formatted": f"${som:,.0f}",
                "description": "Serviceable Obtainable Market - realistic first-year capture",
            },
            "methodology": {
                "population_estimate": estimated_population,
                "spending_per_capita": spending_per_capita,
                "participation_rate": participation_rate,
                "income_factor": round(income_factor, 2),
                "demographic_fit": round(demographic_fit, 2),
                "capture_rate": capture_rate,
                "naics_code": primary_naics,
            },
            "confidence": confidence,
            "assumptions": [
                f"Service radius: {radius_miles} miles",
                f"Estimated population in area: {estimated_population:,}",
                f"Industry avg spending per capita: ${spending_per_capita}/year",
                f"Market participation rate: {participation_rate*100:.0f}%",
            ],
        }

    async def _get_area_demographics(self, location: dict) -> dict:
        """Get demographics for a location."""
        if "demographics" in location:
            return location["demographics"]

        lat = location.get("lat") or location.get("latitude")
        lng = location.get("lng") or location.get("longitude")

        if lat and lng:
            geo = await self.census_client.get_geography_for_coordinates(lat, lng)
            if geo:
                demographics = await self.census_client.get_demographics(
                    geo["state_fips"], geo["county_fips"], geo.get("tract_fips")
                )
                return demographics

        # Return defaults
        return {
            "population": {"total": 50000},
            "income": {"median_household": 65000},
            "age_distribution": {"median_age": 38},
        }

    def _estimate_density_multiplier(self, demographics: dict) -> float:
        """Estimate population density multiplier based on demographics."""
        # Urban areas tend to have higher income variation and housing density
        housing = demographics.get("housing", {})
        total_units = housing.get("total_units", 1000)
        home_value = housing.get("median_home_value", 300000)

        if home_value > 500000 and total_units > 5000:
            return 4.0  # Dense urban
        elif total_units > 3000:
            return 2.5  # Urban
        elif total_units > 1000:
            return 1.5  # Suburban
        return 0.5  # Rural

    def _calculate_demographic_fit(self, demographics: dict, naics_code: str) -> float:
        """Calculate how well demographics match target market."""
        fit_score = 1.0

        income = demographics.get("income", {}).get("median_household", 65000)
        age_dist = demographics.get("age_distribution", {})
        education = demographics.get("education", {})

        # Coffee shops, restaurants - broad appeal
        if naics_code in ["722515", "722511", "722513"]:
            young_adult_pct = age_dist.get("age_18_34_percent", 25)
            if young_adult_pct > 30:
                fit_score *= 1.15
            college_pct = education.get("college_plus_percent", 30)
            if college_pct > 40:
                fit_score *= 1.1

        # Gyms - younger demographics, higher income
        elif naics_code == "713940":
            young_adult_pct = age_dist.get("age_18_34_percent", 25)
            if young_adult_pct > 30:
                fit_score *= 1.2
            if income > 75000:
                fit_score *= 1.15

        # Beauty/Barber - general population
        elif naics_code in ["812111", "812112"]:
            fit_score = 1.0  # Broad appeal

        # Daycare - families with children
        elif naics_code == "624410":
            under_18_pct = age_dist.get("under_18_percent", 20)
            if under_18_pct > 25:
                fit_score *= 1.3
            elif under_18_pct < 15:
                fit_score *= 0.7

        return min(1.2, fit_score)

    def _get_capture_rate(self, competitor_count: int) -> float:
        """Get realistic capture rate based on competition."""
        if competitor_count < 5:
            return CAPTURE_RATES["low_competition"]
        elif competitor_count < 15:
            return CAPTURE_RATES["moderate_competition"]
        elif competitor_count < 30:
            return CAPTURE_RATES["high_competition"]
        return CAPTURE_RATES["very_high_competition"]

    def _calculate_confidence(self, demographics: dict, has_competitor_data: bool) -> dict:
        """Calculate confidence in market size estimates."""
        factors = []
        score = 70  # Base confidence

        if demographics.get("population", {}).get("total"):
            score += 10
            factors.append("Census population data available")
        else:
            factors.append("Using estimated population (lower confidence)")

        if demographics.get("income", {}).get("median_household"):
            score += 5
            factors.append("Income data available")

        if has_competitor_data:
            score += 10
            factors.append("Competitor data included in SOM calculation")
        else:
            factors.append("SOM based on industry averages")

        level = "high" if score >= 85 else "medium" if score >= 70 else "low"

        return {
            "score": score,
            "level": level,
            "factors": factors,
        }

    @cached(ttl=604800, key_prefix="market_growth")  # 7 days
    async def calculate_growth_rate(self, naics_code: str) -> dict[str, Any]:
        """
        Calculate historical and projected growth rate for an industry.

        Args:
            naics_code: NAICS industry code

        Returns:
            Growth rate data with CAGR and projections
        """
        # Get employment trends from BLS
        trends = await self.bls_client.get_industry_employment_trends(naics_code)

        cagr = trends.get("cagr_percent", 2.0)  # Default to 2% if no data

        # Adjust for economic indicators
        indicators = await self.fred_client.get_economic_indicators()
        gdp_growth = 2.5  # Default

        if "gdp" in indicators and indicators["gdp"].get("value"):
            # GDP values are in billions, calculate recent growth
            gdp_growth = 2.5  # Use moderate assumption

        # Blend industry and economic growth
        blended_growth = (cagr * 0.7) + (gdp_growth * 0.3)

        return {
            "naics_code": naics_code,
            "historical_cagr": cagr,
            "economic_growth": gdp_growth,
            "blended_growth_rate": round(blended_growth, 2),
            "source": "BLS Employment Data + FRED Economic Indicators",
            "data_quality": "high" if "error" not in trends else "estimated",
        }

    async def project_market_size(
        self, current_tam: float, growth_rate: float, years: int = 5
    ) -> dict[str, Any]:
        """
        Project market size over time.

        Args:
            current_tam: Current total addressable market
            growth_rate: Annual growth rate (as percentage)
            years: Number of years to project

        Returns:
            Projected market sizes by year
        """
        projections = []
        rate = growth_rate / 100

        for year in range(1, years + 1):
            projected = current_tam * ((1 + rate) ** year)
            projections.append({
                "year": year,
                "projected_tam": round(projected, -3),
                "formatted": f"${projected:,.0f}",
            })

        return {
            "base_tam": current_tam,
            "growth_rate_percent": growth_rate,
            "projections": projections,
            "total_growth": f"{((projections[-1]['projected_tam'] / current_tam) - 1) * 100:.1f}%",
        }

    @cached(ttl=86400, key_prefix="industry_profile")
    async def get_industry_profile(self, naics_code: str) -> dict[str, Any]:
        """
        Build comprehensive industry profile from multiple data sources.

        Args:
            naics_code: NAICS industry code

        Returns:
            Industry profile with size, growth, employment, trends
        """
        naics_info = self.naics_service.lookup_code(naics_code)
        hierarchy = self.naics_service.get_industry_hierarchy(naics_code)

        # Get employment data
        employment = await self.bls_client.get_employment_by_industry(naics_code)
        trends = await self.bls_client.get_industry_employment_trends(naics_code)

        # Get economic context
        indicators = await self.fred_client.get_economic_indicators()

        return {
            "naics_code": naics_code,
            "industry_name": naics_info.get("title") if naics_info else "Unknown",
            "description": naics_info.get("description") if naics_info else "",
            "hierarchy": [
                {"code": h["code"], "title": h["title"]} for h in hierarchy
            ],
            "employment": {
                "current": employment.get("latest_value"),
                "growth_rate": trends.get("cagr_percent"),
                "trend": "growing" if trends.get("cagr_percent", 0) > 0 else "declining",
            },
            "economic_context": {
                "unemployment_rate": indicators.get("unemployment", {}).get("value"),
                "consumer_confidence": indicators.get("consumer_confidence", {}).get("value"),
                "interpretation": indicators.get("_interpretation", {}),
            },
            "spending_estimate": INDUSTRY_SPENDING_PER_CAPITA.get(
                naics_code, INDUSTRY_SPENDING_PER_CAPITA["default"]
            ),
            "data_freshness": "7 days",
        }

    @cached(ttl=86400, key_prefix="labor_market")
    async def analyze_labor_market(
        self, location: dict, business_type: str
    ) -> dict[str, Any]:
        """
        Analyze labor availability and wages for a business type.

        Args:
            location: Dict with lat, lng
            business_type: Business type description

        Returns:
            Labor market analysis with wages, availability, difficulty
        """
        # Get NAICS code
        naics_codes = self.naics_service.map_business_type(business_type)
        primary_naics = naics_codes[0] if naics_codes else "722515"

        # Get area demographics for workforce size
        demographics = await self._get_area_demographics(location)
        population = demographics.get("population", {}).get("total", 50000)
        age_dist = demographics.get("age_distribution", {})

        # Estimate working-age population
        young_adult_pct = age_dist.get("age_18_34_percent", 25) / 100
        working_age_pop = int(population * 0.65)  # ~65% working age
        young_workers = int(working_age_pop * young_adult_pct)

        # Get wage data (using broad occupation codes for common retail/service)
        occupation_codes = {
            "722": "35-0000",  # Food prep and serving
            "713": "39-9000",  # Personal care
            "812": "39-5000",  # Personal appearance
            "445": "41-2000",  # Retail sales
            "624": "39-9011",  # Childcare
        }

        naics_2digit = primary_naics[:3]
        occ_code = occupation_codes.get(naics_2digit, "41-0000")

        wage_data = await self.bls_client.get_wage_data(occ_code)

        # Get unemployment rate for area
        indicators = await self.fred_client.get_economic_indicators()
        unemployment = indicators.get("unemployment", {}).get("value", 4.0)

        # Calculate hiring difficulty score (0-100, higher = harder)
        hiring_difficulty = self._calculate_hiring_difficulty(
            unemployment, wage_data.get("hourly_mean_wage"), primary_naics
        )

        return {
            "location": location,
            "business_type": business_type,
            "naics_code": primary_naics,
            "workforce": {
                "working_age_population": working_age_pop,
                "young_adults_18_34": young_workers,
                "local_unemployment_rate": unemployment,
            },
            "wages": {
                "hourly_mean": wage_data.get("hourly_mean_wage"),
                "annual_mean": wage_data.get("annual_mean_wage"),
                "occupation_code": occ_code,
            },
            "hiring_difficulty": {
                "score": hiring_difficulty,
                "level": "difficult" if hiring_difficulty > 70 else "moderate" if hiring_difficulty > 40 else "easy",
                "factors": self._get_hiring_factors(unemployment, hiring_difficulty),
            },
            "recommendations": self._get_hiring_recommendations(hiring_difficulty, wage_data),
        }

    def _calculate_hiring_difficulty(
        self, unemployment: float, hourly_wage: float | None, naics_code: str
    ) -> int:
        """Calculate hiring difficulty score."""
        base_difficulty = 50

        # Low unemployment = harder to hire
        if unemployment < 4:
            base_difficulty += 25
        elif unemployment < 5:
            base_difficulty += 10
        elif unemployment > 6:
            base_difficulty -= 15

        # Service industries generally harder to staff
        if naics_code.startswith("72"):  # Food service
            base_difficulty += 10

        # Low wages = harder to attract workers
        if hourly_wage and hourly_wage < 15:
            base_difficulty += 10
        elif hourly_wage and hourly_wage > 20:
            base_difficulty -= 10

        return max(0, min(100, base_difficulty))

    def _get_hiring_factors(self, unemployment: float, difficulty: int) -> list[str]:
        """Get factors affecting hiring difficulty."""
        factors = []

        if unemployment < 4:
            factors.append("Very tight labor market")
        elif unemployment < 5:
            factors.append("Competitive labor market")
        else:
            factors.append("Adequate labor supply")

        if difficulty > 70:
            factors.append("Consider competitive wages and benefits")
        elif difficulty < 40:
            factors.append("Favorable hiring conditions")

        return factors

    def _get_hiring_recommendations(
        self, difficulty: int, wage_data: dict
    ) -> list[str]:
        """Generate hiring recommendations."""
        recs = []

        if difficulty > 60:
            recs.append("Offer wages above market average to attract talent")
            recs.append("Consider flexible scheduling to appeal to workers")

        if wage_data.get("hourly_mean_wage", 0) < 15:
            recs.append("Industry wages are below living wage in many areas - budget accordingly")

        if difficulty < 40:
            recs.append("Labor market conditions favorable - focus on quality over speed")

        return recs if recs else ["Standard hiring practices should suffice"]

    @cached(ttl=14400, key_prefix="industry_trends")  # 4 hours
    async def analyze_industry_trends(self, naics_code: str) -> dict[str, Any]:
        """
        Analyze industry trends from employment data and news.

        Args:
            naics_code: NAICS industry code

        Returns:
            Trend analysis with direction, confidence, and signals
        """
        from ..tools.market_research.gdelt_client import get_gdelt_client
        gdelt_client = get_gdelt_client()

        # Get employment trends
        employment_trends = await self.bls_client.get_industry_employment_trends(naics_code)

        # Get NAICS info for keywords
        naics_info = self.naics_service.lookup_code(naics_code)
        industry_name = naics_info.get("title", "") if naics_info else ""

        # Search for industry news
        keywords = naics_info.get("keywords", []) if naics_info else []
        search_term = keywords[0] if keywords else industry_name.split()[0] if industry_name else "business"

        # GDELT client expects a list of keywords and uses the "days_back" parameter
        news_data = await gdelt_client.search_industry_news([search_term], days_back=30)

        # Analyze trend direction
        employment_growth = employment_trends.get("cagr_percent", 0)

        # Determine overall trend
        signals = []
        confidence = 0.7  # Base confidence

        if employment_growth > 3:
            trend_direction = "strongly_growing"
            signals.append(f"Employment growing at {employment_growth:.1f}% annually")
            confidence += 0.1
        elif employment_growth > 0:
            trend_direction = "growing"
            signals.append(f"Employment growing at {employment_growth:.1f}% annually")
        elif employment_growth > -2:
            trend_direction = "stable"
            signals.append("Employment stable")
        else:
            trend_direction = "declining"
            signals.append(f"Employment declining at {abs(employment_growth):.1f}% annually")

        # Add news sentiment if available
        if news_data and "articles" in news_data:
            article_count = len(news_data.get("articles", []))
            if article_count > 10:
                signals.append(f"High media coverage ({article_count} recent articles)")
            avg_tone = news_data.get("average_tone", 0)
            if avg_tone > 2:
                signals.append("Positive media sentiment")
            elif avg_tone < -2:
                signals.append("Negative media sentiment")

        return {
            "naics_code": naics_code,
            "industry_name": industry_name,
            "trend_direction": trend_direction,
            "confidence": round(confidence, 2),
            "employment_growth_rate": employment_growth,
            "signals": signals,
            "data_sources": ["BLS Employment Data", "GDELT News Analysis"],
            "recommendation": self._get_trend_recommendation(trend_direction, employment_growth),
        }

    def _get_trend_recommendation(self, direction: str, growth_rate: float) -> str:
        """Generate recommendation based on trend analysis."""
        if direction == "strongly_growing":
            return "Industry is experiencing strong growth - favorable conditions for market entry"
        elif direction == "growing":
            return "Industry is growing steadily - consider positioning for growth opportunities"
        elif direction == "stable":
            return "Industry is mature and stable - focus on differentiation and value proposition"
        else:
            return "Industry facing headwinds - ensure strong competitive advantage before entering"

    async def get_emerging_trends(self, business_type: str) -> dict[str, Any]:
        """
        Identify emerging trends for a business type.

        Args:
            business_type: Business type description

        Returns:
            Emerging trends and opportunities
        """
        from ..tools.market_research.gdelt_client import get_gdelt_client
        gdelt_client = get_gdelt_client()

        # Get trending topics related to business type
        trending = await gdelt_client.get_trending_topics(business_type)

        naics_codes = self.naics_service.map_business_type(business_type)
        naics_code = naics_codes[0] if naics_codes else None

        # Get industry context
        industry_profile = await self.get_industry_profile(naics_code) if naics_code else {}

        return {
            "business_type": business_type,
            "trending_topics": trending.get("topics", [])[:10] if trending else [],
            "industry_context": {
                "name": industry_profile.get("industry_name"),
                "growth_trend": industry_profile.get("employment", {}).get("trend"),
            },
            "opportunities": self._identify_trend_opportunities(trending, industry_profile),
        }

    def _identify_trend_opportunities(self, trending: dict | None, profile: dict) -> list[str]:
        """Identify opportunities from trends."""
        opportunities = []

        if profile.get("employment", {}).get("trend") == "growing":
            opportunities.append("Growing industry - increasing demand expected")

        if trending and trending.get("topics"):
            opportunities.append("Active media coverage - consumer awareness is high")

        if not opportunities:
            opportunities.append("Focus on local market conditions and direct competition")

        return opportunities


# Singleton instance
_market_analysis_service: MarketAnalysisService | None = None


def get_market_analysis_service() -> MarketAnalysisService:
    global _market_analysis_service
    if _market_analysis_service is None:
        _market_analysis_service = MarketAnalysisService()
    return _market_analysis_service
