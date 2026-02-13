# PHOW Reputation Hub Requirements

**Date:** February 8, 2026  
**Goal:** Expand PHOW into a single-location "review operations" SaaS where owners can monitor and respond to reviews from one interface, with basic sentiment tracking and affordable SMB pricing.

## 1. Product Definition

### 1.1 Core Problem
Single-location businesses currently check Google, Yelp, Facebook, and niche platforms in separate dashboards. This creates slow responses, missed negative reviews, and inconsistent customer communication.

### 1.2 Product Outcome
Build a centralized **Review Inbox** in PHOW that provides:
- Cross-platform review aggregation
- Draft + publish response workflow
- Sentiment classification and trends
- Lightweight SMB-first pricing

### 1.3 Target User
- Owner-operator or manager of a single location
- Vertical focus for initial launch: restaurants, cafes, salons, clinics, gyms, repair shops

## 2. Market Positioning

### 2.1 Packaging Strategy
- Position as **single-location-first reputation OS**
- Avoid enterprise complexity (multi-brand hierarchy, advanced agency white-label, etc.) in MVP

### 2.2 Pricing Direction
- Launch tiers in target range: **$29-$44/month/location**
- Suggested launch:
  - Starter: `$29`
  - Growth: `$39`
  - Pro: `$44`

### 2.3 Competitive Context (Verified)
As of **February 8, 2026**:
- BrightLocal pricing page shows `Track $39`, `Manage $49`, `Grow $59` monthly.
- EmbedSocial pricing page shows plans from `PRO $29`, then `PRO Plus $49`, `Premium $99`.

Use this to message PHOW as:
- More focused than broad local SEO suites
- Better value than multi-location-first reputation tools
- Purpose-built for one-location owner workflows

## 3. External Platform Capability Matrix (Critical Prerequisite)

| Platform | Read Reviews | Publish Reply | Key Constraint | MVP Decision |
|---|---|---|---|---|
| Google Business Profile | Yes | Yes | API access request required; OAuth + policy compliance required | **Phase 1 full integration** |
| Yelp Fusion (public) | Limited | No (public API) | Public endpoint returns limited excerpts; write flows require partner-level APIs/access | **Phase 1 read-lite + deep-link reply** |
| Yelp Partner APIs | Yes (expanded) | Possible with approved access | Partner onboarding/contract, OAuth with extra scopes, write access disabled by default | **Phase 2 after partner approval** |
| Facebook/Meta Pages | Conditional | Conditional | Requires approved app permissions and app review; capability must be validated before commitment | **Phase 2 validation gate** |
| Trustpilot (example vertical connector) | Yes | Yes | Business account/API credentials required | **Optional Phase 2/3 adapter** |

**Important:** Do not promise universal one-click "publish reply everywhere" in MVP. Promise unified workflow with direct publish where APIs permit.

## 4. MVP Scope (Must Build)

### 4.1 Reviews Aggregation
- Connect accounts per source (OAuth/token-based where available)
- Pull latest reviews on schedule + webhook where supported
- Normalize into shared schema (source, author, rating, text, created_at, permalink, response_state)
- Deduplicate and preserve source attribution

### 4.2 Unified Inbox
- Combined stream across sources with filters:
  - Unreplied
  - Negative only (<=3 stars or negative sentiment)
  - Source filter
  - Date range
- Search by keyword/customer text
- SLA tag (`new`, `needs_response`, `responded`, `closed`)

### 4.3 Response Management
- Generate 3 draft tones: `professional`, `friendly`, `apologetic`
- Owner edits before publish
- Publish directly if API allows; otherwise open source deep link
- Store final response body, actor, publish status, error codes, and timestamps

### 4.4 Sentiment Tracking
- Per-review sentiment: `positive`, `neutral`, `negative`, confidence score
- Theme extraction tags (service speed, quality, staff, cleanliness, pricing)
- Trend widgets:
  - 7/30-day sentiment distribution
  - Average rating trend
  - Top recurring complaint themes

### 4.5 Notifications
- Daily digest email
- Real-time alert for new low-rating review (configurable threshold)

## 5. Non-MVP (Explicitly Defer)

- Multi-location hierarchy
- Agency white-label and client workspaces
- Full BI/report builder
- Auto-posting fully autonomous responses without human review
- Predictive churn/LTV modeling

## 6. Repo-Level Implementation Plan (PHOW-Specific)

### 6.1 Backend Additions

Create:
- `backend/app/tools/reputation_hub/tool.py`
- `backend/app/tools/reputation_hub/agent.py`
- `backend/app/tools/reputation_hub/agent_tools.py`
- `backend/app/tools/reputation_hub/prompts.py`
- `backend/app/clients/reviews/google_business_profile_client.py`
- `backend/app/clients/reviews/yelp_client.py`
- `backend/app/clients/reviews/meta_client.py`
- `backend/app/services/reviews/review_aggregation_service.py`
- `backend/app/services/reviews/review_response_service.py`
- `backend/app/services/reviews/sentiment_service.py`
- `backend/app/services/reviews/sync_scheduler_service.py`

Update:
- `backend/app/core/config.py` with new env vars
- `backend/app/main.py` to register `ReputationHubTool`
- `backend/app/api/routes/` with a new `reviews.py` REST router for inbox/reply/sync endpoints

### 6.2 Frontend Additions

Create:
- `frontend/src/app/reviews/page.tsx`
- `frontend/src/components/reviews/ReviewsInbox.tsx`
- `frontend/src/components/reviews/ReviewThreadCard.tsx`
- `frontend/src/components/reviews/ReplyComposer.tsx`
- `frontend/src/components/reviews/SentimentOverview.tsx`
- `frontend/src/components/reviews/SourceConnectionPanel.tsx`

Update:
- Tool selector/dashboard navigation for `reputation_hub`
- Existing chat widget parser to handle review-specific widget payloads

### 6.3 Database Migrations

Add migration `supabase/migrations/006_reputation_hub.sql` with tables:

1. `review_sources`
- `id`, `business_profile_id`, `source` (`google`,`yelp`,`facebook`,`trustpilot`), `external_account_id`, `status`, `connected_at`, `last_sync_at`

2. `reviews`
- `id`, `business_profile_id`, `source`, `external_review_id`, `rating`, `review_text`, `author_name`, `review_created_at`, `review_url`, `raw_payload`, `response_status`, `synced_at`
- Unique: `(source, external_review_id)`

3. `review_responses`
- `id`, `review_id`, `source`, `draft_text`, `final_text`, `publish_mode` (`api`,`deeplink`), `publish_status`, `published_at`, `published_by`, `error_message`

4. `review_sentiment`
- `id`, `review_id`, `sentiment_label`, `confidence`, `themes` (text[]), `model_version`, `created_at`

5. `review_sync_jobs`
- `id`, `source`, `job_type` (`pull`,`push`), `status`, `started_at`, `completed_at`, `error_message`, `metrics` (jsonb)

6. `review_activity_log`
- audit trail for compliance and support debugging

Indexes:
- `reviews(business_profile_id, review_created_at desc)`
- `reviews(business_profile_id, response_status)`
- `review_sentiment(review_id)`

## 7. API Contract Requirements

Add endpoints under `/api/reviews`:
- `POST /connections/{source}/start`
- `POST /connections/{source}/callback`
- `GET /connections`
- `POST /sync`
- `GET /inbox`
- `GET /{review_id}`
- `POST /{review_id}/draft`
- `POST /{review_id}/publish`
- `GET /analytics/summary`
- `GET /analytics/trends`

Common requirements:
- Session + business profile ownership checks
- Idempotency key on publish endpoint
- Consistent error taxonomy (`auth_expired`, `rate_limited`, `policy_blocked`, `validation_failed`)

## 8. AI + Sentiment Requirements

### 8.1 Model Behavior
- Deterministic sentiment classification where possible (temperature near 0)
- Draft generation includes source-aware tone and length constraints
- No fabricated facts or promises (refunds/discounts/actions) unless user explicitly adds them

### 8.2 Guardrails
- Block unsafe phrasing (threatening, discriminatory, medical/legal claims)
- Enforce response length per platform limits
- Require human confirmation before publish

### 8.3 Evaluation
- Create a small labeled review dataset (>=300 reviews across target verticals)
- Track:
  - Sentiment F1
  - Theme extraction precision@k
  - Draft acceptance rate by users

## 9. Security, Privacy, and Compliance Prerequisites

### 9.1 Security
- Encrypt provider access tokens at rest
- Rotate encryption keys
- Apply row-level security strategy for business isolation
- Audit log for all publish actions

### 9.2 Privacy
- Publish Privacy Policy and Terms before external launch
- Data retention controls (soft-delete and purge path)
- DSAR handling process for customer data requests

### 9.3 Platform Policy Compliance
- Preserve source attribution requirements
- Respect storage and display restrictions by platform
- Implement consent flow for any user data access

## 10. Operations Requirements

### 10.1 Background Jobs
- Scheduled sync every 15 minutes (configurable per source)
- Retry with exponential backoff
- Dead-letter queue for failed sync/publish jobs

### 10.2 Observability
- Metrics:
  - `sync_success_rate`
  - `avg_sync_latency`
  - `publish_success_rate`
  - `time_to_first_response`
- Tracing per connector call
- Alerting on auth expiration spikes and repeated publish failures

### 10.3 Reliability Targets
- API uptime target: `99.9%`
- P95 inbox load: `< 1.5s`
- P95 draft generation: `< 4s`

## 11. Business and Go-To-Market Prerequisites

### 11.1 Initial Pricing and Limits
- Starter `$29`: 1 location, 2 sources, 300 AI drafts/month
- Growth `$39`: 1 location, 3 sources, 800 AI drafts/month
- Pro `$44`: 1 location, all supported sources, 1500 AI drafts/month + weekly insights PDF

### 11.2 Launch Motion
- Self-serve signup + 14-day trial
- Vertical landing pages (restaurant/salon/clinic)
- Onboarding checklist to first value in < 15 minutes

### 11.3 Core Success Metrics
- Activation: connect at least 1 source + send first response within 24h
- Week-4 retention
- Median response time improvement
- Net revenue retention for single-location segment

## 12. Delivery Plan (Execution Workstreams)

### 12.1 Workstream A: Integrations
- Google full connector and reply publishing
- Yelp read-lite connector + reply deep links
- Connector abstraction and token lifecycle handling

### 12.2 Workstream B: Product + UX
- Inbox, filters, thread detail, reply composer, connection flows
- Error and fallback UX for non-write-capable platforms

### 12.3 Workstream C: Data + AI
- Canonical review schema + migrations
- Sentiment/theme pipeline + analytics aggregates

### 12.4 Workstream D: Platform + Ops
- Job scheduler, retries, observability, alerting
- Billing/entitlements and usage metering

### 12.5 Suggested Timeline
- Week 1-2: Schema + Google connector + basic inbox
- Week 3-4: Draft/publish workflow + sentiment + analytics v1
- Week 5: Billing gates + alerting + hardening
- Week 6: Beta cohort (10-20 businesses), feedback loop, launch fixes

## 13. Definition of Done (MVP)

- User can connect Google and at least one additional source
- New reviews sync automatically and appear in unified inbox
- User can generate/edit/publish response from PHOW for Google reviews
- User can manage Yelp via unified workflow with deep-link fallback
- Sentiment and theme trends visible for 7 and 30 days
- Billing and monthly usage limits enforced
- Audit logs, retries, and failure notifications operational

## 14. Source Notes (Verified on February 8, 2026)

- BrightLocal pricing: https://www.brightlocal.com/pricing/  
- EmbedSocial pricing: https://embedsocial.com/pricing/  
- Google Business Profile API overview and access/setup/policies:  
  - https://developers.google.com/my-business/content/overview  
  - https://developers.google.com/my-business/content/basic-setup  
  - https://developers.google.com/my-business/content/policies  
  - https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/list  
  - https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/updateReply  
  - https://developers.google.com/my-business/content/notifications  
- Yelp API docs and partner constraints:
  - https://docs.developer.yelp.com/docs/fusion-intro  
  - https://docs.developer.yelp.com/reference/v3_business_reviews  
  - https://docs.developer.yelp.com/docs/v3-rate-limiting  
  - https://docs.developer.yelp.com/docs/v3-oauth2  
  - https://docs.developer.yelp.com/reference/v3_business_review_responses_upsert  
  - https://docs.developer.yelp.com/docs/reporting-api-terms-and-conditions  
- Trustpilot service review reply endpoint:
  - https://documentation-apidocumentation.trustpilot.com/service-reviews-api

## 15. Open Risks Requiring Explicit Decision

1. Facebook/Meta review reply capability can vary by permission/app review status; validate before public commitment.
2. Yelp full reply automation depends on partner-level access and contractual approval.
3. Platform terms can change; assign owner for quarterly policy review.

