# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PHOW is an AI-powered analytics platform for small business owners. The MVP features a Location Scout tool using Google Maps and LLM analysis with a scalable, production-ready architecture.

## Architecture

### Stack
- **Frontend**: Next.js 15 with App Router, TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Python FastAPI with layered architecture (Repository → Service → API)
- **Database**: Supabase (PostgreSQL)
- **Caching**: Redis for external API response caching
- **Background Jobs**: Celery with Redis broker
- **LLM Framework**: LangChain with OpenAI and Anthropic support
- **External APIs**: Google Maps (Places, Geocoding)

### Architecture Patterns
- **Repository Pattern**: Database operations abstracted in `repositories/`
- **Service Layer**: Business logic in `services/`
- **Dependency Injection**: FastAPI Depends() for clean separation
- **Caching Decorator**: `@cached()` for automatic Redis caching
- **Retry Logic**: Tenacity for API resilience

## Coding Principles & Rules

**CRITICAL: Follow these principles for all code changes**

### 1. Succinctness & Minimalism
- **Write only what's necessary** - Avoid verbose code, unnecessary abstractions, or over-engineering
- **Prefer existing patterns** - Reuse existing code patterns rather than creating new ones
- **Remove redundant code** - If functionality already exists elsewhere, use it instead of duplicating
- **One-liners over multi-liners** - When appropriate, use concise Python/TypeScript idioms

### 2. Code Quality Standards
- **DRY (Don't Repeat Yourself)** - Never duplicate logic; extract to shared functions/services
- **Single Responsibility** - Each function/class should do one thing well
- **No dead code** - Remove unused imports, variables, functions, and comments
- **No commented-out code** - Delete it; git history preserves it if needed
- **No placeholder TODOs** - Either implement it or remove the comment

### 3. When Making Changes
- **Minimal diffs** - Make the smallest change necessary to achieve the goal
- **Edit existing code** - Prefer modifying existing files over creating new ones
- **Reuse existing utilities** - Check `core/`, `lib/`, and `services/` before creating new helpers
- **Follow existing patterns** - Match the style and structure of similar code in the codebase

### 4. Code Review Checklist
Before submitting code, ensure:
- ✅ No duplicate logic exists elsewhere
- ✅ All imports are used
- ✅ No unused variables or functions
- ✅ No commented-out code blocks
- ✅ Code follows existing patterns in the file
- ✅ Changes are minimal and focused
- ✅ No unnecessary abstractions or layers
- ✅ Code is formatted with Black (`black app/`)

### 5. Anti-Patterns to Avoid
- ❌ Creating new utility functions when existing ones suffice
- ❌ Adding multiple layers of abstraction for simple operations
- ❌ Writing verbose error handling when simple try/except works
- ❌ Adding extensive comments explaining obvious code
- ❌ Creating wrapper functions that only call another function
- ❌ Adding "future-proof" code that isn't needed now

### 6. Examples

**❌ Bad (verbose, redundant):**
```python
def get_user_data(user_id: str):
    # First, let's validate the user_id
    if user_id is None:
        return None
    if user_id == "":
        return None
    # Now let's fetch the user
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    # Return the user data
    return user
```

**✅ Good (succinct, clean):**
```python
def get_user_data(user_id: str):
    if not user_id:
        return None
    return db.query("SELECT * FROM users WHERE id = ?", user_id)
```

**❌ Bad (unnecessary abstraction):**
```python
class UserDataFetcher:
    def __init__(self, db):
        self.db = db
    
    def fetch(self, user_id):
        return self.db.query("SELECT * FROM users WHERE id = ?", user_id)

fetcher = UserDataFetcher(db)
user = fetcher.fetch(user_id)
```

**✅ Good (direct, simple):**
```python
user = db.query("SELECT * FROM users WHERE id = ?", user_id)
```

## Development Commands

### Frontend (from `frontend/`)
```bash
npm run dev          # Start dev server on port 3000
npm run build        # Build for production
npm run lint         # Run ESLint
```

### Backend (from `backend/`)
```bash
pip install -r requirements.txt              # Install dependencies
uvicorn app.main:app --reload --port 8000    # Start FastAPI server

# Celery worker (for background tasks)
celery -A app.workers.celery_app worker --loglevel=info

# Code formatting with Black
black app/                                    # Format all Python files
black --check app/                            # Check formatting without changes
```

### Docker (from root)
```bash
docker-compose up           # Start all services (API, DB, Redis, Celery)
docker-compose up backend   # Start only specific service
```

## Key File Locations

### Backend Core
- `backend/app/main.py` - FastAPI app with lifespan events
- `backend/app/core/llm.py` - LangChain LLM service (OpenAI/Anthropic)
- `backend/app/core/cache.py` - Redis cache manager with decorator
- `backend/app/core/tool_registry.py` - Tool registration system
- `backend/app/core/config.py` - Centralized configuration

### Backend Layers
- `backend/app/repositories/` - Database access layer
  - `conversation_repository.py` - Conversation CRUD operations
  - `message_repository.py` - Message CRUD operations
- `backend/app/services/` - Business logic layer
  - `chat_service.py` - Chat orchestration
  - `location_service.py` - Location analysis with caching
- `backend/app/api/routes/` - HTTP endpoints
  - `chat.py` - SSE streaming chat endpoint
  - `tools.py` - Tool management endpoints
- `backend/app/api/deps.py` - Dependency injection providers

### Tools & Workers
- `backend/app/tools/base.py` - Base tool interface
- `backend/app/tools/location_scout/` - Location Scout implementation
- `backend/app/workers/celery_app.py` - Celery configuration
- `backend/app/workers/tasks.py` - Background tasks (batch analysis, reports)

### Frontend
- `frontend/src/app/page.tsx` - Main page with chat interface
- `frontend/src/components/chat/` - Chat UI components
- `frontend/src/lib/api.ts` - Backend API client with SSE
- `frontend/src/lib/session.ts` - Anonymous session management

## Adding New Tools

1. Create tool directory: `backend/app/tools/your_tool/`
2. Implement tool class extending `BaseTool`:
   ```python
   from ..base import BaseTool, ToolContext, ToolResponse
   from ...core.llm import get_llm_service
   from ...services.your_service import YourService

   class YourTool(BaseTool):
       tool_id = "your_tool"
       name = "Your Tool"
       description = "Tool description"
       icon = "🔧"

       def __init__(self):
           self.service = YourService()
           self.llm = get_llm_service()

       async def process_stream(self, query: str, context: ToolContext):
           # Implementation with LangChain
           ...
   ```
3. Create service in `backend/app/services/your_service.py` with business logic
4. Register in `backend/app/main.py` lifespan:
   ```python
   ToolRegistry.register(YourTool())
   ```

## Using Caching

Decorate service methods with `@cached()`:
```python
from ...core.cache import cached

@cached(ttl=3600, key_prefix="geocode")
async def geocode_address(self, address: str):
    # Results cached for 1 hour
    return await self.maps_client.geocode(address)
```

## Background Tasks

Use Celery for long-running operations:
```python
from app.workers import analyze_location_batch

# Async task
result = analyze_location_batch.delay(addresses, business_type)
result_data = result.get()  # Blocks until complete
```

## Environment Variables

Copy `.env.example` in `backend/` and configure:
- **Supabase**: URL and service key
- **LLMs**: OpenAI and/or Anthropic API keys
- **Google Maps**: API key for Places/Geocoding
- **Redis**: URL for caching (default: localhost:6379)
- **Celery**: Broker and result backend URLs

## Database

Migrations: `supabase/migrations/`

Schema:
- `conversations` - Session-based chats (supports future user_id)
- `messages` - Chat messages with JSONB metadata

## Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Deployment Notes

- FastAPI: Deploy on Railway/Render/Fly.io
- Redis: Use managed Redis (Upstash, Redis Cloud)
- Celery: Run as separate dyno/service
- Frontend: Vercel/Netlify
- Database: Supabase hosted

## Market Research Agency Expectations & PHOW Differentiation

**Research Date**: 2026-01-24
**Relevance**: Strategic positioning of PHOW against traditional market research agencies to identify competitive advantages and inform feature development/marketing strategy.

### Traditional Market Research Agency Expectations

#### 1. Core Deliverables
Small business owners hiring traditional market research agencies typically expect:

- **Comprehensive Reports (30-100+ pages)**
  - Executive summary with key findings
  - Detailed methodology section
  - Data visualizations (charts, graphs, heat maps)
  - Competitive landscape analysis
  - Market sizing and opportunity assessment
  - Customer demographic profiles
  - Actionable recommendations section

- **Presentation Decks**
  - PowerPoint/PDF summary of findings
  - In-person or virtual presentation of results
  - Q&A session with research team

- **Raw Data Access** (varies by agency)
  - Survey responses, interview transcripts
  - Spreadsheets with demographic data
  - Source documentation

#### 2. Service Levels & Turnaround Times

**Typical Project Timelines:**
- Location/Site Selection Analysis: 2-4 weeks
- Competitor Research: 3-6 weeks
- Market Entry Feasibility Study: 4-8 weeks
- Customer Segmentation Study: 6-12 weeks
- Comprehensive Market Analysis: 8-16 weeks

**Consultation Process:**
- Initial discovery call (1-2 hours)
- Research proposal and scope definition (1 week)
- Midpoint check-in (optional)
- Final presentation and handoff
- Limited post-delivery support (1-2 follow-up calls)

**Pain Point**: Most small businesses need answers in days, not weeks or months. By the time research is delivered, market conditions may have changed.

#### 3. Pricing Models

**Common Structures:**
- **Project-Based**: $5,000 - $50,000+ per study
  - Location analysis: $8,000 - $15,000
  - Competitor analysis: $10,000 - $25,000
  - Market sizing: $12,000 - $30,000
  - Customer research (surveys/focus groups): $15,000 - $50,000+

- **Retainer Models**: $3,000 - $10,000/month (rare for small businesses)
- **Hourly Rates**: $150 - $400/hour for senior researchers

**Pain Point**: Pricing is prohibitively expensive for most small businesses. A single study can cost more than a small business owner's monthly revenue.

#### 4. Data Sources & Methodologies

**Primary Research:**
- Surveys (online, phone, in-person)
- Focus groups ($5,000 - $15,000 per group)
- Customer interviews
- Field observations

**Secondary Research:**
- Census data and demographic databases
- Industry reports (IBISWorld, Mintel, Nielsen)
- Competitor websites and public filings
- Trade association data
- Social media monitoring

**Pain Point**: Small businesses pay for methodologies designed for enterprises. They don't need statistically significant sample sizes of 1,000+ respondents.

#### 5. Communication & Consultation

**Expected Interactions:**
- Dedicated account manager or project lead
- Scheduled check-ins (bi-weekly or monthly)
- Email updates on project progress
- Final presentation with recommendations
- Limited post-project support (30-60 days)

**Pain Point**: Communication is one-way and scheduled. Business owners can't ask follow-up questions on-demand or iterate quickly.

#### 6. Key Pain Points with Traditional Agencies

1. **Cost Barrier**: Minimum projects start at $5,000-$10,000, putting professional research out of reach for most small businesses

2. **Time Lag**: Weeks or months between question and answer; market conditions change during research period

3. **One-Time Snapshot**: Research becomes outdated quickly; ongoing monitoring requires new expensive engagements

4. **Over-Engineering**: Enterprise methodologies (large sample sizes, academic rigor) applied to small business questions that need "good enough" answers fast

5. **Limited Iterations**: Each new question or pivot requires a new scope of work and additional fees

6. **Complexity**: Dense reports with academic language; actionable insights buried in methodology and caveats

7. **No Self-Service**: Complete dependency on agency timeline and availability

8. **Lack of Transparency**: Black box process; business owners don't see how conclusions were reached

9. **Minimum Project Sizes**: Agencies won't take small/quick projects; minimum engagements required

10. **Ongoing Costs**: Competitive monitoring, market updates, and new questions require continuous expensive engagements

### PHOW Differentiation Opportunities

#### 1. Speed & Real-Time Analysis

**Traditional Agency**: 2-16 weeks for deliverables
**PHOW Advantage**: Instant to minutes for most analyses

- Location Scout: Real-time analysis of foot traffic, demographics, competitors in seconds
- Market Validator: Immediate feasibility assessment for business ideas
- Competitor Analyzer: On-demand competitive intelligence, continuously updated
- Social Media Coach: Real-time content recommendations and trend analysis

**Marketing Message**: "Get answers in minutes, not months. Make decisions this week, not next quarter."

#### 2. Democratized Pricing

**Traditional Agency**: $5,000 - $50,000 per project
**PHOW Advantage**: Subscription model at $49-$199/month (estimated)

- Unlimited queries within subscription tier
- No per-project fees
- Pay for access, not per question
- ROI achievable with a single good decision

**Marketing Message**: "Professional market research for the price of a nice dinner. Access insights that used to cost $10,000+ for less than your monthly phone bill."

#### 3. Continuous Intelligence vs. Point-in-Time Snapshot

**Traditional Agency**: Static report, outdated within months
**PHOW Advantage**: Ongoing monitoring and fresh data

- Real-time competitor tracking (new reviews, menu changes, pricing)
- Updated demographic and foot traffic data
- Market condition changes reflected immediately
- Historical trending to see how markets evolve

**Marketing Message**: "Your market doesn't stand still. Why should your research? Get continuous intelligence, not outdated snapshots."

#### 4. Conversational Self-Service Interface

**Traditional Agency**: Schedule meetings, wait for responses, formal SOW for new questions
**PHOW Advantage**: Ask anything, anytime through chat interface

- No waiting for account manager availability
- Iterate and refine questions instantly
- Follow-up questions cost nothing extra
- Explore tangents and pivots freely
- Learn through conversation, not 100-page reports

**Marketing Message**: "Your AI market research team, available 24/7. No meetings required."

#### 5. Actionable Over Academic

**Traditional Agency**: Dense reports with methodology, caveats, and buried insights
**PHOW Advantage**: Direct answers optimized for decisions, not dissertations

- Clear recommendations without academic hedging
- Visual widgets (maps, charts, competitor cards) over text walls
- Confidence levels on insights (high/medium/low)
- "So what?" answers automatically included

**Marketing Message**: "Get answers, not reports. We tell you what to do, not just what the data says."

#### 6. Multi-Tool Synergy (Unique to AI Platforms)

**Traditional Agency**: Siloed projects (location study separate from competitor analysis)
**PHOW Advantage**: Integrated insights across all tools

- Location Scout factors in competitor proximity automatically
- Market Validator references location demographics
- Social Media Coach informed by competitor content strategies
- Review Responder learns from competitor review patterns

**Marketing Message**: "All your market intelligence, connected. Insights that traditional agencies would charge separately for, working together automatically."

#### 7. Impossible-Without-AI Features

These capabilities are economically unfeasible with human-only services:

1. **Hyper-Local Granularity**: Analyze every street corner in a city (traditional agencies charge per location analyzed)

2. **Unlimited What-If Scenarios**: "What if I open at this location vs. that one?" - run 50 scenarios in an hour

3. **Real-Time Review Monitoring**: Track all competitor reviews across platforms continuously (agencies charge $2,000+/month for social listening)

4. **Personalized Benchmarking**: Compare your business to contextually similar competitors, not generic industry averages

5. **Predictive Trending**: AI pattern recognition on emerging market signals humans would miss

6. **Multi-Language Analysis**: Analyze reviews, social media, and markets in any language without specialized translators

7. **Instant Competitive Response**: Competitor launches promotion → PHOW alerts you and suggests counter-strategy within minutes

**Marketing Message**: "Market intelligence superpowers that didn't exist 5 years ago. AI makes the impossible affordable."

#### 8. Transparent Learning Process

**Traditional Agency**: "Trust us, we're experts" - black box methodology
**PHOW Advantage**: Show your work

- Explain data sources for each insight
- Display confidence levels and caveats
- Allow users to dig into underlying data
- Cite specific reviews, demographics, or competitor data
- Users learn market research principles while using tools

**Marketing Message**: "See exactly where insights come from. Learn market research while you use it."

### Feature Prioritization Based on Agency Gaps

#### High-Priority Features to Emphasize

1. **Speed Metrics**: Show "Analysis completed in 12 seconds" - make speed visceral
2. **Cost Comparison Widget**: "This analysis would cost $X from a traditional agency"
3. **Real-Time Badges**: "Data updated 3 minutes ago" - emphasize freshness
4. **Iteration Counter**: "You've run 47 analyses this month - that would be $94,000 with traditional research"
5. **Confidence Scores**: Clear indicators when insights are strong vs. speculative
6. **Export to Action**: One-click export insights to actionable formats (pitch deck, business plan section, social posts)

#### Gaps in Current PHOW Offerings (Opportunities)

Based on traditional agency deliverables that PHOW could provide:

1. **Market Sizing Tool**: "How many potential customers exist in this area?" - combine census data + Google traffic + business category filters

2. **Trend Forecasting**: Historical data analysis to predict future market conditions (e.g., "foot traffic increasing 15% year-over-year")

3. **Customer Profile Generator**: Synthesize demographic data into personas ("Your typical customer: 35-44, HHI $75k-100k, interested in...")

4. **Pricing Optimizer**: Analyze competitor pricing + local income levels to suggest optimal price points

5. **Risk Assessment**: Quantify market entry risks (saturation, economic trends, regulatory environment)

6. **Exportable Reports**: Generate professional PDF reports for bank loans, investor pitches, or internal planning (even if PHOW users don't need them, stakeholders might)

7. **Historical Snapshots**: Save point-in-time analyses to compare "market conditions when I launched vs. now"

8. **Alert System**: Proactive notifications when significant market changes occur (new competitor, demographic shift, viral negative review)

### Positioning Strategy Recommendations

#### Target Messaging by Use Case

**For Pre-Launch Businesses:**
- "Validate your business idea in an afternoon, not after months of expensive research"
- "Find the perfect location with data, not gut instinct - for less than $100"
- Compare PHOW to: $15,000 location feasibility study

**For Existing Small Businesses:**
- "Know what your competitors are doing before your customers tell you"
- "Monitor your market 24/7 for the cost of a single consulting hour"
- Compare PHOW to: $5,000/month marketing agency retainer

**For Multi-Location Businesses:**
- "Analyze 50 potential locations in an hour. Traditional agencies charge per location."
- "Continuous competitive intelligence across all your markets"
- Compare PHOW to: $25,000 per location analysis

#### Competitive Positioning Statement

**PHOW = Professional Market Research Democratized**

"Traditional market research agencies charge $10,000-$50,000 for insights that take weeks to deliver and are outdated within months. PHOW gives you the same caliber of intelligence - location analysis, competitive research, market validation - instantly, continuously, and for less than $200/month. It's like having a $100,000/year market research analyst on your team, available 24/7."

#### What NOT to Compete On

- Statistical rigor (agencies have PhDs; emphasize "good enough fast" over "perfect eventually")
- Custom primary research (surveys, focus groups) - stick to secondary data + AI synthesis
- Industry-specific deep expertise (agencies have vertical specialists)
- High-touch consultation (PHOW is self-service; feature, not bug)

#### What TO Compete On

- Speed (100x faster)
- Cost (50-100x cheaper)
- Accessibility (24/7 self-service)
- Freshness (real-time vs. stale)
- Iteration velocity (unlimited questions)
- Integrated intelligence (tools working together)

### Success Metrics to Track

To validate differentiation strategy, measure:

1. **Time-to-Insight**: Average seconds from query to actionable answer
2. **Cost-per-Insight**: Subscription cost / number of analyses run
3. **Iteration Rate**: How many follow-up questions users ask (high = good, shows confidence)
4. **Perceived Value**: Survey users on "What would this have cost from an agency?"
5. **Decision Velocity**: Time from signup to business decision made
6. **Retention by Use Case**: Which user segments stick vs. churn

### Sources & References

This research synthesizes established industry knowledge from:
- Market research industry pricing standards (2020-2026)
- Small business market research best practices literature
- Competitive analysis of traditional agencies vs. AI-powered platforms
- Common pain points documented in small business research accessibility studies
- SaaS pricing models for SMB analytics tools

**Note**: This analysis is based on industry patterns and standards as of January 2026. For specific competitive intelligence on named agencies, additional proprietary research would be required.
