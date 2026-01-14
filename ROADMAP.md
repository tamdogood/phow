# PHOW Tool Expansion Roadmap

## Vision

Transform PHOW from a "one-time planning tool" into an **indispensable daily companion** for small business owners. The goal is to solve high-frequency pain points that business owners face every day.

---

## Current State

### Completed Tools

| Tool | Category | Usage Frequency | Status |
|------|----------|-----------------|--------|
| Location Scout | Pre-launch | One-time | ✅ Built |
| Market Validator | Pre-launch | One-time | ✅ Built |
| Competitor Analyzer | Strategic | Monthly | ✅ Built |
| **Social Media Coach** | Daily Operations | **Daily** | ✅ Built |

### Tech Stack
- **Backend**: FastAPI + LangChain + LangGraph ReAct agents
- **Frontend**: Next.js 15 + Tailwind CSS (Dark theme)
- **Database**: Supabase (PostgreSQL)
- **Caching**: Redis
- **External APIs**: Google Maps, Yelp, OpenWeatherMap

---

## Remaining Build Plan

### Tier 1: Daily Drivers (High Priority)

#### 1. Review Responder
*"Help me respond to this review"*

**Why It's Critical:**
- 89% of consumers read business responses to reviews
- Bad responses hurt more than no response
- Owners spend hours crafting responses

**Capabilities:**
- AI-generated response drafts (3 tone options: professional, friendly, apologetic)
- Sentiment analysis of the review
- Key issues extraction from review text
- Response templates library
- Multi-platform support (Google, Yelp, Facebook)

**Data Sources:**
- Google Places API (existing)
- Yelp Fusion API (existing)
- NLP sentiment analysis (LLM-based)

**Widget Design:**
```
┌─────────────────────────────────────────────────┐
│ 📝 Review Response Assistant                    │
├─────────────────────────────────────────────────┤
│ Review: "The food was cold and service slow..." │
│ Sentiment: 😞 Negative | Issues: Food temp, Wait│
├─────────────────────────────────────────────────┤
│ Response Options:                               │
│ [Professional] [Friendly] [Apologetic]          │
│                                                 │
│ "Dear [Customer], Thank you for taking the time │
│ to share your feedback. We sincerely apologize  │
│ for the issues with..."                         │
│                                    [📋 Copy]    │
└─────────────────────────────────────────────────┘
```

**Implementation Files:**
```
backend/app/tools/review_responder/
├── __init__.py
├── tool.py
├── agent.py
├── agent_tools.py
├── prompts.py
└── sentiment_analyzer.py

frontend/src/components/tools/ReviewResponderWidget.tsx
```

**Estimated Effort:** Medium (2-3 days)

---

#### 2. Local Pulse
*"What's happening near me that affects my business?"*

**Why It's Critical:**
- Local events = foot traffic opportunities
- Weather impacts all retail/service businesses
- Competitors' moves need quick response
- No competitor offers this combined view

**Capabilities:**
- Daily weather briefing with business impact analysis
- Local events calendar (next 7 days)
- Construction/road closure alerts
- Competitor activity monitoring
- Community happenings and festivals
- Holiday and seasonal opportunity alerts

**Data Sources:**
- OpenWeatherMap API (already integrated)
- Eventbrite API
- Meetup API
- Local news APIs (NewsAPI)
- Google Places (competitor monitoring)

**Widget Design:**
```
┌─────────────────────────────────────────────────┐
│ 📍 Local Pulse - Austin, TX                     │
│ Monday, January 13, 2025                        │
├─────────────────────────────────────────────────┤
│ 🌤️ Weather                                      │
│ 72°F Sunny - Great for outdoor seating!         │
│ Business Impact: ✅ Positive                    │
├─────────────────────────────────────────────────┤
│ 📅 This Week                                    │
│ • Tue: Farmers Market (2 blocks away)           │
│ • Thu: SXSW Pre-Party @ Convention Center       │
│ • Sat: Marathon - expect road closures          │
├─────────────────────────────────────────────────┤
│ 🔔 Alerts                                       │
│ • Competitor "Joe's Coffee" changed hours       │
│ • Road work on 6th St until Friday              │
├─────────────────────────────────────────────────┤
│ 💡 Opportunities                                │
│ • National Coffee Day is in 3 days              │
│ • Marathon = hungry runners nearby              │
└─────────────────────────────────────────────────┘
```

**Implementation Files:**
```
backend/app/tools/local_pulse/
├── __init__.py
├── tool.py
├── agent.py
├── agent_tools.py
├── prompts.py
├── news_client.py
└── alerts_aggregator.py

frontend/src/components/tools/LocalPulseWidget.tsx
```

**Estimated Effort:** Medium-High (3-4 days)

---

### Tier 2: Weekly Tools (Medium Priority)

#### 3. Review Sentinel
*"What are people saying about me this week?"*

**Capabilities:**
- Weekly review summary across all platforms
- Sentiment trend vs last week
- Common themes in reviews (NLP extraction)
- Rating trajectory visualization
- Competitor review comparison
- AI-suggested improvement areas

**Widget:** Weekly dashboard with metrics, trend charts, actionable insights

**Estimated Effort:** Medium (2-3 days)

---

#### 4. Promo Planner
*"What should I promote this week?"*

**Capabilities:**
- AI-suggested promotions based on:
  - Upcoming local events
  - Weather forecast
  - Competitor activity
  - Historical patterns
- Discount strategy recommendations
- Bundle suggestions
- Social media promo templates
- Email/SMS copy generation

**Widget:** Weekly promo calendar with suggestions, ready-to-use copy

**Estimated Effort:** Medium (2-3 days)

---

#### 5. Customer Communicator
*"Help me respond to customer messages professionally"*

**Capabilities:**
- AI message drafts for common scenarios:
  - Booking confirmations
  - Cancellation handling
  - Complaint resolution
  - Price quote responses
  - Follow-up messages
- Tone adjustment (formal/casual/friendly)
- Multi-language support
- Template library with customization

**Widget:** Message composer with AI suggestions, template picker

**Estimated Effort:** Low-Medium (1-2 days)

---

### Tier 3: Monthly Strategic Tools (Lower Priority)

| Tool | Description | Effort |
|------|-------------|--------|
| Pricing Advisor | AI-powered pricing recommendations based on competitors, demand | Medium |
| Growth Advisor | Quarterly business health check and growth recommendations | High |
| Cash Flow Forecaster | Revenue prediction based on events, weather, seasonality | High |

---

## Implementation Priority Queue

```
NEXT UP (Sprint 1):
├── Review Responder     ← Start here
└── Local Pulse

FOLLOWING (Sprint 2):
├── Review Sentinel
├── Promo Planner
└── Customer Communicator

BACKLOG (Sprint 3+):
├── Pricing Advisor
├── Growth Advisor
└── Cash Flow Forecaster
```

---

## API Keys Required

| API | Purpose | Status | Pricing |
|-----|---------|--------|---------|
| OpenWeatherMap | Weather data | ✅ Added | Free: 1000/day |
| Google Maps | Location, competitors | ✅ Added | Pay-per-use |
| Yelp Fusion | Reviews, businesses | ✅ Added | Free: 5000/day |
| Eventbrite | Local events | 🔲 Needed | Free tier |
| NewsAPI | Local news | 🔲 Needed | Free: 100/day |
| Meetup | Community events | 🔲 Optional | Free tier |

---

## Shared Patterns

### Backend Tool Structure
```
backend/app/tools/{tool_name}/
├── __init__.py           # Exports
├── tool.py               # BaseTool implementation
├── agent.py              # LangGraph ReAct agent
├── agent_tools.py        # LangChain tools
├── prompts.py            # System prompts
└── {api_client}.py       # External API clients
```

### Frontend Widget Pattern
```typescript
// Backend emits widget data in streaming response
yield f"\n<!--{WIDGET_TYPE}_DATA:{json.dumps(data)}-->\n"

// Frontend parses in ChatMessage.tsx
const match = content.match(/<!--{WIDGET_TYPE}_DATA:(.*?)-->/s);

// Widget component renders the data
components/tools/{ToolName}Widget.tsx
```

### Tool Registration
```python
# backend/app/main.py
from .tools.{tool_name} import {ToolName}Tool
ToolRegistry.register({ToolName}Tool())
```

---

## Success Metrics

| Metric | Target | Why It Matters |
|--------|--------|----------------|
| Daily Active Users (DAU) | 30% of total users | Daily tools drive engagement |
| Tool Usage per Session | 2+ tools | Cross-tool usage = stickiness |
| Return Rate (7-day) | 60%+ | Users coming back weekly |
| Time to First Value | < 2 min | Quick wins = retention |

### Per-Tool Success Metrics

| Tool | Success Metric | Target |
|------|----------------|--------|
| Social Media Coach | Posts created using suggestions | 3+ per week |
| Review Responder | Responses drafted | 2+ per week |
| Local Pulse | Daily check-ins | 5+ per week |
| Review Sentinel | Weekly dashboard views | 1+ per week |

---

## Database Schema Additions (Future)

```sql
-- Review response tracking
CREATE TABLE review_responses (
    id UUID PRIMARY KEY,
    business_profile_id UUID REFERENCES business_profiles,
    platform TEXT NOT NULL,  -- 'google', 'yelp', 'facebook'
    original_review TEXT NOT NULL,
    review_rating INTEGER,
    generated_response TEXT NOT NULL,
    tone TEXT,  -- 'professional', 'friendly', 'apologetic'
    copied BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Local events cache
CREATE TABLE local_events_cache (
    id UUID PRIMARY KEY,
    location_key TEXT NOT NULL,
    events JSONB NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

-- Competitor monitoring
CREATE TABLE competitor_alerts (
    id UUID PRIMARY KEY,
    business_profile_id UUID REFERENCES business_profiles,
    competitor_name TEXT NOT NULL,
    alert_type TEXT NOT NULL,  -- 'hours_change', 'new_review', 'price_change'
    alert_data JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Competitive Advantage

| Feature | PHOW | Yelp for Business | Google Business | Buffer/Hootsuite |
|---------|------|-------------------|-----------------|------------------|
| Social content ideas | ✅ AI-powered | ❌ | ❌ | ❌ |
| Weather-aware suggestions | ✅ | ❌ | ❌ | ❌ |
| Local events awareness | ✅ | ❌ | ❌ | ❌ |
| Review response AI | ✅ Multiple tones | ❌ | ❌ | ❌ |
| Competitor intelligence | ✅ | ✅ Limited | ❌ | ❌ |
| All-in-one for SMB | ✅ | ❌ | ❌ | ❌ |

**Unique Value:** PHOW is the only tool that combines local awareness (weather, events, trends) with AI-powered content creation specifically for small business owners.

---

## Next Steps

1. **Implement Review Responder** - High-value, leverages existing Yelp/Google integrations
2. **Implement Local Pulse** - Unique differentiator, builds on weather client
3. **Add Eventbrite/NewsAPI integrations** - Expands data sources
4. **User testing** - Validate daily usage patterns
5. **Iterate based on feedback** - Refine tool capabilities

---

*Last Updated: January 13, 2025*
