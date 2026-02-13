# Review Management & Aggregation Platform - Complete Technical Specification

## Context

Local businesses currently check Google, Yelp, Facebook, and industry-specific platforms separately to monitor their reputation. BrightLocal's Grow package runs $44/month per location, while EmbedSocial starts at $259/month - leaving single-location small businesses underserved. This spec covers building a centralized review aggregation, response management, and sentiment tracking system within PHOW, priced at $29-44/month.

---

## 1. Platform API Integrations

### 1.1 Google Business Profile API (Primary)

Google sunsetted the legacy "My Business" REST API in April 2022. The replacement is the **Google Business Profile API**.

**APIs Required:**

| API | Purpose | Base URL |
|-----|---------|----------|
| Business Profile API | Location management | `https://mybusinessbusinessinformation.googleapis.com/v1` |
| Account Management API | Account linking | `https://mybusinessaccountmanagement.googleapis.com/v1` |
| Business Profile Performance API | Metrics | `https://businessprofileperformance.googleapis.com/v1` |

**Key Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/accounts` | Discover user's business accounts after OAuth |
| `GET` | `/accounts/{account}/locations` | List all locations for an account |
| `GET` | `/accounts/{account}/locations/{location}/reviews` | Fetch reviews (paginated, max 50/page via `pageToken`) |
| `GET` | `/accounts/{account}/locations/{location}/reviews/{review}` | Single review detail |
| `PUT` | `/accounts/{account}/locations/{location}/reviews/{review}/reply` | Post reply (`{"comment": "..."}`) |
| `DELETE` | `/accounts/{account}/locations/{location}/reviews/{review}/reply` | Delete reply |

**OAuth 2.0:**
- **Scope**: `https://www.googleapis.com/auth/business.manage`
- **Flow**: Authorization Code
- **Token lifetime**: Access = 1 hour, Refresh = long-lived
- **Redirect URI**: `/api/auth/callback/google`
- **Consent**: Must be Google-verified for production (Testing mode supports up to 100 users)

**Rate Limits**: 60 requests/minute/project (increase via GCP Console)

**Webhooks**: Not natively supported for reviews. Must poll. Google Cloud Pub/Sub via Notifications API is an alternative but requires separate GCP topic setup.

**Polling Strategy**: Every 15 min (active businesses), every 2 hours (inactive)

### 1.2 Facebook/Meta Graph API

**Base URL**: `https://graph.facebook.com/v19.0`

**Key Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/{page_id}/ratings?fields=reviewer,rating,review_text,created_time,has_rating` | Fetch recommendations |
| `POST` | `/{rating_id}/comments` | Reply to recommendation (`{"message": "..."}`) |
| `GET` | `/{page_id}?fields=name,overall_star_rating,rating_count` | Page aggregate data |
| `GET` | `/me/accounts?fields=access_token,name,id` | Get Page tokens from User token |

**OAuth 2.0:**
- **Permissions**: `pages_read_engagement`, `pages_manage_engagement`, `pages_show_list`, `pages_read_user_content`
- **Token chain**: User Access Token (1 hour) -> Long-lived User Token (60 days) -> Page Access Token (perpetual)
- **App Review**: Required by Meta for `pages_read_user_content` permission

**Webhooks**: Subscribe to `feed` field on Page for real-time new review notifications. Webhook URL: `/api/webhooks/facebook` with challenge-response verification.

**Rate Limits**: 200 calls/user/hour

**Polling Strategy**: Real-time via webhook + every 30 min fallback

**Note**: Facebook uses "Recommendations" (yes/no + optional text) since 2018, not traditional star ratings.

### 1.3 Yelp Fusion API

**Existing client**: `backend/app/tools/competitor_analyzer/yelp_client.py` - extend this.

**Key Endpoints:**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/v3/businesses/matches` | Match user's business to Yelp listing |
| `GET` | `/v3/businesses/{id}` | Business details (already implemented) |
| `GET` | `/v3/businesses/{id}/reviews` | Reviews (already implemented) |

**Critical Limitations:**
- Returns **max 3 reviews** per business. Hard API limit.
- **No reply via API** - owners must use Yelp for Business Owners portal.
- Scraping explicitly prohibited by TOS.

**Practical Approach:**
- Use 3 reviews as preview + aggregate data (rating, review_count)
- Deep-link to Yelp business page for full management
- Consider Yelp Knowledge API ($500+/mo) only if revenue justifies it later

**Rate Limits**: 5,000 calls/day (already configured in rate limiter)

**Polling Strategy**: Every 6 hours (active), every 24 hours (inactive)

### 1.4 Industry-Specific Platforms

| Platform | API Status | Approach |
|----------|-----------|----------|
| TripAdvisor | Content API (partnership required) | Apply for partnership; read-only aggregation |
| Healthgrades | No public API | Manual import only |
| HomeAdvisor/Angi | No public API | Skip for MVP |

**Fallback for platforms without APIs:**
- Manual "Add Review" form (paste text)
- CSV/JSON bulk import
- Browser extension (Phase 4+)

---

## 2. OAuth & Account Linking

### 2.1 Flow Architecture

1. Frontend calls `POST /api/auth/connect/{platform}` with `session_id`/`user_id`
2. Backend generates OAuth URL with encrypted state param (`{session_id, platform, timestamp}`) and returns it
3. Frontend redirects user to OAuth URL
4. Platform redirects to `GET /api/auth/callback/{platform}` with auth code
5. Backend exchanges code for tokens, encrypts and stores in DB
6. Backend redirects to `/reviews?connected={platform}`

### 2.2 Token Security

- **Encryption**: Fernet symmetric encryption (`cryptography` library)
- **Key storage**: `OAUTH_ENCRYPTION_KEY` env var, never in DB
- **Refresh**: Celery beat task every 30 min checks for tokens expiring within 1 hour

### 2.3 Scopes Per Platform

| Platform | OAuth? | Scopes | Read Reviews | Reply |
|----------|--------|--------|-------------|-------|
| Google | Yes | `business.manage` | Yes | Yes |
| Facebook | Yes | `pages_read_engagement`, `pages_manage_engagement`, `pages_show_list`, `pages_read_user_content` | Yes | Yes |
| Yelp | No (API key) | N/A | 3 only | No |
| TripAdvisor | Partnership key | N/A | Yes | No |

### 2.4 Re-authorization

When token refresh fails:
1. Set `platform_connections.status = 'disconnected'` with `error_message`
2. Create in-app alert: "Your {platform} connection needs re-authorization"
3. User clicks "Reconnect" -> re-triggers OAuth flow, updates existing record

---

## 3. Database Schema

**Migration file**: `supabase/migrations/006_review_management.sql`

### 3.1 `platform_connections`

```sql
CREATE TABLE platform_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    platform TEXT NOT NULL,
    platform_account_id TEXT,
    platform_location_id TEXT,
    platform_business_name TEXT,
    access_token_encrypted BYTEA,
    refresh_token_encrypted BYTEA,
    token_expires_at TIMESTAMPTZ,
    scopes TEXT[],
    status TEXT NOT NULL DEFAULT 'active',  -- active/disconnected/expired/error
    error_message TEXT,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_profile_id, platform)
);

CREATE INDEX idx_platform_connections_profile ON platform_connections(business_profile_id);
CREATE INDEX idx_platform_connections_status ON platform_connections(status);
```

### 3.2 `reviews` (Unified Schema)

```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    platform TEXT NOT NULL,
    platform_review_id TEXT,
    reviewer_name TEXT,
    reviewer_avatar_url TEXT,
    rating DECIMAL(2, 1),        -- 1.0-5.0 (NULL for FB recommendations)
    is_recommended BOOLEAN,       -- Facebook yes/no
    review_text TEXT,
    review_url TEXT,
    published_at TIMESTAMPTZ,
    sentiment TEXT,               -- positive/negative/mixed/neutral
    sentiment_score DECIMAL(3, 2),-- -1.00 to 1.00
    key_themes TEXT[],
    language TEXT DEFAULT 'en',
    is_responded BOOLEAN DEFAULT FALSE,
    response_id UUID,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_profile_id, platform, platform_review_id)
);

CREATE INDEX idx_reviews_profile ON reviews(business_profile_id);
CREATE INDEX idx_reviews_platform ON reviews(platform);
CREATE INDEX idx_reviews_sentiment ON reviews(sentiment);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_published ON reviews(published_at DESC);
CREATE INDEX idx_reviews_responded ON reviews(is_responded);
```

### 3.3 `review_responses`

```sql
CREATE TABLE review_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews ON DELETE CASCADE,
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    draft_text TEXT NOT NULL,
    published_text TEXT,
    tone TEXT,                     -- professional/friendly/apologetic/empathetic
    status TEXT NOT NULL DEFAULT 'draft',  -- draft/approved/published/failed
    published_at TIMESTAMPTZ,
    error_message TEXT,
    ai_generated BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_review_responses_review ON review_responses(review_id);
CREATE INDEX idx_review_responses_status ON review_responses(status);
```

### 3.4 `review_sentiment_analyses`

```sql
CREATE TABLE review_sentiment_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL REFERENCES reviews ON DELETE CASCADE,
    sentiment TEXT NOT NULL,
    sentiment_score DECIMAL(3, 2) NOT NULL,
    emotional_tone TEXT,          -- angry/disappointed/frustrated/neutral/satisfied/enthusiastic
    key_issues TEXT[],
    positive_themes TEXT[],
    negative_themes TEXT[],
    urgency_level TEXT DEFAULT 'normal',  -- low/normal/high/critical
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    model_version TEXT,
    UNIQUE(review_id)
);

CREATE INDEX idx_sentiment_review ON review_sentiment_analyses(review_id);
CREATE INDEX idx_sentiment_urgency ON review_sentiment_analyses(urgency_level);
```

### 3.5 `review_alerts`

```sql
CREATE TABLE review_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    review_id UUID REFERENCES reviews ON DELETE SET NULL,
    alert_type TEXT NOT NULL,     -- new_review/negative_review/rating_drop/trend_change/unanswered/connection_error
    severity TEXT NOT NULL DEFAULT 'info',  -- info/warning/critical
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_profile ON review_alerts(business_profile_id);
CREATE INDEX idx_alerts_read ON review_alerts(is_read);
CREATE INDEX idx_alerts_created ON review_alerts(created_at DESC);
```

### 3.6 `review_metrics`

```sql
CREATE TABLE review_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    platform TEXT,                -- NULL for aggregate, platform name for per-platform
    period TEXT NOT NULL,         -- daily/weekly/monthly
    period_start DATE NOT NULL,
    total_reviews INT DEFAULT 0,
    new_reviews INT DEFAULT 0,
    average_rating DECIMAL(2, 1),
    positive_count INT DEFAULT 0,
    negative_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,
    mixed_count INT DEFAULT 0,
    responded_count INT DEFAULT 0,
    avg_response_time_hours DECIMAL(6, 1),
    top_themes TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(business_profile_id, platform, period, period_start)
);

CREATE INDEX idx_metrics_profile ON review_metrics(business_profile_id);
CREATE INDEX idx_metrics_period ON review_metrics(period, period_start);
```

### 3.7 `subscriptions`

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_profile_id UUID NOT NULL REFERENCES business_profiles ON DELETE CASCADE,
    user_id UUID,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan TEXT NOT NULL DEFAULT 'free',  -- free/basic/pro
    status TEXT NOT NULL DEFAULT 'active',
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_profile ON subscriptions(business_profile_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
```

---

## 4. Backend Architecture

### 4.1 New File Structure

```
backend/app/
├── clients/
│   ├── google_business_client.py    # NEW
│   └── facebook_client.py           # NEW
├── tools/
│   └── review_manager/              # NEW
│       ├── __init__.py
│       ├── tool.py
│       ├── agent.py
│       ├── agent_tools.py
│       └── prompts.py
├── repositories/
│   ├── review_repository.py                # NEW
│   ├── platform_connection_repository.py   # NEW
│   ├── review_response_repository.py       # NEW
│   ├── review_alert_repository.py          # NEW
│   └── review_metrics_repository.py        # NEW
├── services/
│   ├── review_service.py                   # NEW
│   ├── review_sync_service.py              # NEW
│   ├── review_sentiment_service.py         # NEW
│   ├── review_notification_service.py      # NEW
│   └── oauth_service.py                    # NEW
├── api/routes/
│   ├── reviews.py                          # NEW
│   └── oauth.py                            # NEW
├── core/
│   └── encryption.py                       # NEW
└── workers/
    └── tasks.py                            # EXTEND
```

### 4.2 API Clients

Follow the exact patterns from:
- `backend/app/tools/location_scout/google_maps.py` (httpx singleton, @cached, structured logging)
- `backend/app/tools/competitor_analyzer/yelp_client.py` (graceful degradation with `self.enabled`, always return expected type)

Both `GoogleBusinessClient` and `FacebookClient`:
- Singleton `httpx.AsyncClient` via class variable
- Bearer auth via per-request headers (tokens vary per user)
- `@cached()` on read endpoints (reviews: 30 min TTL)
- `tenacity` retry with exponential backoff on HTTP errors
- Rate limiting via existing `RateLimiter`
- `_normalize_review(raw)` method to map platform-specific fields to unified schema

### 4.3 Repository Layer

Extend `BaseRepository` (from `backend/app/repositories/base.py`). Key methods:

**ReviewRepository**: `upsert()`, `get_by_profile()` (with filters), `get_unresponded()`, `get_stats()`
**PlatformConnectionRepository**: `create()`, `get_by_profile()`, `get_active()`, `update_tokens()`, `mark_disconnected()`
**ReviewResponseRepository**: `create_draft()`, `update()`, `get_by_review()`, `mark_published()`
**ReviewAlertRepository**: `create()`, `get_unread()`, `mark_read()`, `dismiss()`
**ReviewMetricsRepository**: `upsert_metrics()`, `get_by_period()`

### 4.4 Service Layer

**ReviewService** (core orchestration):
- `get_dashboard_data()` - aggregate stats + recent reviews + alerts
- `publish_response()` - decrypt token -> call platform API -> update status
- `generate_ai_response()` - uses existing LLM service

**ReviewSyncService** (platform sync):
- `sync_connection()` - fetch reviews from platform, upsert, trigger sentiment analysis
- `sync_all_active()` - iterate all active connections
- `initial_import()` - paginate all historical reviews on first connect

**ReviewSentimentService** (AI analysis):
- `analyze()` - keyword-based fast pass (reuse existing `analyze_review_sentiment` from `review_responder/agent_tools.py`), LLM for ambiguous cases
- `analyze_batch()` - process multiple reviews efficiently

**OAuthService** (OAuth management):
- `initiate_flow()` - generate OAuth URL with encrypted state
- `handle_callback()` - exchange code for tokens, store encrypted
- `refresh_token()` - preemptive token refresh
- `disconnect()` - revoke and delete tokens

### 4.5 API Routes

**Reviews** (`/api/reviews`):

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/dashboard` | Dashboard data (stats, recent reviews, alerts) |
| `GET` | `/` | Review list with filters (platform, rating, sentiment, responded) |
| `GET` | `/{review_id}` | Single review detail |
| `POST` | `/{review_id}/respond` | Generate AI response draft |
| `PATCH` | `/responses/{response_id}` | Edit response draft |
| `POST` | `/responses/{response_id}/publish` | Publish to platform |
| `POST` | `/sync` | Trigger manual sync |
| `GET` | `/alerts` | Get alerts |
| `PATCH` | `/alerts/{alert_id}/dismiss` | Dismiss alert |
| `GET` | `/metrics` | Get metrics by period |

**OAuth** (`/api/auth`):

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/connect/{platform}` | Initiate OAuth, return redirect URL |
| `GET` | `/callback/{platform}` | OAuth callback handler |
| `DELETE` | `/disconnect/{platform}` | Disconnect platform |
| `GET` | `/connections` | List connected platforms |

### 4.6 Dependency Injection

Add to `backend/app/api/deps.py`:

```python
def get_review_service(db: Client = Depends(get_supabase)) -> ReviewService:
    return ReviewService(db)

def get_oauth_service(db: Client = Depends(get_supabase)) -> OAuthService:
    return OAuthService(db)
```

### 4.7 Rate Limiting

Add to `API_LIMITS` in `backend/app/core/rate_limiter.py`:

```python
"google_business": (60, 60),    # 60 req/min
"facebook_graph": (200, 3600),  # 200 req/hour/user
```

---

## 5. Review Aggregation Engine

### 5.1 Sync Strategy

| Platform | Active Frequency | Inactive Frequency | Method |
|----------|-----------------|-------------------|--------|
| Google | 15 min | 2 hours | Celery beat |
| Facebook | Real-time webhook + 30 min fallback | 4 hours | Webhook + Celery beat |
| Yelp | 6 hours | 24 hours | Celery beat |
| TripAdvisor | 2 hours | 12 hours | Celery beat |

"Active" = received a new review in the past 7 days.

### 5.2 Deduplication

Composite unique key: `(business_profile_id, platform, platform_review_id)`. Supabase `upsert` with `on_conflict` handles dedup. Only update if `review_text` or `rating` changed (reviews can be edited).

### 5.3 Initial Import

On first platform connection, paginate through ALL available reviews (respecting rate limits). For Google, follow `nextPageToken` until exhausted. For Yelp, limited to 3 reviews.

### 5.4 Incremental Sync

After initial import, fetch reviews newer than `platform_connections.last_synced_at`. Google API supports ordering by `updateTime` DESC - stop when encountering an already-stored review.

---

## 6. AI-Powered Features

### 6.1 Sentiment Analysis

**Fast path** (all tiers): Keyword-based analysis reusing existing `analyze_review_sentiment` from `backend/app/tools/review_responder/agent_tools.py`.

**LLM path** (Pro tier): Use existing `LLMService` with a sentiment-specific system prompt:

```
Analyze this review and return JSON:
- sentiment: positive/negative/mixed/neutral
- sentiment_score: -1.0 to 1.0
- emotional_tone: angry/disappointed/frustrated/neutral/satisfied/enthusiastic
- key_issues: list of issue categories
- positive_themes / negative_themes: lists
- urgency_level: low/normal/high/critical
```

### 6.2 AI Response Drafting

Extend the existing `review_responder` tool with:
- Business context injection (name, type from `business_profiles`)
- Response history awareness (avoid repeating same phrasing)
- Platform-specific length limits (Google allows longer than Facebook)
- Multiple tone options: professional, friendly, apologetic, empathetic, casual, formal

### 6.3 Trend Detection

Daily Celery task:
- Aggregate reviews by week/month
- Detect: rating drops > 0.3, sentiment shifts > 20%, sudden theme frequency changes
- Generate alerts for significant trends

### 6.4 Alert Triggers

| Trigger | Severity | Example |
|---------|----------|---------|
| New review | Info | "New 4-star review on Google from Jane D." |
| Negative review (rating <= 2) | Warning | "New 1-star review on Google" |
| Critical review (1-star + angry tone) | Critical | Immediate notification |
| Rating drop (weekly avg drops > 0.3) | Warning | "Google rating dropped from 4.5 to 4.2" |
| Unanswered reviews (> 48 hours) | Info | "3 reviews older than 48 hours without response" |
| Connection error | Critical | "Your Google connection needs re-authorization" |

---

## 7. Response Management

### 7.1 Workflow

1. **Generate**: User clicks "Generate Response" -> AI creates draft -> saved as `review_responses` with `status='draft'`
2. **Edit**: User modifies text -> `PATCH /api/reviews/responses/{id}`
3. **Approve**: Status -> `'approved'`
4. **Publish**: Backend decrypts token -> calls platform API -> status -> `'published'` or `'failed'`

### 7.2 Platform-Specific Publishing

- **Google**: `PUT .../reviews/{id}/reply` with `{"comment": "..."}`
- **Facebook**: `POST /{rating_id}/comments` with `{"message": "..."}`
- **Yelp**: Not supported. Show "Reply on Yelp" link.
- **TripAdvisor**: Not supported via API.

### 7.3 Templates

Store as JSONB in `business_profiles.metadata` or a dedicated `response_templates` table. Include placeholders: `{business_name}`, `{reviewer_name}`, `{specific_issue}`.

### 7.4 Bulk Response (Pro tier)

Select multiple reviews -> apply template or AI-generate -> review each before publishing.

---

## 8. Frontend Components

### 8.1 New Pages & Components

```
frontend/src/
├── app/reviews/page.tsx                         # Review dashboard page
├── components/reviews/
│   ├── ReviewDashboard.tsx                      # Main dashboard: stats + list + alerts
│   ├── ReviewList.tsx                           # Filterable, paginated review list
│   ├── ReviewCard.tsx                           # Individual review display
│   ├── ReviewDetail.tsx                         # Full review with response editor
│   ├── ResponseEditor.tsx                       # AI response editing + tone selector
│   ├── PlatformConnector.tsx                    # OAuth connection UI
│   ├── SentimentChart.tsx                       # Sentiment trend chart
│   ├── RatingDistribution.tsx                   # Star rating bar chart
│   ├── PlatformBadge.tsx                        # Google/FB/Yelp badge
│   ├── AlertCenter.tsx                          # Notification center
│   └── ReviewMetrics.tsx                        # Stats cards
├── components/tools/ReviewManagerWidget.tsx      # Chat integration widget
├── lib/api.ts                                   # EXTEND with review functions
└── types/index.ts                               # EXTEND with review types
```

### 8.2 Styling

Follow existing dark theme patterns from `frontend/src/app/dashboard/page.tsx`:
- `widget-card` for containers
- Gradient headers: `bg-gradient-to-r from-emerald-500 to-teal-500` (emerald/teal for reviews)
- Stats bars: `bg-slate-800/50 border-b border-slate-800`
- Scrollable content: `max-h-96 overflow-y-auto custom-scrollbar`
- Icons: Lucide React (`Star`, `MessageCircle`, `ThumbsUp`, `AlertCircle`)
- Reuse: `RatingDisplay`, `MetricCard`, `ScoreCard`, `Button`, `Card`

### 8.3 TypeScript Types

```typescript
interface PlatformConnection {
  id: string;
  platform: 'google' | 'facebook' | 'yelp' | 'tripadvisor';
  platform_business_name: string | null;
  status: 'active' | 'disconnected' | 'expired' | 'error';
  last_synced_at: string | null;
}

interface Review {
  id: string;
  platform: string;
  reviewer_name: string | null;
  rating: number | null;
  is_recommended: boolean | null;
  review_text: string | null;
  published_at: string;
  sentiment: string | null;
  sentiment_score: number | null;
  key_themes: string[] | null;
  is_responded: boolean;
}

interface ReviewResponse {
  id: string;
  draft_text: string;
  published_text: string | null;
  tone: string | null;
  status: 'draft' | 'approved' | 'published' | 'failed';
  ai_generated: boolean;
}

interface ReviewDashboardData {
  connections: PlatformConnection[];
  stats: {
    total_reviews: number;
    average_rating: number;
    response_rate: number;
    avg_response_time_hours: number;
    sentiment_breakdown: Record<string, number>;
  };
  recent_reviews: Review[];
  unread_alerts: ReviewAlert[];
}
```

### 8.4 API Client Functions

Add to `frontend/src/lib/api.ts`:
- `getReviewDashboard()`, `getReviews()`, `generateReviewResponse()`, `updateReviewResponse()`, `publishReviewResponse()`
- `connectPlatform()`, `disconnectPlatform()`, `getConnections()`
- `getReviewAlerts()`, `dismissAlert()`, `triggerReviewSync()`

### 8.5 Chat Integration

Register `ReviewManagerTool` in `ToolRegistry` for conversational queries:
- "Show me my worst reviews this month"
- "Help me respond to John's review about slow service"
- "What are the top complaints from Google reviews?"

Widget data via `<!--REVIEW_DATA:{...}-->` HTML comments, parsed in `ChatMessage.tsx`.

---

## 9. Background Jobs

### 9.1 Celery Tasks

Add to `backend/app/workers/tasks.py`:

| Task | Frequency | Purpose |
|------|-----------|---------|
| `sync_all_reviews` | Every 15 min | Fetch new reviews from all active connections |
| `sync_platform_reviews` | On-demand | Sync single connection (manual trigger) |
| `analyze_review_sentiment_batch` | On new review | Run sentiment analysis on new reviews |
| `generate_review_alerts` | Every 15 min | Check alert conditions, create alerts |
| `aggregate_review_metrics` | Daily | Compute daily/weekly/monthly metrics |
| `refresh_expiring_tokens` | Every 30 min | Preemptively refresh tokens expiring within 1 hour |
| `send_review_digest` | Weekly (Mon 9am) | Email digest summary |

### 9.2 Celery Beat Schedule

Add to existing beat schedule in `backend/app/workers/tasks.py`:

```python
"sync-reviews-frequent": {
    "task": "app.workers.tasks.sync_all_reviews",
    "schedule": 900,  # Every 15 minutes
},
"generate-review-alerts": {
    "task": "app.workers.tasks.generate_review_alerts",
    "schedule": 900,
},
"aggregate-review-metrics": {
    "task": "app.workers.tasks.aggregate_review_metrics",
    "schedule": 86400,  # Daily
},
"refresh-oauth-tokens": {
    "task": "app.workers.tasks.refresh_expiring_tokens",
    "schedule": 1800,  # Every 30 minutes
},
"send-review-digest": {
    "task": "app.workers.tasks.send_review_digest",
    "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Mondays 9am
},
```

---

## 10. Notification System

### 10.1 In-App

Stored in `review_alerts` table. Frontend polls `GET /api/reviews/alerts?is_read=false` every 60 seconds.

### 10.2 Email (Phase 2+)

Using SendGrid/Resend/Postmark:
- **Immediate**: Critical negative reviews (Pro tier)
- **Daily digest**: Summary of new reviews (Basic tier)
- **Weekly digest**: Comprehensive analytics (Basic + Pro)

---

## 11. Subscription & Billing

### 11.1 Tier Structure

| Feature | Free | Basic ($29/mo) | Pro ($44/mo) |
|---------|------|----------------|--------------|
| Connected platforms | 1 (Google) | 2 | Unlimited |
| Sync frequency | 4 hours | 30 min | 15 min |
| AI response drafts/month | 5 | 50 | Unlimited |
| Sentiment analysis | Keyword | AI-powered | AI-powered |
| Custom templates | 3 built-in | Unlimited | Unlimited |
| Bulk response | No | No | Yes |
| Email alerts | No | Daily digest | Real-time + digest |
| Data retention | 30 days | 1 year | Unlimited |
| Trend reports | No | Weekly | Daily + weekly |

### 11.2 Stripe Integration

Add to `backend/app/core/config.py`: `stripe_secret_key`, `stripe_publishable_key`, `stripe_webhook_secret`, `stripe_price_basic`, `stripe_price_pro`

Routes: `POST /api/billing/checkout`, `POST /api/billing/portal`, `POST /api/webhooks/stripe`

Feature gating via FastAPI dependency that checks `subscriptions` table.

---

## 12. Security

- **Token encryption**: Fernet at rest (`backend/app/core/encryption.py`), `OAUTH_ENCRYPTION_KEY` env var
- **Scope minimization**: Request only minimum OAuth scopes
- **GDPR**: `CASCADE` deletes on account removal, data export function, tier-based retention periods
- **TOS compliance**: Only use official APIs, never scrape, show proper attribution
- **Token rotation**: Short-lived access tokens auto-refreshed; disconnect + reconnect for compromised refresh tokens

---

## 13. New Dependencies

**Backend** (`requirements.txt`):
```
cryptography>=42.0.0    # Fernet encryption
stripe>=8.0.0           # Payments
```

**Frontend** (`package.json`):
```
@stripe/stripe-js       # Stripe checkout
```

---

## 14. Environment Variables

**Backend `.env`:**
```
GOOGLE_BUSINESS_CLIENT_ID=
GOOGLE_BUSINESS_CLIENT_SECRET=
GOOGLE_BUSINESS_REDIRECT_URI=http://localhost:8000/api/auth/callback/google
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/auth/callback/facebook
OAUTH_ENCRYPTION_KEY=   # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_BASIC=
STRIPE_PRICE_PRO=
```

**Frontend `.env.local`:**
```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

---

## 15. Docker Compose Updates

Add Celery Beat service to `docker-compose.yml`:

```yaml
celery_beat:
  build: { context: ./backend, dockerfile: Dockerfile }
  env_file: ./backend/.env
  volumes: [./backend:/app]
  command: celery -A app.workers.celery_app beat --loglevel=info
  depends_on: [redis, db]
  restart: unless-stopped
```

---

## 16. Rollout Phases

### Phase 1: Google Reviews (Weeks 1-4)
- DB migration, encryption module
- `GoogleBusinessClient`, OAuth flow
- Repositories + `ReviewService` + `ReviewSyncService`
- API routes for dashboard, reviews, auth
- Celery sync tasks
- Frontend: `ReviewDashboard`, `ReviewList`, `ReviewCard`, `PlatformConnector`
- AI response generation + publish flow
- Basic alerts (new review, negative review)

### Phase 2: Facebook Reviews (Weeks 5-6)
- `FacebookClient`, Facebook OAuth (Page token chain)
- Facebook webhook integration
- Multi-platform dashboard view, platform filters
- Facebook App Review submission

### Phase 3: Yelp Read-Only (Week 7)
- Extend existing `YelpClient` with business match
- Store 3 reviews + aggregate data
- Read-only display with deep links

### Phase 4: Billing & Advanced (Weeks 8-10)
- Stripe integration, subscription management, feature gating
- LLM sentiment analysis (Pro tier)
- Trend detection, email digests, bulk response
- Manual review import, response templates UI
- Data export, performance optimization

---

## 17. Verification

- **Unit tests**: Mock platform APIs with `respx`, test each client, repository, service
- **Integration tests**: Full sync pipeline (mock API -> sync -> DB -> sentiment -> alert)
- **E2E tests**: Connect platform (mock OAuth), view dashboard, generate/publish response
- **Manual testing**: `docker-compose up`, connect real Google Business account, verify sync and response flow

---

## Critical Files Reference

| File | Role |
|------|------|
| `backend/app/tools/review_responder/agent_tools.py` | Existing sentiment analysis + response generation to reuse |
| `backend/app/tools/competitor_analyzer/yelp_client.py` | API client pattern (httpx + @cached + graceful degradation) |
| `backend/app/repositories/business_profile_repository.py` | Repository pattern to follow |
| `backend/app/workers/tasks.py` | Celery task patterns + beat schedule to extend |
| `backend/app/core/cache.py` | @cached decorator for API caching |
| `backend/app/core/rate_limiter.py` | Rate limiter to add new API limits |
| `backend/app/core/config.py` | Settings class to add new env vars |
| `backend/app/api/deps.py` | Dependency injection to add new services |
| `backend/app/main.py` | Tool registration in lifespan |
| `frontend/src/app/dashboard/page.tsx` | Dashboard layout pattern to follow |
| `frontend/src/components/tools/ReviewResponderWidget.tsx` | Widget pattern for chat integration |
| `frontend/src/lib/api.ts` | API client functions to extend |
