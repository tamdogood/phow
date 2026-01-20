# Market Research Tool - Flagship Development Sprint Plan

## Implementation Progress

| Sprint | Status | Completed | Description |
|--------|--------|-----------|-------------|
| **Sprint 1** | COMPLETED | 2026-01-19 | Data Infrastructure & Rate Limiting |
| **Sprint 2** | COMPLETED | 2026-01-19 | Market Sizing & TAM Analysis |
| **Sprint 3** | COMPLETED | 2026-01-20 | Economic Intelligence & Trends |
| **Sprint 4** | COMPLETED | 2026-01-20 | Advanced Competitive Intelligence |
| **Sprint 5** | COMPLETED | 2026-01-20 | Consumer Insights & Sentiment |
| **Sprint 6** | COMPLETED | 2026-01-20 | Financial Projections & Scenarios |
| Sprint 7 | Pending | - | Lightweight Reporting & Snapshots |
| Sprint 8 | Pending | - | Location Intelligence Enhancement |
| Sprint 9 | Pending | - | Risk Assessment & Opportunities |
| Sprint 10 | Pending | - | Comprehensive Reporting & PDF |
| Sprint 11 | Pending | - | Real-Time Market Monitoring |
| Sprint 12 | Pending | - | Primary Research & Integration |

### Sprint 1 Deliverables

**Files Created:**
- `backend/app/core/rate_limiter.py` - Central rate limiting service
- `backend/app/tools/market_research/bls_client.py` - BLS API client
- `backend/app/tools/market_research/fred_client.py` - FRED API client
- `backend/app/tools/market_research/gdelt_client.py` - GDELT news client
- `backend/app/tools/market_research/naics_service.py` - NAICS classification service
- `backend/app/tools/market_research/data/naics_codes.json` - NAICS data
- `backend/app/tools/market_research/data_fetcher.py` - Unified data orchestration
- `backend/tests/tools/market_research/test_naics_service.py` - 17 passing tests

### Sprint 2 Deliverables

**Files Created:**
- `backend/app/services/market_analysis_service.py` - Market sizing service with:
  - TAM/SAM/SOM calculations using BLS Consumer Expenditure data
  - Market growth rate calculations (CAGR) from BLS/FRED data
  - Industry profile builder aggregating multiple data sources
  - Labor market analyzer with hiring difficulty scoring
  - Confidence scoring based on data quality
- `backend/app/tools/market_research/market_sizing_tools.py` - 5 LangChain tools:
  - `calculate_market_size` - TAM/SAM/SOM analysis
  - `get_industry_profile` - Industry overview
  - `analyze_labor_market` - Labor availability and wages
  - `project_market_growth` - Market projections
  - `get_market_sizing_summary` - Comprehensive analysis
- `backend/app/tools/market_research/widget_extractor.py` - Widget data extraction with:
  - `MARKET_SIZE_DATA` widget type for TAM/SAM/SOM visualization
  - `INDUSTRY_DATA` widget type for industry profiles
  - `LABOR_MARKET_DATA` widget type for workforce analysis
  - `GROWTH_PROJECTION_DATA` widget type for charts
- `backend/tests/services/test_market_analysis_service.py` - 17 passing tests

**Files Modified:**
- `backend/app/tools/market_research/agent.py` - Integrated 5 new market sizing tools (17 total tools)

### Sprint 3 Deliverables

**Files Created:**
- `backend/app/services/economic_service.py` - Economic intelligence service with:
  - Economic snapshot with key indicators (GDP, unemployment, consumer confidence)
  - Regional economic data support (state-level indicators)
  - Industry seasonality patterns for 6+ common business types
  - Consumer spending trend analysis
  - Market entry timing analyzer combining economic + seasonal factors
- `backend/app/tools/market_research/economic_tools.py` - 6 LangChain tools:
  - `get_economic_indicators` - Economic snapshot with outlook
  - `analyze_industry_trends` - Industry trend analysis from BLS/GDELT
  - `get_seasonality_pattern` - Monthly business patterns
  - `analyze_entry_timing` - Optimal market entry timing
  - `get_consumer_spending_trends` - Spending trend analysis
  - `get_economic_summary` - Comprehensive economic intelligence
- `backend/tests/services/test_economic_service.py` - 14 passing tests

**Files Modified:**
- `backend/app/services/market_analysis_service.py` - Added:
  - `analyze_industry_trends()` - Industry trend analysis with news sentiment
  - `get_emerging_trends()` - Emerging trend identification
- `backend/app/tools/market_research/widget_extractor.py` - Added widget types:
  - `ECONOMIC_DATA` for economic snapshots
  - `TREND_DATA` for industry trends
  - `SEASONALITY_DATA` for seasonal charts
  - `TIMING_DATA` for entry timing visualization
- `backend/app/tools/market_research/agent.py` - Integrated 6 new economic tools (23 total tools)

### Sprint 4 Deliverables

**Files Created:**
- `backend/app/services/competitive_analysis_service.py` - Competitive intelligence service with:
  - SWOT analysis generator with data-backed insights
  - Porter's Five Forces analyzer
  - Market share estimator using review/rating proxies
  - Competitive pricing landscape analyzer
  - Competitor benchmarking
- `backend/app/tools/market_research/competitive_intelligence_tools.py` - 6 LangChain tools:
  - `generate_swot_analysis` - SWOT analysis with assessment scoring
  - `analyze_competitive_forces` - Porter's Five Forces analysis
  - `estimate_market_shares` - Market share distribution
  - `analyze_pricing_landscape` - Pricing tier analysis and gaps
  - `benchmark_competitors` - Business vs competitor benchmarking
  - `get_competitive_intelligence_summary` - Comprehensive competitive analysis
- `backend/tests/services/test_competitive_analysis_service.py` - 21 tests

**Files Modified:**
- `backend/app/tools/market_research/widget_extractor.py` - Added widget types:
  - `SWOT_DATA` for SWOT visualization (4 quadrants)
  - `FIVE_FORCES_DATA` for Porter's Five Forces radar chart
  - `PRICING_DATA` for pricing distribution chart
  - `MARKET_SHARE_DATA` for market share pie chart
- `backend/app/tools/market_research/agent.py` - Integrated 6 new competitive intelligence tools (29 total tools across 6 domains)

### Sprint 5 Deliverables

**Files Created:**
- `backend/app/services/consumer_analysis_service.py` - Consumer insights service with:
  - Sentiment analysis with aspect-level breakdown (service, quality, price, atmosphere, location)
  - Theme extraction from reviews grouped by category
  - Pain point identification and ranking with severity scores
  - Customer journey mapping with 5 stages and touchpoints
  - Consumer profile builder with psychographic personas
- `backend/app/tools/market_research/consumer_insights_tools.py` - 6 LangChain tools:
  - `analyze_customer_sentiment` - Sentiment analysis from competitor reviews
  - `extract_customer_themes` - Theme extraction by category
  - `identify_customer_pain_points` - Pain points with opportunities
  - `map_customer_journey` - Customer journey mapping
  - `build_customer_profile` - Psychographic customer profiles
  - `get_consumer_insights_summary` - Comprehensive consumer analysis

**Files Modified:**
- `backend/app/tools/market_research/widget_extractor.py` - Added widget types:
  - `SENTIMENT_DATA` for sentiment visualization with aspects
  - `PAIN_POINTS_DATA` for pain point ranking
  - `CUSTOMER_JOURNEY_DATA` for journey funnel visualization
  - `CONSUMER_PROFILE_DATA` for persona cards
- `backend/app/tools/market_research/agent.py` - Integrated 6 new consumer insights tools (35 total tools across 7 domains)

### Sprint 6 Deliverables

**Files Created:**
- `backend/app/tools/market_research/data/industry_benchmarks.json` - Industry financial benchmarks:
  - Revenue averages and ranges for 10+ industries
  - Cost structure breakdowns (COGS, labor, rent, marketing, utilities)
  - Profit margin ranges (low/median/high)
  - Average ticket and transaction volumes
  - Startup costs and break-even timelines
- `backend/app/services/financial_analysis_service.py` - Financial analysis service with:
  - Revenue projection with scenario modeling (conservative/moderate/optimistic)
  - Break-even calculator with startup recovery timeline
  - What-if scenario analysis (price, cost, volume changes)
  - Financial viability scorer with risk assessment
  - Industry benchmark integration
- `backend/app/tools/market_research/financial_tools.py` - 6 LangChain tools:
  - `project_revenue` - Revenue projections with market adjustments
  - `calculate_break_even` - Break-even and startup recovery analysis
  - `run_financial_scenario` - What-if scenario modeling
  - `assess_financial_viability` - Viability score with risk factors
  - `get_financial_summary` - Comprehensive financial analysis
  - `get_industry_benchmarks` - Industry benchmark data

**Files Modified:**
- `backend/app/tools/market_research/widget_extractor.py` - Added widget types:
  - `FINANCIAL_PROJECTION_DATA` for revenue scenario charts
  - `BREAK_EVEN_DATA` for break-even visualization
  - `SCENARIO_COMPARISON_DATA` for what-if comparison
  - `VIABILITY_DATA` for viability gauge/scorecard
- `backend/app/tools/market_research/agent.py` - Integrated 6 new financial tools (41 total tools across 8 domains)

---

## Executive Summary

Transform the existing Market Research tool from a basic location/competitor analysis tool into a comprehensive market research platform that delivers insights equivalent to hiring a full-scale market research firm. This plan breaks down the development into 12 sprints, each delivering demoable, incremental value.

**Key Design Principles:**
- Every sprint delivers demoable value
- Every ticket is atomic and independently committable
- Tests validate both functionality AND accuracy
- Cost and rate limiting are first-class concerns
- Services are consolidated by domain to avoid fragmentation

---

## Current State Analysis

### Existing Capabilities (12 tools across 3 domains)

**Location Analysis:**
- `geocode_address` - Address to coordinates
- `search_nearby_places` - Find nearby POIs
- `get_place_details` - Place details from Google
- `discover_neighborhood` - Neighborhood overview

**Market Validation:**
- `get_location_demographics` - Census demographics
- `analyze_competition_density` - Competition saturation
- `assess_foot_traffic_potential` - Foot traffic scoring
- `calculate_market_viability` - Viability score

**Competitor Intelligence:**
- `find_competitors` - Find competitors (Google + Yelp)
- `get_competitor_details` - Competitor details
- `analyze_competitor_reviews` - Review theme extraction
- `create_positioning_map` - Price vs quality positioning

### Current Data Sources
- Google Maps API (Places, Geocoding)
- Yelp Fusion API (Business, Reviews)
- US Census Bureau API (Demographics)

---

## Target State: Professional-Grade Market Research Platform

### New Capability Domains

1. **Market Sizing & TAM Analysis** - Total addressable market calculations
2. **Industry & Economic Intelligence** - Industry trends, economic indicators, labor market
3. **Advanced Competitive Intelligence** - SWOT, Porter's Five Forces, market share, pricing intelligence
4. **Consumer Insights** - Psychographics, sentiment analysis, customer journey, pain points
5. **Financial Projections** - Revenue estimates, break-even analysis, scenario modeling
6. **Real-Time Market Monitoring** - Alerts, trend tracking, competitor monitoring
7. **Comprehensive Reporting** - Executive reports, dashboards, shareable snapshots
8. **Primary Research Tools** - Survey builder, interview analysis
9. **Risk Assessment** - Market risks, regulatory, timing analysis

### Service Architecture (Consolidated)

To avoid service fragmentation, new functionality will be organized into 5 domain services:

```
backend/app/services/
├── market_analysis_service.py      # Market sizing, growth, industry profiles
├── competitive_analysis_service.py # SWOT, Porter's, market share, pricing, benchmarking
├── consumer_analysis_service.py    # Sentiment, pain points, profiles, journey
├── financial_analysis_service.py   # Revenue, break-even, viability, scenarios
├── report_service.py               # Report generation, recommendations
```

---

## API Cost & Rate Limiting Strategy

### Cost Projections (100 analyses/day)

| API | Pricing | Est. Daily Cost | Strategy |
|-----|---------|-----------------|----------|
| Google Maps | $0.017/request | $50-100 | Aggressive caching (2h-24h TTL) |
| Yelp Fusion | 5000 calls/day free | $0 | Pool requests across users |
| BLS | Free | $0 | Cache 7 days (monthly data) |
| FRED | Free (with key) | $0 | Cache 24h |
| GDELT (news) | Free | $0 | Use instead of NewsAPI |
| Census | Free | $0 | Cache 30 days |
| OpenAI/Anthropic | ~$0.03-0.15/query | $15-75 | LLM call budgeting |

### Rate Limiter Infrastructure (Sprint 1 Prerequisite)

```python
# backend/app/core/rate_limiter.py
class APIRateLimiter:
    """Central rate limiter for all external API calls."""
    async def acquire(self, api_name: str, cost: int = 1) -> bool
    async def get_quota_status(self, api_name: str) -> dict
```

### Caching Strategy

| Data Type | TTL | Rationale |
|-----------|-----|-----------|
| Economic indicators | 24h | FRED updates daily at most |
| Industry data | 7d | BLS updates monthly/quarterly |
| Competitor info | 2-4h | Ratings/reviews change frequently |
| Demographics | 30d | Census data is annual |
| News/trends | 4h | Balance freshness vs. cost |
| Geocoding | 7d | Addresses don't change |

---

## Sprint Breakdown

---

## SPRINT 1: Foundation - Data Infrastructure & Rate Limiting
**Goal:** Establish robust data infrastructure, rate limiting, and integrate additional data sources.
**Demo:** Show unified data fetch for a location with all sources, displaying rate limit status and data freshness indicators.

### Ticket 1.1: Central Rate Limiter Service
**Description:** Create rate limiting infrastructure for all external API calls.
**Files to create:**
- `backend/app/core/rate_limiter.py`
**Acceptance Criteria:**
- [ ] Redis-backed rate limiter with sliding window algorithm
- [ ] Methods: `acquire(api_name, cost)`, `get_quota_status(api_name)`, `reset_quota(api_name)`
- [ ] Configuration for each API's limits (Google: 100 QPS, Yelp: 5000/day, BLS: 500/day)
- [ ] Graceful handling when quota exhausted (return False, don't throw)
- [ ] Unit tests with mocked Redis
**Validation:** Run `pytest tests/core/test_rate_limiter.py` - all tests pass

### Ticket 1.2: BLS (Bureau of Labor Statistics) API Client
**Description:** Create async client for BLS Public Data API to fetch employment, wage, and industry data.
**Files to create:**
- `backend/app/tools/market_research/bls_client.py`
**Acceptance Criteria:**
- [ ] Async client with httpx, integrates with rate limiter
- [ ] Methods: `get_employment_by_industry(naics_code, area)`, `get_wage_data(occupation_code, area)`, `get_industry_employment_trends(naics_code)`
- [ ] Response caching with `@cached` decorator (TTL: 7 days)
- [ ] Error handling with retries (tenacity)
- [ ] Unit tests with mocked responses covering success and error cases
**Validation:** Run `pytest tests/tools/market_research/test_bls_client.py` - all tests pass

### Ticket 1.3: FRED (Federal Reserve Economic Data) API Client
**Description:** Create async client for FRED API to fetch economic indicators.
**Files to create:**
- `backend/app/tools/market_research/fred_client.py`
**Acceptance Criteria:**
- [ ] Async client with httpx, integrates with rate limiter
- [ ] Methods: `get_series(series_id)`, `get_regional_data(series_id, region)`, `get_economic_indicators()`
- [ ] Support for key series: GDP, unemployment rate, CPI, consumer confidence
- [ ] Response caching (TTL: 24h)
- [ ] Unit tests with mocked responses
**Validation:** Run `pytest tests/tools/market_research/test_fred_client.py` - all tests pass

### Ticket 1.4: GDELT News/Trends Client
**Description:** Create client for GDELT Project API (free alternative to NewsAPI) for industry news and trends.
**Files to create:**
- `backend/app/tools/market_research/gdelt_client.py`
**Acceptance Criteria:**
- [ ] Async client for GDELT GKG and Events APIs
- [ ] Methods: `search_industry_news(keywords, date_range)`, `get_trending_topics(theme)`, `get_sentiment_trends(keyword)`
- [ ] Response caching (TTL: 4h)
- [ ] Unit tests
**Validation:** Run `pytest tests/tools/market_research/test_gdelt_client.py` - all tests pass

### Ticket 1.5: NAICS Code Service - Data Collection
**Description:** Collect and bundle NAICS code data for business type mapping.
**Files to create:**
- `backend/app/tools/market_research/data/naics_codes.json`
- `scripts/fetch_naics_data.py`
**Acceptance Criteria:**
- [ ] Script fetches NAICS codes from Census Bureau
- [ ] JSON includes: code, title, description, parent_code, keywords (for search)
- [ ] Business type keyword mappings (e.g., "coffee shop" -> ["722515", "722511"])
- [ ] Data file is complete and valid JSON
**Validation:** Run `python scripts/fetch_naics_data.py && python -c "import json; json.load(open('backend/app/tools/market_research/data/naics_codes.json'))"`

### Ticket 1.6: NAICS Code Service - Implementation
**Description:** Create service for NAICS code lookup and business type mapping.
**Files to create:**
- `backend/app/tools/market_research/naics_service.py`
**Acceptance Criteria:**
- [ ] Load NAICS hierarchy from bundled JSON
- [ ] Methods: `lookup_code(code)`, `search_by_keyword(keyword)`, `get_parent_industry(code)`, `get_related_industries(code)`, `classify_business_type(description)` (LLM-assisted)
- [ ] Unit tests
**Validation:** Run `pytest tests/tools/market_research/test_naics_service.py` - all tests pass

### Ticket 1.7: Unified Data Fetcher - Basic Implementation
**Description:** Create orchestration service that coordinates data fetching from all sources.
**Files to create:**
- `backend/app/tools/market_research/data_fetcher.py`
**Acceptance Criteria:**
- [ ] Basic fetch methods: `fetch_market_data(location, business_type)`, `fetch_industry_data(naics_code)`
- [ ] Sequential fetching (parallel comes in 1.8)
- [ ] Returns data with freshness metadata
- [ ] Unit tests with mocked clients
**Validation:** Run `pytest tests/tools/market_research/test_data_fetcher.py` - basic tests pass

### Ticket 1.8: Unified Data Fetcher - Parallel Execution
**Description:** Add parallel fetching capability with timeouts to data fetcher.
**Files to modify:**
- `backend/app/tools/market_research/data_fetcher.py`
**Acceptance Criteria:**
- [ ] Use `asyncio.gather()` with `return_exceptions=True` for parallel fetching
- [ ] Per-source timeout (default 10s)
- [ ] Aggregate results from successful fetches
- [ ] Unit tests for parallel execution
**Validation:** Run `pytest tests/tools/market_research/test_data_fetcher.py` - parallel tests pass

### Ticket 1.9: Unified Data Fetcher - Graceful Degradation
**Description:** Add graceful degradation when data sources fail.
**Files to modify:**
- `backend/app/tools/market_research/data_fetcher.py`
**Acceptance Criteria:**
- [ ] Continue with partial data when sources fail
- [ ] Log failures with context
- [ ] Return `sources_available` and `sources_failed` in response
- [ ] Unit tests simulating failures
**Validation:** Run `pytest tests/tools/market_research/test_data_fetcher.py` - degradation tests pass

---

## SPRINT 2: Market Sizing & TAM Analysis
**Goal:** Enable users to understand total addressable market, serviceable market, and market opportunity.
**Demo:** Query "What's the market size for coffee shops in Seattle?" and receive TAM/SAM/SOM breakdown with growth projections.

### Ticket 2.1: Market Size Calculator (TAM/SAM/SOM)
**Description:** Create service to calculate TAM, SAM, and SOM in a single cohesive module.
**Files to create:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] TAM calculation: population * category spending * market participation rate
- [ ] SAM calculation: TAM filtered by service radius, demographic fit, income thresholds
- [ ] SOM calculation: SAM * realistic capture rate based on competition
- [ ] Pull industry spending data from BLS Consumer Expenditure Survey
- [ ] Methods: `calculate_market_size(location, business_type, radius_miles)` returning {tam, sam, som, methodology}
- [ ] Include confidence intervals based on data quality
- [ ] Unit tests with known market scenarios (e.g., Seattle coffee market)
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - market size tests pass

### Ticket 2.2: Market Growth Rate Calculator
**Description:** Calculate historical and projected market growth rates.
**Files to modify:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] Fetch historical industry growth from BLS/FRED data
- [ ] Calculate CAGR (Compound Annual Growth Rate)
- [ ] Project future market size (1, 3, 5 years)
- [ ] Methods: `calculate_growth_rate(naics_code)`, `project_market_size(current_tam, growth_rate, years)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - growth tests pass

### Ticket 2.3: Industry Profile Builder
**Description:** Build comprehensive industry profiles from multiple data sources.
**Files to modify:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] Aggregate data from BLS, Census, FRED for industry profiles
- [ ] Methods: `get_industry_profile(naics_code)` returning: industry size, growth, employment, avg wages, business count, trends
- [ ] Cache aggregated profiles (TTL: 24h)
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - profile tests pass

### Ticket 2.4: Labor Market Analyzer
**Description:** Analyze labor availability, wages, and hiring difficulty for the business type.
**Files to modify:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] Fetch occupation data from BLS (wages, employment, projections)
- [ ] Analyze labor supply vs demand in the area
- [ ] Methods: `analyze_labor_market(location, business_type)` returning: available workforce, median wages, hiring difficulty score
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - labor tests pass

### Ticket 2.5: Market Sizing Agent Tools
**Description:** Create LangChain tools for market sizing that the agent can invoke.
**Files to create:**
- `backend/app/tools/market_research/market_sizing_tools.py`
**Acceptance Criteria:**
- [ ] `calculate_market_size` tool with params: address, business_type, radius_miles
- [ ] `get_industry_profile` tool
- [ ] `analyze_labor_market` tool
- [ ] Returns structured data with methodology explanation
- [ ] Tool docstrings explain when to use
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 2.6: Market Sizing Widget Data
**Description:** Add frontend widget data output for market sizing visualization.
**Files to modify:**
- `backend/app/tools/market_research/agent.py`
**Acceptance Criteria:**
- [ ] Create `widget_extractor.py` with registry pattern for widget extraction
- [ ] Extract `<!--MARKET_SIZE_DATA:{...}-->` for frontend widget
- [ ] Include: tam, sam, som, growth_rate, methodology, confidence, data_freshness
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 3: Economic Intelligence & Trends
**Goal:** Provide economic context, trend analysis, and timing intelligence.
**Demo:** Query "What are the economic conditions for retail in Austin?" with trend analysis.

### Ticket 3.1: Economic Indicators Service
**Description:** Fetch and interpret relevant economic indicators for business decisions.
**Files to create:**
- `backend/app/services/economic_service.py`
**Acceptance Criteria:**
- [ ] Fetch from FRED: GDP growth, unemployment, consumer confidence, inflation, retail sales
- [ ] Regional breakdown where available
- [ ] Methods: `get_economic_snapshot(region)`, `get_consumer_spending_trends(category)`
- [ ] Include interpretation (e.g., "Consumer confidence is high, favorable for discretionary spending")
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_economic_service.py` - all tests pass

### Ticket 3.2: Industry Trend Analyzer
**Description:** Analyze industry trends from news, employment data, and market signals.
**Files to modify:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] Aggregate trend signals from: GDELT news, employment growth, search trends
- [ ] Identify trend direction: growing, stable, declining with confidence
- [ ] Methods: `analyze_industry_trends(naics_code)`, `get_emerging_trends(business_type)`
- [ ] LLM-assisted trend interpretation
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - trend tests pass

### Ticket 3.3: Seasonality Analyzer
**Description:** Analyze seasonal patterns for the business type.
**Files to modify:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] Identify seasonal peaks/troughs from historical industry data
- [ ] Methods: `get_seasonality_pattern(business_type)` returning monthly index (1.0 = average)
- [ ] Include recommendations for seasonal planning
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - seasonality tests pass

### Ticket 3.4: Market Entry Timing Analyzer
**Description:** Analyze optimal timing for market entry based on seasonality and economic conditions.
**Files to modify:**
- `backend/app/services/market_analysis_service.py`
**Acceptance Criteria:**
- [ ] Combine seasonality, economic indicators, and trend data
- [ ] Methods: `analyze_entry_timing(business_type, location)` returning: optimal_months, avoid_months, rationale
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_analysis_service.py` - timing tests pass

### Ticket 3.5: Economic Intelligence Agent Tools
**Description:** Create LangChain tools for economic and trend analysis.
**Files to create:**
- `backend/app/tools/market_research/economic_tools.py`
**Acceptance Criteria:**
- [ ] `get_economic_indicators` tool
- [ ] `analyze_industry_trends` tool
- [ ] `get_seasonality_pattern` tool
- [ ] `analyze_entry_timing` tool
- [ ] Comprehensive docstrings
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 3.6: Economic Intelligence Widget Data
**Description:** Add widget data for economic/trend visualizations.
**Files to modify:**
- `backend/app/tools/market_research/widget_extractor.py`
**Acceptance Criteria:**
- [ ] Register `INDUSTRY_DATA` widget type
- [ ] Register `ECONOMIC_DATA` widget type
- [ ] Include: metrics, trends, seasonality chart data
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 4: Advanced Competitive Intelligence
**Goal:** Provide professional-grade competitive analysis with strategic frameworks.
**Demo:** Query "SWOT analysis for opening a yoga studio in downtown Portland" and receive comprehensive competitive intelligence with pricing analysis.

### Ticket 4.1: SWOT Analysis Generator
**Description:** Generate SWOT analysis from gathered market data.
**Files to create:**
- `backend/app/services/competitive_analysis_service.py`
**Acceptance Criteria:**
- [ ] Generate Strengths, Weaknesses, Opportunities, Threats from: location data, competition, demographics, trends
- [ ] LLM-assisted interpretation of data points into SWOT items
- [ ] Methods: `generate_swot(location, business_type, market_data)`
- [ ] Each SWOT item includes supporting data citation
- [ ] Unit tests with sample market data
**Validation:** Run `pytest tests/services/test_competitive_analysis_service.py` - SWOT tests pass

### Ticket 4.2: Porter's Five Forces Analyzer
**Description:** Analyze competitive forces for the market.
**Files to modify:**
- `backend/app/services/competitive_analysis_service.py`
**Acceptance Criteria:**
- [ ] Analyze: Competitive Rivalry, Supplier Power, Buyer Power, Threat of Substitutes, Threat of New Entrants
- [ ] Score each force (low/medium/high) with supporting rationale
- [ ] Methods: `analyze_five_forces(business_type, location, market_data)`
- [ ] LLM-assisted force assessment with data grounding
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_competitive_analysis_service.py` - Porter tests pass

### Ticket 4.3: Market Share Estimator
**Description:** Estimate market share distribution among competitors.
**Files to modify:**
- `backend/app/services/competitive_analysis_service.py`
**Acceptance Criteria:**
- [ ] Estimate relative market share using: review counts, ratings, price levels as proxies
- [ ] Methods: `estimate_market_shares(competitors)`, `identify_market_leader(competitors)`
- [ ] Return share percentages with confidence levels and methodology
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_competitive_analysis_service.py` - share tests pass

### Ticket 4.4: Competitive Pricing Intelligence
**Description:** Track and analyze competitor pricing strategies.
**Files to modify:**
- `backend/app/services/competitive_analysis_service.py`
**Acceptance Criteria:**
- [ ] Extract pricing info from Yelp ($ to $$$$) and Google (price_level)
- [ ] Methods: `analyze_pricing_landscape(competitors)`, `identify_pricing_gaps(competitors)`
- [ ] Include price-quality correlation analysis
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_competitive_analysis_service.py` - pricing tests pass

### Ticket 4.5: Competitor Benchmarking
**Description:** Benchmark potential business against top competitors.
**Files to modify:**
- `backend/app/services/competitive_analysis_service.py`
**Acceptance Criteria:**
- [ ] Compare across dimensions: pricing tier, ratings, review volume, service breadth
- [ ] Methods: `benchmark_against_competitors(business_profile, competitors)`
- [ ] Identify competitive advantages and gaps
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_competitive_analysis_service.py` - benchmark tests pass

### Ticket 4.6: Enhanced Positioning Map (Multi-Dimensional)
**Description:** Enhance positioning map with multiple axes beyond price/quality.
**Files to modify:**
- `backend/app/tools/competitor_analyzer/agent_tools.py`
**Acceptance Criteria:**
- [ ] Support configurable axes: price vs quality, price vs variety, quality vs convenience
- [ ] Methods: Update `create_positioning_map` with `axes` parameter
- [ ] Identify white space opportunities on each dimension
- [ ] Unit tests
**Validation:** Run `pytest tests/tools/competitor_analyzer/test_agent_tools.py` - positioning tests pass

### Ticket 4.7: Competitive Intelligence Agent Tools
**Description:** Create LangChain tools for strategic competitive analysis.
**Files to create:**
- `backend/app/tools/market_research/competitive_intelligence_tools.py`
**Acceptance Criteria:**
- [ ] `generate_swot_analysis` tool
- [ ] `analyze_competitive_forces` tool (Porter's)
- [ ] `estimate_market_shares` tool
- [ ] `analyze_pricing_landscape` tool
- [ ] Comprehensive docstrings with examples
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 4.8: Strategic Frameworks Widget Data
**Description:** Add widget data for SWOT and Porter's Five Forces.
**Files to modify:**
- `backend/app/tools/market_research/widget_extractor.py`
**Acceptance Criteria:**
- [ ] Register `SWOT_DATA` widget type (4 quadrant data)
- [ ] Register `FIVE_FORCES_DATA` widget type (5 force scores with rationale)
- [ ] Register `PRICING_DATA` widget type (price distribution chart)
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 5: Consumer Insights & Sentiment Analysis
**Goal:** Provide deep consumer insights through review analysis, sentiment tracking, and journey mapping.
**Demo:** Query "What do customers love and hate about coffee shops in Capitol Hill?" with sentiment breakdown, pain points, and customer journey insights.

### Ticket 5.1: Advanced Sentiment Analysis Service
**Description:** Create NLP service for deep sentiment analysis of reviews.
**Files to create:**
- `backend/app/services/consumer_analysis_service.py`
**Acceptance Criteria:**
- [ ] LLM-powered sentiment analysis with aspect extraction
- [ ] Methods: `analyze_sentiment(reviews)`, `extract_aspects(reviews)`
- [ ] Return: overall_sentiment (-1 to 1), aspect_sentiments (service, quality, price, atmosphere, location)
- [ ] Confidence scores for each analysis
- [ ] Unit tests with sample review data
**Validation:** Run `pytest tests/services/test_consumer_analysis_service.py` - sentiment tests pass

### Ticket 5.2: Enhanced Review Theme Extractor
**Description:** LLM-powered theme extraction replacing keyword matching.
**Files to modify:**
- `backend/app/services/consumer_analysis_service.py`
**Acceptance Criteria:**
- [ ] LLM extracts themes (not just keyword matching)
- [ ] Group themes by category: product, service, experience, value, location
- [ ] Track theme frequency, sentiment polarity, and example quotes
- [ ] Methods: `extract_themes(reviews)` returning structured theme data
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_consumer_analysis_service.py` - theme tests pass

### Ticket 5.3: Customer Pain Point Identifier
**Description:** Identify and rank customer pain points from competitor reviews.
**Files to modify:**
- `backend/app/services/consumer_analysis_service.py`
**Acceptance Criteria:**
- [ ] Extract pain points from negative reviews using LLM
- [ ] Categorize: wait times, pricing, quality, service, cleanliness, hours, parking, etc.
- [ ] Rank by frequency and severity (1-5 scale)
- [ ] Methods: `identify_pain_points(reviews)`, `get_opportunities_from_pain_points(pain_points)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_consumer_analysis_service.py` - pain point tests pass

### Ticket 5.4: Customer Journey Mapper
**Description:** Map typical customer journey for the business type.
**Files to modify:**
- `backend/app/services/consumer_analysis_service.py`
**Acceptance Criteria:**
- [ ] Define journey stages: awareness, consideration, purchase, experience, loyalty
- [ ] Identify touchpoints and decision factors for each stage
- [ ] Methods: `map_customer_journey(business_type, reviews)` using LLM to infer from review content
- [ ] Include opportunity identification at each stage
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_consumer_analysis_service.py` - journey tests pass

### Ticket 5.5: Consumer Profile Builder
**Description:** Build psychographic consumer profile for the target market.
**Files to modify:**
- `backend/app/services/consumer_analysis_service.py`
**Acceptance Criteria:**
- [ ] Combine demographics with behavioral signals from reviews
- [ ] Infer: values, lifestyle, preferences, price sensitivity
- [ ] Methods: `build_consumer_profile(location, business_type, demographics, reviews)`
- [ ] LLM-assisted profile generation with persona format
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_consumer_analysis_service.py` - profile tests pass

### Ticket 5.6: Consumer Insights Agent Tools
**Description:** Create LangChain tools for consumer analysis.
**Files to create:**
- `backend/app/tools/market_research/consumer_insights_tools.py`
**Acceptance Criteria:**
- [ ] `analyze_customer_sentiment` tool
- [ ] `identify_customer_pain_points` tool
- [ ] `map_customer_journey` tool
- [ ] `build_customer_profile` tool
- [ ] Comprehensive docstrings
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 5.7: Consumer Insights Widget Data
**Description:** Add widget data for consumer visualizations.
**Files to modify:**
- `backend/app/tools/market_research/widget_extractor.py`
**Acceptance Criteria:**
- [ ] Register `SENTIMENT_DATA` widget type (sentiment chart, aspect breakdown)
- [ ] Register `PAIN_POINTS_DATA` widget type (ranked list with severity)
- [ ] Register `CUSTOMER_JOURNEY_DATA` widget type (funnel/journey visualization)
- [ ] Register `CONSUMER_PROFILE_DATA` widget type (persona card)
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 6: Financial Projections & Scenario Modeling
**Goal:** Provide revenue projections, break-even analysis, and what-if scenario modeling.
**Demo:** Query "Revenue projection for a new pizza restaurant in Austin" with multiple scenarios and break-even analysis.

### Ticket 6.1: Industry Benchmark Data Collection
**Description:** Collect and bundle industry financial benchmarks.
**Files to create:**
- `backend/app/tools/market_research/data/industry_benchmarks.json`
- `scripts/compile_industry_benchmarks.py`
**Acceptance Criteria:**
- [ ] Compile from SBA, RMA, and public sources
- [ ] Include by NAICS: avg revenue, cost structure (rent %, labor %, COGS %), profit margins
- [ ] Data file is complete and documented
**Validation:** Run `python scripts/compile_industry_benchmarks.py` and verify JSON validity

### Ticket 6.2: Revenue Projection Service
**Description:** Create service to project potential revenue.
**Files to create:**
- `backend/app/services/financial_analysis_service.py`
**Acceptance Criteria:**
- [ ] Calculate revenue using: market size (SOM), avg ticket, visit frequency, capture rate
- [ ] Support multiple scenarios: conservative (25th percentile), moderate (50th), optimistic (75th)
- [ ] Methods: `project_revenue(business_type, location, market_data, scenario)`
- [ ] Include industry benchmarks for validation
- [ ] Unit tests with known scenarios
**Validation:** Run `pytest tests/services/test_financial_analysis_service.py` - revenue tests pass

### Ticket 6.3: Break-Even Calculator
**Description:** Calculate break-even point and timeline.
**Files to modify:**
- `backend/app/services/financial_analysis_service.py`
**Acceptance Criteria:**
- [ ] Calculate: break-even units, break-even revenue, months to break-even
- [ ] Use industry benchmarks for typical cost structures when user doesn't provide
- [ ] Methods: `calculate_break_even(revenue_projection, fixed_costs, variable_cost_pct)`, `estimate_break_even_timeline(monthly_revenue, monthly_costs)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_financial_analysis_service.py` - break-even tests pass

### Ticket 6.4: Scenario Modeling Engine
**Description:** Enable what-if analysis for market variables.
**Files to modify:**
- `backend/app/services/financial_analysis_service.py`
**Acceptance Criteria:**
- [ ] Allow users to modify: location, pricing, competition level, opening date
- [ ] Methods: `run_scenario(base_analysis, modifications)` returning modified projections
- [ ] Calculate impact delta from baseline
- [ ] Unit tests with various scenarios
**Validation:** Run `pytest tests/services/test_financial_analysis_service.py` - scenario tests pass

### Ticket 6.5: Financial Viability Scorer
**Description:** Score overall financial viability.
**Files to modify:**
- `backend/app/services/financial_analysis_service.py`
**Acceptance Criteria:**
- [ ] Score (0-100) based on: revenue potential, margin expectations, break-even timeline, market growth
- [ ] Methods: `calculate_financial_viability(revenue_projection, costs, market_growth)`
- [ ] Include risk-adjusted projections
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_financial_analysis_service.py` - viability tests pass

### Ticket 6.6: Financial Projection Agent Tools
**Description:** Create LangChain tools for financial analysis.
**Files to create:**
- `backend/app/tools/market_research/financial_tools.py`
**Acceptance Criteria:**
- [ ] `project_revenue` tool (with scenario parameter)
- [ ] `calculate_break_even` tool
- [ ] `run_scenario` tool (what-if analysis)
- [ ] `assess_financial_viability` tool
- [ ] Comprehensive docstrings
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 6.7: Financial Projections Widget Data
**Description:** Add widget data for financial visualizations.
**Files to modify:**
- `backend/app/tools/market_research/widget_extractor.py`
**Acceptance Criteria:**
- [ ] Register `FINANCIAL_PROJECTION_DATA` widget type (revenue chart with scenarios)
- [ ] Register `BREAK_EVEN_DATA` widget type (break-even visualization)
- [ ] Register `SCENARIO_COMPARISON_DATA` widget type (scenario comparison table)
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 7: Lightweight Reporting & Shareable Snapshots
**Goal:** Enable users to export and share market research findings early (before comprehensive reporting).
**Demo:** Generate a shareable market snapshot and download summary PDF.

### Ticket 7.1: Report Data Aggregator
**Description:** Aggregate analysis results into report structure.
**Files to create:**
- `backend/app/services/report_service.py`
**Acceptance Criteria:**
- [ ] Collect data from all analysis services run in session
- [ ] Organize into sections: Summary, Market Size, Competition, Financials
- [ ] Methods: `aggregate_report_data(analysis_results)` returning structured report
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_report_service.py` - aggregation tests pass

### Ticket 7.2: Executive Summary Generator
**Description:** Generate AI-powered executive summary.
**Files to modify:**
- `backend/app/services/report_service.py`
**Acceptance Criteria:**
- [ ] LLM-generated executive summary (2-3 paragraphs)
- [ ] Key findings bullets (5-7 points)
- [ ] Overall recommendation (Go/Caution/No-Go) with confidence
- [ ] Methods: `generate_executive_summary(report_data)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_report_service.py` - summary tests pass

### Ticket 7.3: Recommendation Engine
**Description:** Generate actionable recommendations from analysis.
**Files to modify:**
- `backend/app/services/report_service.py`
**Acceptance Criteria:**
- [ ] Generate prioritized recommendations from all analysis
- [ ] Categories: immediate actions, strategic considerations, risk mitigations
- [ ] Methods: `generate_recommendations(report_data)`
- [ ] Each recommendation includes rationale and priority (high/medium/low)
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_report_service.py` - recommendation tests pass

### Ticket 7.4: Shareable Market Snapshot
**Description:** Create one-click shareable market analysis summary.
**Files to create:**
- `backend/app/api/routes/snapshots.py`
- `supabase/migrations/xxx_market_snapshots.sql`
**Acceptance Criteria:**
- [ ] Store snapshot in database with unique shareable ID
- [ ] `POST /api/snapshots` - create snapshot from analysis
- [ ] `GET /api/snapshots/{id}` - retrieve snapshot (public, no auth)
- [ ] Include expiration (30 days default)
- [ ] API tests
**Validation:** Run `pytest tests/api/test_snapshots.py` - all tests pass

### Ticket 7.5: Summary PDF Generator
**Description:** Generate lightweight PDF summary (not full report yet).
**Files to create:**
- `backend/app/services/pdf_service.py`
**Acceptance Criteria:**
- [ ] Use reportlab for simple PDF generation
- [ ] Include: executive summary, key metrics, top recommendations
- [ ] Methods: `generate_summary_pdf(report_data)` returning bytes
- [ ] 2-3 page output max
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_pdf_service.py` - all tests pass

### Ticket 7.6: Report Generation Agent Tool
**Description:** Create tool for generating reports and snapshots.
**Files to create:**
- `backend/app/tools/market_research/report_tools.py`
**Acceptance Criteria:**
- [ ] `generate_market_summary` tool (returns executive summary + recommendations)
- [ ] `create_shareable_snapshot` tool (returns share URL)
- [ ] Integration tests
**Validation:** Run tools directly and verify output

---

## SPRINT 8: Location Intelligence Enhancement
**Goal:** Enhance location analysis with trade area mapping, site scoring, and accessibility analysis.
**Demo:** Query "Score this specific address for a retail store" with trade area and site score breakdown.

### Ticket 8.1: Trade Area Analysis Service
**Description:** Define and analyze primary, secondary, and tertiary trade areas.
**Files to create:**
- `backend/app/services/location_intelligence_service.py`
**Acceptance Criteria:**
- [ ] Calculate trade areas using drive-time estimates (5, 10, 15 min)
- [ ] Use Google Maps Distance Matrix API for drive times
- [ ] Aggregate demographics for each trade area ring
- [ ] Methods: `define_trade_areas(location)`, `analyze_trade_area(location, minutes)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_location_intelligence_service.py` - trade area tests pass

### Ticket 8.2: Site Scoring Model
**Description:** Create comprehensive site scoring with weighted factors.
**Files to modify:**
- `backend/app/services/location_intelligence_service.py`
**Acceptance Criteria:**
- [ ] Score sites on: visibility (major road), accessibility (transit), parking, co-tenancy, demographics match, competition
- [ ] Configurable weights by business type
- [ ] Methods: `score_site(location, business_type)` returning detailed breakdown (0-100 per factor)
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_location_intelligence_service.py` - site score tests pass

### Ticket 8.3: Parking & Accessibility Analyzer
**Description:** Analyze parking and accessibility factors.
**Files to modify:**
- `backend/app/services/location_intelligence_service.py`
**Acceptance Criteria:**
- [ ] Find nearby parking lots/garages via Google Places
- [ ] Assess transit accessibility (stations within 500m)
- [ ] Methods: `analyze_parking(location)`, `get_accessibility_score(location)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_location_intelligence_service.py` - accessibility tests pass

### Ticket 8.4: Co-Tenancy Analyzer
**Description:** Analyze neighboring businesses for synergy.
**Files to modify:**
- `backend/app/services/location_intelligence_service.py`
**Acceptance Criteria:**
- [ ] Identify anchor tenants (major retailers, restaurants)
- [ ] Score co-tenancy synergy based on business type compatibility matrix
- [ ] Methods: `analyze_co_tenancy(location, business_type)` returning score and key neighbors
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_location_intelligence_service.py` - co-tenancy tests pass

### Ticket 8.5: Multi-Location Comparison
**Description:** Compare multiple locations for the same business type.
**Files to modify:**
- `backend/app/services/location_intelligence_service.py`
**Acceptance Criteria:**
- [ ] Score and rank multiple locations
- [ ] Methods: `compare_locations(locations, business_type)` returning ranked list with scores
- [ ] Highlight strengths/weaknesses of each
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_location_intelligence_service.py` - comparison tests pass

### Ticket 8.6: Location Intelligence Agent Tools
**Description:** Create LangChain tools for location analysis.
**Files to create:**
- `backend/app/tools/market_research/location_intelligence_tools.py`
**Acceptance Criteria:**
- [ ] `analyze_trade_area` tool
- [ ] `score_site` tool
- [ ] `analyze_accessibility` tool
- [ ] `compare_locations` tool
- [ ] Comprehensive docstrings
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 8.7: Location Intelligence Widget Data
**Description:** Add widget data for location visualizations.
**Files to modify:**
- `backend/app/tools/market_research/widget_extractor.py`
**Acceptance Criteria:**
- [ ] Register `TRADE_AREA_DATA` widget type (map overlay with rings)
- [ ] Register `SITE_SCORE_DATA` widget type (radar chart)
- [ ] Register `LOCATION_COMPARISON_DATA` widget type (comparison table)
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 9: Risk Assessment & Opportunity Analysis
**Goal:** Provide comprehensive risk assessment and opportunity identification.
**Demo:** Query "What are the risks of opening a bookstore in this area?" with risk matrix and mitigation strategies.

### Ticket 9.1: Regulatory Data Collection
**Description:** Collect and bundle regulatory requirements by business type and state.
**Files to create:**
- `backend/app/tools/market_research/data/regulatory_requirements.json`
- `scripts/compile_regulatory_data.py`
**Acceptance Criteria:**
- [ ] Compile from SBA, state government sources
- [ ] Include by business type x state: licenses, permits, health codes, zoning considerations
- [ ] Data file structured and documented
**Validation:** Run `python scripts/compile_regulatory_data.py` and verify JSON validity

### Ticket 9.2: Market Risk Assessment Service
**Description:** Assess market-specific risks.
**Files to create:**
- `backend/app/services/risk_assessment_service.py`
**Acceptance Criteria:**
- [ ] Identify risks: market saturation, declining trends, economic sensitivity, demographic shifts
- [ ] Score each risk by likelihood (1-5) and impact (1-5)
- [ ] Methods: `assess_market_risks(location, business_type, market_data)` returning risk matrix
- [ ] Include mitigation suggestions per risk
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_risk_assessment_service.py` - market risk tests pass

### Ticket 9.3: Competitive Threat Analyzer
**Description:** Analyze specific competitive threats.
**Files to modify:**
- `backend/app/services/risk_assessment_service.py`
**Acceptance Criteria:**
- [ ] Identify threats: dominant competitors, new entrants (recent openings), substitute products
- [ ] Methods: `analyze_competitive_threats(competitors, market_data)`
- [ ] Include defensive strategy recommendations
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_risk_assessment_service.py` - threat tests pass

### Ticket 9.4: Regulatory Requirements Service
**Description:** Surface regulatory considerations for the business.
**Files to modify:**
- `backend/app/services/risk_assessment_service.py`
**Acceptance Criteria:**
- [ ] Look up requirements from bundled data
- [ ] Methods: `get_regulatory_requirements(business_type, state)`
- [ ] Flag potential compliance challenges
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_risk_assessment_service.py` - regulatory tests pass

### Ticket 9.5: Opportunity Scorer
**Description:** Identify and score market opportunities.
**Files to create:**
- `backend/app/services/opportunity_service.py`
**Acceptance Criteria:**
- [ ] Identify opportunities from: unmet needs (pain points), market gaps (positioning), underserved segments, emerging trends
- [ ] Score opportunities by: size, feasibility, timing, fit (each 1-5)
- [ ] Methods: `identify_opportunities(market_data, consumer_insights)`, `score_opportunities(opportunities)`
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_opportunity_service.py` - all tests pass

### Ticket 9.6: Risk & Opportunity Agent Tools
**Description:** Create LangChain tools for risk and opportunity analysis.
**Files to create:**
- `backend/app/tools/market_research/risk_opportunity_tools.py`
**Acceptance Criteria:**
- [ ] `assess_market_risks` tool
- [ ] `analyze_competitive_threats` tool
- [ ] `identify_opportunities` tool
- [ ] `get_regulatory_requirements` tool
- [ ] Comprehensive docstrings
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 9.7: Risk & Opportunity Widget Data
**Description:** Add widget data for risk/opportunity visualizations.
**Files to modify:**
- `backend/app/tools/market_research/widget_extractor.py`
**Acceptance Criteria:**
- [ ] Register `RISK_MATRIX_DATA` widget type (likelihood x impact matrix)
- [ ] Register `OPPORTUNITY_DATA` widget type (scored opportunity list)
- [ ] Test widget data extraction
**Validation:** Run agent query and verify widget data in stream output

---

## SPRINT 10: Comprehensive Reporting & PDF Generation
**Goal:** Generate professional full-length market research reports.
**Demo:** Generate complete market research PDF report with all sections and visualizations.

### Ticket 10.1: Full Report Template
**Description:** Design comprehensive report structure with all sections.
**Files to create:**
- `backend/app/tools/market_research/templates/full_report.py`
**Acceptance Criteria:**
- [ ] Define report sections: Executive Summary, Market Overview, Industry Analysis, Competitive Landscape, Consumer Insights, Financial Projections, Location Analysis, Risk Assessment, Recommendations, Appendix
- [ ] Each section has defined data requirements
- [ ] Template structure for PDF rendering
**Validation:** Template file exists and is importable

### Ticket 10.2: Chart/Visualization Generator
**Description:** Generate charts for report inclusion.
**Files to create:**
- `backend/app/services/chart_service.py`
**Acceptance Criteria:**
- [ ] Use matplotlib/plotly for chart generation
- [ ] Charts: market size pie, competitor positioning scatter, sentiment bar, risk matrix heatmap, revenue projection line
- [ ] Methods: `generate_chart(chart_type, data)` returning image bytes
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_chart_service.py` - all tests pass

### Ticket 10.3: Full PDF Report Generator
**Description:** Generate comprehensive PDF report.
**Files to modify:**
- `backend/app/services/pdf_service.py`
**Acceptance Criteria:**
- [ ] Render full report from template with all sections
- [ ] Include generated charts
- [ ] Professional formatting (headers, page numbers, table of contents)
- [ ] Methods: `generate_full_report_pdf(report_data)` returning bytes
- [ ] 15-25 page output
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_pdf_service.py` - full report tests pass

### Ticket 10.4: Report Generation Celery Task
**Description:** Background task for report generation.
**Files to create:**
- `backend/app/workers/report_tasks.py`
**Acceptance Criteria:**
- [ ] Celery task: `generate_report_task(report_data, report_type)`
- [ ] Separate queue for report generation (CPU-intensive)
- [ ] Store result in Supabase storage
- [ ] Return download URL on completion
- [ ] Integration tests
**Validation:** Run task and verify PDF generation and storage

### Ticket 10.5: Report API Endpoints
**Description:** API endpoints for report management.
**Files to create:**
- `backend/app/api/routes/reports.py`
**Acceptance Criteria:**
- [ ] `POST /api/reports/generate` - start async report generation
- [ ] `GET /api/reports/{report_id}/status` - check generation status
- [ ] `GET /api/reports/{report_id}/download` - download completed report
- [ ] Rate limiting (1 full report per 5 minutes per session)
- [ ] API tests
**Validation:** Run `pytest tests/api/test_reports.py` - all tests pass

### Ticket 10.6: Report Generation Agent Tool
**Description:** Create tool for generating full reports.
**Files to modify:**
- `backend/app/tools/market_research/report_tools.py`
**Acceptance Criteria:**
- [ ] `generate_full_report` tool (initiates async generation, returns status URL)
- [ ] Integration tests
**Validation:** Run tool directly and verify report generation initiated

---

## SPRINT 11: Real-Time Market Monitoring
**Goal:** Enable ongoing market monitoring with alerts for significant changes.
**Demo:** Set up monitoring for a market and demonstrate alert generation for competitor change.

### Ticket 11.1: Market Watch Infrastructure
**Description:** Database models and repository for market watches.
**Files to create:**
- `supabase/migrations/xxx_market_watches.sql`
- `backend/app/repositories/market_watch_repository.py`
**Acceptance Criteria:**
- [ ] Tables: `market_watches` (user watches), `market_snapshots` (periodic snapshots), `market_alerts` (detected changes)
- [ ] Snapshot retention policy: keep 30 days, then aggregate to weekly
- [ ] Repository CRUD methods
- [ ] Migration runs successfully
**Validation:** Apply migration and run repository tests

### Ticket 11.2: Market Watch Service
**Description:** Create and manage market watches.
**Files to create:**
- `backend/app/services/market_watch_service.py`
**Acceptance Criteria:**
- [ ] Methods: `create_watch(session_id, location, business_type)`, `update_watch(watch_id)`, `delete_watch(watch_id)`
- [ ] Store initial snapshot on creation
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_market_watch_service.py` - all tests pass

### Ticket 11.3: Change Detection Service
**Description:** Detect significant changes between snapshots.
**Files to create:**
- `backend/app/services/change_detection_service.py`
**Acceptance Criteria:**
- [ ] Detect: new competitors, closed businesses, significant rating changes (> 0.3), price changes
- [ ] Methods: `detect_changes(old_snapshot, new_snapshot)` returning list of changes with type and severity
- [ ] Filter by significance threshold
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_change_detection_service.py` - all tests pass

### Ticket 11.4: Alert Generation Service
**Description:** Generate alerts from detected changes.
**Files to create:**
- `backend/app/services/alert_service.py`
**Acceptance Criteria:**
- [ ] Generate alerts with: type, severity (info/warning/critical), message, data
- [ ] Methods: `generate_alerts(changes)`, `get_alerts(watch_id, since)`
- [ ] Store alerts in database
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_alert_service.py` - all tests pass

### Ticket 11.5: Market Monitoring Celery Tasks
**Description:** Background tasks for periodic monitoring.
**Files to create:**
- `backend/app/workers/monitoring_tasks.py`
**Acceptance Criteria:**
- [ ] Task: `update_market_watch(watch_id)` - update single watch
- [ ] Task: `process_all_watches()` - process all active watches (use Celery groups for parallelism)
- [ ] Celery beat schedule: daily updates (configurable)
- [ ] Error handling with retry
- [ ] Integration tests
**Validation:** Run task and verify snapshot creation

### Ticket 11.6: Monitoring API Endpoints
**Description:** API endpoints for monitoring management.
**Files to create:**
- `backend/app/api/routes/monitoring.py`
**Acceptance Criteria:**
- [ ] `POST /api/monitoring/watches` - create watch
- [ ] `GET /api/monitoring/watches` - list user's watches
- [ ] `GET /api/monitoring/watches/{id}/alerts` - get alerts for watch
- [ ] `DELETE /api/monitoring/watches/{id}` - stop watching
- [ ] API tests
**Validation:** Run `pytest tests/api/test_monitoring.py` - all tests pass

---

## SPRINT 12: Primary Research Tools & Final Integration
**Goal:** Enable primary research and integrate all tools into unified flagship feature.
**Demo:** Complete market research workflow demonstrating all capabilities.

### Ticket 12.1: Survey Builder Service
**Description:** Create service for building market research surveys.
**Files to create:**
- `backend/app/services/survey_service.py`
- `supabase/migrations/xxx_surveys.sql`
**Acceptance Criteria:**
- [ ] Survey templates by goal: market validation, pricing research, feature priority
- [ ] Question types: multiple choice, rating (1-5), open-ended
- [ ] Methods: `create_survey(goal, business_type)`, `get_survey(survey_id)`
- [ ] Database models for surveys, questions, responses
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_survey_service.py` - all tests pass

### Ticket 12.2: Survey Response Analyzer
**Description:** Analyze survey responses with statistical and AI analysis.
**Files to modify:**
- `backend/app/services/survey_service.py`
**Acceptance Criteria:**
- [ ] Calculate: response rates, distributions, correlations
- [ ] LLM-powered open-ended response analysis
- [ ] Methods: `analyze_responses(survey_id)`, `extract_insights(responses)`
- [ ] Unit tests with sample response data
**Validation:** Run `pytest tests/services/test_survey_service.py` - analysis tests pass

### Ticket 12.3: Interview Transcript Analyzer
**Description:** Analyze interview transcripts for themes and insights.
**Files to create:**
- `backend/app/services/interview_analysis_service.py`
**Acceptance Criteria:**
- [ ] LLM-powered transcript analysis
- [ ] Methods: `analyze_transcript(transcript_text)`, `extract_themes(transcripts)`
- [ ] Return: key themes, notable quotes, sentiment, actionable insights
- [ ] Unit tests
**Validation:** Run `pytest tests/services/test_interview_analysis_service.py` - all tests pass

### Ticket 12.4: Primary Research Agent Tools
**Description:** Create LangChain tools for primary research.
**Files to create:**
- `backend/app/tools/market_research/primary_research_tools.py`
**Acceptance Criteria:**
- [ ] `create_survey` tool
- [ ] `analyze_survey_responses` tool
- [ ] `analyze_interview_transcript` tool
- [ ] Comprehensive docstrings
- [ ] Integration tests
**Validation:** Run tools directly and verify structured output

### Ticket 12.5: Unified Tool Registry Update
**Description:** Register all tools in Market Research agent.
**Files to modify:**
- `backend/app/tools/market_research/agent.py`
**Acceptance Criteria:**
- [ ] Import and combine all tool lists (~37 tools total)
- [ ] Verify no tool name conflicts
- [ ] Update agent initialization
**Validation:** Agent initializes without errors with all tools

### Ticket 12.6: Enhanced System Prompt
**Description:** Update agent system prompt for comprehensive tool usage.
**Files to modify:**
- `backend/app/tools/market_research/prompts.py`
**Acceptance Criteria:**
- [ ] Comprehensive tool categorization (9 domains)
- [ ] Query routing patterns for each domain
- [ ] Response formatting guidelines
- [ ] LLM call budget awareness
- [ ] Context management for multi-tool queries
**Validation:** Agent correctly routes queries to appropriate tools

### Ticket 12.7: LLM Call Budget Manager
**Description:** Implement LLM call budgeting for cost control.
**Files to create:**
- `backend/app/core/llm_budget.py`
**Acceptance Criteria:**
- [ ] Track LLM calls per query/session
- [ ] Set max calls per comprehensive query (default: 10)
- [ ] Methods: `track_call(session_id)`, `get_remaining_budget(session_id)`, `is_budget_exceeded(session_id)`
- [ ] Unit tests
**Validation:** Run `pytest tests/core/test_llm_budget.py` - all tests pass

### Ticket 12.8: Parallel Tool Execution Optimizer
**Description:** Optimize agent for parallel independent tool execution.
**Files to modify:**
- `backend/app/tools/market_research/agent.py`
**Acceptance Criteria:**
- [ ] Identify tools that can run in parallel (no data dependencies)
- [ ] Group independent calls with `asyncio.gather()`
- [ ] Benchmark: comprehensive query < 45s average
**Validation:** Benchmark tests pass

### Ticket 12.9: Progress Streaming Enhancement
**Description:** Stream partial results during long analyses.
**Files to modify:**
- `backend/app/tools/market_research/agent.py`
**Acceptance Criteria:**
- [ ] Yield intermediate progress updates (tool completion, partial data)
- [ ] Users see progress, not just final answer
- [ ] Integration tests
**Validation:** Run agent query and verify progress messages in stream

### Ticket 12.10: End-to-End Integration Tests
**Description:** Comprehensive E2E tests for flagship feature.
**Files to create:**
- `tests/integration/test_market_research_e2e.py`
**Acceptance Criteria:**
- [ ] Test full market research query flow
- [ ] Test each analysis domain independently
- [ ] Test comprehensive report generation
- [ ] Test error handling and graceful degradation
- [ ] Test with "golden dataset" markets for accuracy validation
- [ ] All E2E tests pass
**Validation:** Run `pytest tests/integration/test_market_research_e2e.py` - all tests pass

### Ticket 12.11: Load & Performance Testing
**Description:** Load test the complete system.
**Files to create:**
- `tests/performance/test_load.py`
- `tests/performance/locustfile.py`
**Acceptance Criteria:**
- [ ] Test with 10 concurrent comprehensive queries
- [ ] Verify response times < 60s at p95
- [ ] Verify no memory leaks over sustained load
- [ ] Document performance baseline
**Validation:** Run load tests and verify metrics meet targets

---

## Appendix A: Tool Inventory Summary

### Existing Tools (12)
1. geocode_address
2. search_nearby_places
3. get_place_details
4. discover_neighborhood
5. get_location_demographics
6. analyze_competition_density
7. assess_foot_traffic_potential
8. calculate_market_viability
9. find_competitors
10. get_competitor_details
11. analyze_competitor_reviews
12. create_positioning_map

### New Tools (~25)
13. calculate_market_size (TAM/SAM/SOM)
14. get_industry_profile
15. analyze_labor_market
16. get_economic_indicators
17. analyze_industry_trends
18. get_seasonality_pattern
19. analyze_entry_timing
20. generate_swot_analysis
21. analyze_competitive_forces (Porter's)
22. estimate_market_shares
23. analyze_pricing_landscape
24. analyze_customer_sentiment
25. identify_customer_pain_points
26. map_customer_journey
27. build_customer_profile
28. project_revenue
29. calculate_break_even
30. run_scenario (what-if)
31. assess_financial_viability
32. analyze_trade_area
33. score_site
34. compare_locations
35. assess_market_risks
36. identify_opportunities
37. get_regulatory_requirements
38. generate_market_summary
39. create_shareable_snapshot
40. generate_full_report
41. create_survey
42. analyze_survey_responses
43. analyze_interview_transcript

### Total: ~43 tools across 9 domains

---

## Appendix B: Data Source Summary

### Current Sources
- Google Maps API (Places, Geocoding)
- Yelp Fusion API (Business, Reviews)
- US Census Bureau API (Demographics)

### New Sources
- Bureau of Labor Statistics (BLS) API - employment, wages, industry data
- Federal Reserve Economic Data (FRED) API - economic indicators
- GDELT Project - news, trends, sentiment (free)
- FCC Area API - coordinates to Census geography
- Bundled data files:
  - NAICS codes (Census Bureau)
  - Industry benchmarks (SBA, RMA, public sources)
  - Regulatory requirements (SBA, state sources)

---

## Appendix C: Success Metrics

1. **Comprehensiveness**: Tool answers any market research question a professional firm would address
2. **Accuracy**: Financial projections within 20% of industry benchmarks
3. **Speed**: Comprehensive analysis < 60 seconds (p95)
4. **Cost**: < $1 per comprehensive analysis (API + LLM costs)
5. **User Value**: NPS > 50 from pilot users
6. **Differentiation**: Unique capabilities (scenario modeling, shareable snapshots) not offered by competitors

---

## Appendix D: Testing Strategy

### Test Types

| Type | Purpose | Location |
|------|---------|----------|
| Unit Tests | Test individual functions | `tests/services/`, `tests/tools/` |
| Integration Tests | Test service interactions | `tests/integration/` |
| API Tests | Test HTTP endpoints | `tests/api/` |
| Contract Tests | Verify external API schemas | `tests/contracts/` |
| Load Tests | Performance under load | `tests/performance/` |
| Accuracy Tests | Validate calculations | `tests/accuracy/` |
| LLM Quality Tests | Evaluate AI output quality | `tests/llm/` |

### Golden Dataset
Create known markets for accuracy validation:
- Seattle coffee shop market (known TAM, competitor count)
- Austin restaurant market (known demographics, growth rate)
- NYC retail market (known foot traffic, rent benchmarks)

---

## Appendix E: Risk Mitigation

| Risk | Mitigation |
|------|------------|
| API costs exceed budget | Aggressive caching, LLM call budgeting, user-facing cost warnings |
| External API downtime | Graceful degradation, cached fallbacks, multi-source redundancy |
| LLM output quality varies | Structured prompts, output validation, fallback to rule-based |
| Data staleness | Freshness indicators in UI, regular cache invalidation |
| Scope creep | Sprint boundaries enforced, MVP focus per sprint |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Draft sprint plan |
| 2.0 | Post-Review | Incorporated system-architect feedback: reordered sprints, split large tickets, added rate limiting, consolidated services, added missing capabilities (labor market, pricing intelligence, scenario modeling), enhanced testing strategy |
