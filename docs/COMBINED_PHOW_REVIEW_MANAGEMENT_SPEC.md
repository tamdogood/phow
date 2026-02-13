# COMBINED PHOW Review Management Specification

**Date:** February 8, 2026  
**Scope:** Combined "best version" of:
- `docs/CLAUDE_SAAS_REVIEW_MANAGEMENT_SPEC.md`
- `docs/PHOW_REPUTATION_HUB_REQUIREMENTS.md`

This combined spec keeps the technical depth of the CLAUDE draft and applies the investigation constraints so the MVP is realistic, buildable, and policy-safe.

## 1. Product Definition

### 1.1 Problem
Single-location businesses monitor reviews across multiple dashboards (Google, Yelp, Facebook, vertical sites). This causes slow responses, missed negative reviews, and fragmented reputation operations.

### 1.2 Product Outcome
Build a centralized PHOW "Review Operations Hub" with:
- Aggregation of reviews across major sources
- Unified response workflow from one interface
- Basic sentiment/theme tracking and trend alerts
- SMB-first pricing in the `$29-$44/month` range

### 1.3 Target User
- Owner-operator or manager of a single location
- Early verticals: restaurants, cafes, salons, clinics, gyms, repair services

## 2. Market Positioning and Packaging

### 2.1 Positioning
- Single-location-first product, not agency/enterprise-first
- Faster workflow than source-by-source logins
- Priced below enterprise-heavy reputation suites

### 2.2 Competitive Context (Verified February 8, 2026)
- BrightLocal pricing page shows `Track $39`, `Manage $49`, `Grow $59` monthly.
- EmbedSocial pricing page shows plans from `PRO $29`, then `PRO Plus $49`, `Premium $99`.

### 2.3 Packaging Recommendation
- Starter: `$29` (1 location, limited source count and AI drafts)
- Growth: `$39` (1 location, broader source support)
- Pro: `$44` (1 location, full source support, advanced alerts/analytics)

## 3. Platform Capability Matrix (Source of Truth)

| Platform | Read Reviews | Reply via API | Key Constraints | MVP Decision |
|---|---|---|---|---|
| Google Business Profile | Yes | Yes | Access request + OAuth + policy compliance required | **Phase 1 full integration** |
| Yelp Fusion (public) | Limited | No | Public endpoint is limited; reply automation requires partner-level programs | **Phase 1 read-lite + deep link for replies** |
| Yelp partner APIs | Yes (expanded) | Possible (approval dependent) | Partner onboarding and contractual approval required | **Phase 2 gate** |
| Facebook/Meta Pages | Conditional | Conditional | Requires app review and permission approval; capability must be validated before commitment | **Phase 2 validation gate** |
| Trustpilot (optional) | Yes | Yes | Requires business API credentials and connector work | **Phase 2/3 optional connector** |

**MVP policy:** Do not promise "reply everywhere from one click." Promise unified workflow, with direct publish where APIs allow and deep-link fallback otherwise.

## 4. Prerequisites Checklist

### 4.1 Business and Compliance Prerequisites
- Privacy Policy and Terms of Service published before beta onboarding.
- Data retention policy documented (default retention + purge flow).
- DSAR process defined (export/delete on request).
- Platform attribution and display restrictions documented by source.

### 4.2 Platform Access Prerequisites
- Google Cloud project configured for Business Profile APIs.
- Google OAuth consent configured and verified for production access.
- Google scope approved: `https://www.googleapis.com/auth/business.manage`.
- Yelp API key available for Fusion read-lite.
- Facebook app created with required permissions submitted for app review.
- Optional: Trustpilot credentials and sandbox access.

### 4.3 Infrastructure Prerequisites
- Redis and Celery running (worker + beat).
- Supabase migration path ready for `006_review_management.sql`.
- Encrypted token storage key provisioned (`OAUTH_ENCRYPTION_KEY`).
- Secret management set up for provider credentials and Stripe keys.

### 4.4 Product and Ops Prerequisites
- Alert routing (in-app now, email provider optional in Phase 2).
- Support runbook for auth failures and sync incidents.
- Feature flag support for connector rollout by platform.

## 5. MVP Functional Requirements

### 5.1 Account Connection
- Connect/reconnect/disconnect Google and Yelp per business profile.
- Store connection status (`active`, `disconnected`, `expired`, `error`).
- Expose clear user-facing error messages for auth and policy failures.

### 5.2 Unified Review Inbox
- Aggregated stream across connected sources.
- Filters: unreplied, negative, platform, date range.
- Search by reviewer and review text.
- Review state labels: `new`, `needs_response`, `responded`, `closed`.

### 5.3 Response Management
- Generate AI draft options (`professional`, `friendly`, `apologetic`).
- User edits required before publish.
- Direct publish for supported platforms (Google in MVP).
- Deep-link handoff for unsupported write APIs (Yelp in MVP).
- Persist draft, final response, publish status, error messages, timestamps.

### 5.4 Sentiment and Themes
- Per-review sentiment label and confidence score.
- Theme tags (speed, quality, staff, cleanliness, pricing, accuracy).
- 7-day and 30-day trend views for sentiment distribution, average rating, and top complaint themes.

### 5.5 Alerts
- New negative review alerts (threshold configurable).
- Connection/auth failure alerts.
- Unanswered review aging alerts (for example >48h).

## 6. Non-MVP (Explicit Deferrals)

- Multi-location hierarchy and agency workspaces
- White-label portals
- Fully autonomous auto-publish without human review
- Advanced BI/report builder
- Predictive churn/LTV models

## 7. Data Model and Migration Plan

Create `supabase/migrations/006_review_management.sql`.

### 7.1 `platform_connections`
Purpose: one row per `business_profile_id + platform` with OAuth/API credentials and sync status.

Key fields:
- `business_profile_id`, `platform`, `platform_account_id`, `platform_location_id`
- `access_token_encrypted`, `refresh_token_encrypted`, `token_expires_at`
- `status`, `error_message`, `last_synced_at`

### 7.2 `reviews`
Purpose: canonical normalized review store.

Key fields:
- `business_profile_id`, `platform`, `platform_review_id`
- `reviewer_name`, `rating`, `is_recommended`, `review_text`, `review_url`
- `published_at`, `metadata`, `is_responded`

Constraint:
- Unique composite: `(business_profile_id, platform, platform_review_id)`

### 7.3 `review_responses`
Purpose: response drafting and publishing lifecycle.

Key fields:
- `review_id`, `draft_text`, `published_text`, `tone`
- `status` (`draft`, `approved`, `published`, `failed`)
- `published_at`, `error_message`, `ai_generated`

### 7.4 `review_sentiment_analyses`
Purpose: structured sentiment and issue extraction.

Key fields:
- `review_id`, `sentiment`, `sentiment_score`, `emotional_tone`
- `key_issues`, `positive_themes`, `negative_themes`, `urgency_level`
- `model_version`

### 7.5 `review_alerts`
Purpose: in-app notification feed.

Key fields:
- `business_profile_id`, `review_id`, `alert_type`, `severity`
- `title`, `message`, `metadata`, `is_read`, `is_dismissed`

### 7.6 `review_metrics`
Purpose: pre-aggregated analytics by period.

Key fields:
- `business_profile_id`, `platform`, `period`, `period_start`
- `total_reviews`, `new_reviews`, `average_rating`
- `positive_count`, `negative_count`, `responded_count`, `avg_response_time_hours`

### 7.7 Optional/Phase 2 Tables
- `review_sync_jobs` for detailed job telemetry
- `subscriptions` for billing/entitlements if not already modeled elsewhere

## 8. Backend Implementation (PHOW-Aligned)

### 8.1 New Backend Files
- `backend/app/tools/reputation_hub/tool.py`
- `backend/app/tools/reputation_hub/agent.py`
- `backend/app/tools/reputation_hub/agent_tools.py`
- `backend/app/tools/reputation_hub/prompts.py`
- `backend/app/clients/reviews/google_business_profile_client.py`
- `backend/app/clients/reviews/yelp_client.py`
- `backend/app/clients/reviews/meta_client.py`
- `backend/app/repositories/platform_connection_repository.py`
- `backend/app/repositories/review_repository.py`
- `backend/app/repositories/review_response_repository.py`
- `backend/app/repositories/review_alert_repository.py`
- `backend/app/repositories/review_metrics_repository.py`
- `backend/app/services/reviews/review_service.py`
- `backend/app/services/reviews/review_sync_service.py`
- `backend/app/services/reviews/review_sentiment_service.py`
- `backend/app/services/reviews/oauth_service.py`
- `backend/app/api/routes/reviews.py`
- `backend/app/api/routes/oauth.py`
- `backend/app/core/encryption.py`

### 8.2 Backend Updates
- `backend/app/main.py` register `ReputationHubTool`.
- `backend/app/api/routes/__init__.py` export and include new routers.
- `backend/app/core/config.py` add connector/billing/env settings.
- `backend/app/api/deps.py` add DI constructors for review services.
- `backend/app/workers/tasks.py` add sync/sentiment/metrics/token-refresh tasks.
- `backend/app/core/rate_limiter.py` add source-specific limits.

### 8.3 Implementation Pattern Reuse
- Reuse API client patterns from `backend/app/tools/competitor_analyzer/yelp_client.py`.
- Reuse sentiment bootstrap logic from `backend/app/tools/review_responder/agent_tools.py`.
- Follow repository conventions from `backend/app/repositories/business_profile_repository.py`.

## 9. API Contract

Base path: `/api/reviews` and `/api/auth`.

### 9.1 Reviews API
- `GET /api/reviews/dashboard`
- `GET /api/reviews`
- `GET /api/reviews/{review_id}`
- `POST /api/reviews/{review_id}/respond`
- `PATCH /api/reviews/responses/{response_id}`
- `POST /api/reviews/responses/{response_id}/publish`
- `POST /api/reviews/sync`
- `GET /api/reviews/alerts`
- `PATCH /api/reviews/alerts/{alert_id}/dismiss`
- `GET /api/reviews/metrics`

### 9.2 Auth/Connections API
- `POST /api/auth/connect/{platform}`
- `GET /api/auth/callback/{platform}`
- `DELETE /api/auth/disconnect/{platform}`
- `GET /api/auth/connections`

### 9.3 API Guarantees
- Business profile ownership/session checks on all endpoints.
- Idempotency key required for publish endpoint.
- Error taxonomy: `auth_expired`, `rate_limited`, `policy_blocked`, `validation_failed`, `provider_unavailable`.

## 10. Frontend Requirements

### 10.1 New UI Surfaces
- `frontend/src/app/reviews/page.tsx`
- `frontend/src/components/reviews/ReviewDashboard.tsx`
- `frontend/src/components/reviews/ReviewList.tsx`
- `frontend/src/components/reviews/ReviewCard.tsx`
- `frontend/src/components/reviews/ReviewDetail.tsx`
- `frontend/src/components/reviews/ResponseEditor.tsx`
- `frontend/src/components/reviews/PlatformConnector.tsx`
- `frontend/src/components/reviews/SentimentChart.tsx`
- `frontend/src/components/reviews/AlertCenter.tsx`
- `frontend/src/components/tools/ReviewManagerWidget.tsx`

### 10.2 Frontend Updates
- Extend `frontend/src/lib/api.ts` with review/auth endpoints.
- Extend shared types in `frontend/src/types`.
- Add dashboard/tool navigation for reputation hub.

## 11. Connector and Sync Strategy

### 11.1 Sync Cadence
| Platform | Active Businesses | Inactive Businesses | Mode |
|---|---|---|---|
| Google | 15 min | 2 hours | Polling |
| Yelp | 6 hours | 24 hours | Polling |
| Facebook (if approved) | webhook + 30 min fallback | 4 hours | Webhook + polling |

Definition: "active" means at least one new review in last 7 days.

### 11.2 Deduplication
- Upsert by `(business_profile_id, platform, platform_review_id)`.
- Update existing row only if review body/rating/reply state changed.

### 11.3 Import Strategy
- Initial connect: full backfill where API allows.
- Incremental sync: fetch newest first, stop on previously known review boundary.

## 12. AI and Sentiment Requirements

### 12.1 Sentiment Pipeline
- Fast path: keyword/rating heuristic (existing review responder logic).
- LLM path: structured JSON output for ambiguous/mixed cases.
- Store model version for auditability and regression tracking.

### 12.2 Response Generation Guardrails
- No fabricated operational promises.
- No legal/medical claim language.
- Respect platform-specific text length constraints.
- Human approval required before publish in MVP.

### 12.3 Evaluation Targets
- Labeled dataset: >=300 reviews across target verticals.
- Metrics: sentiment F1, theme precision@k, draft acceptance/edit rate.

## 13. Jobs, Observability, and Reliability

### 13.1 Celery Tasks
- `sync_all_reviews` (15 min)
- `sync_platform_reviews` (on demand)
- `analyze_review_sentiment_batch` (event-driven)
- `generate_review_alerts` (15 min)
- `aggregate_review_metrics` (daily)
- `refresh_expiring_tokens` (30 min)
- `send_review_digest` (weekly, phase 2)

### 13.2 Operational Metrics
- `sync_success_rate`
- `publish_success_rate`
- `avg_sync_latency`
- `time_to_first_response`
- `auth_failure_rate`

### 13.3 SLO Targets
- API uptime target: `99.9%`
- P95 inbox load: `<1.5s`
- P95 draft generation: `<4s`

## 14. Security and Compliance Requirements

- Encrypt access/refresh tokens at rest via `backend/app/core/encryption.py`.
- Keep encryption key outside DB and rotate regularly.
- Scope minimization per provider.
- Full audit trail for response publish actions.
- Strict use of official APIs only; no scraping.
- Quarterly provider policy review ownership assigned.

## 15. Billing and Entitlements

### 15.1 Recommended Plans
| Plan | Price | Included |
|---|---|---|
| Starter | `$29` | 1 location, 2 sources, limited drafts |
| Growth | `$39` | 1 location, 3 sources, expanded drafts |
| Pro | `$44` | 1 location, all supported sources, advanced alerts/analytics |

### 15.2 Stripe (Phase 2+)
Add config keys:
- `stripe_secret_key`
- `stripe_publishable_key`
- `stripe_webhook_secret`
- `stripe_price_starter`
- `stripe_price_growth`
- `stripe_price_pro`

## 16. Required Configuration and Dependencies

### 16.1 Backend Environment Variables
- `GOOGLE_BUSINESS_CLIENT_ID`
- `GOOGLE_BUSINESS_CLIENT_SECRET`
- `GOOGLE_BUSINESS_REDIRECT_URI`
- `FACEBOOK_APP_ID`
- `FACEBOOK_APP_SECRET`
- `FACEBOOK_REDIRECT_URI`
- `YELP_API_KEY`
- `OAUTH_ENCRYPTION_KEY`
- `STRIPE_SECRET_KEY` (phase 2+)
- `STRIPE_PUBLISHABLE_KEY` (phase 2+)
- `STRIPE_WEBHOOK_SECRET` (phase 2+)
- `STRIPE_PRICE_STARTER` (phase 2+)
- `STRIPE_PRICE_GROWTH` (phase 2+)
- `STRIPE_PRICE_PRO` (phase 2+)

### 16.2 Frontend Environment Variables
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` (phase 2+)

### 16.3 Dependency Additions
- Backend: `cryptography` (token encryption), `stripe` (billing).
- Frontend: `@stripe/stripe-js` (phase 2+ checkout).

### 16.4 Runtime Services
- Add Celery beat process to schedule sync, alerts, and metric tasks.
- Ensure Redis is available for broker/cache and background job coordination.

## 17. Delivery Plan (Subagent Workstreams)

### 17.1 Workstream A: Integrations Subagent
- Google connector (read + reply publish)
- Yelp connector (read-lite + deep links)
- OAuth/token lifecycle + reconnect flows

### 17.2 Workstream B: Data/AI Subagent
- Migration `006_review_management.sql`
- Canonical schema + repositories
- Sentiment analysis and trend aggregation

### 17.3 Workstream C: API/Backend Subagent
- Review/OAuth routes
- Service orchestration and error taxonomy
- Task scheduling and retry logic

### 17.4 Workstream D: Frontend Subagent
- Reviews page, inbox, detail, editor, connection panel
- Alerts and analytics UI
- Chat widget integration for review workflows

### 17.5 Workstream E: Ops/GTM Subagent
- Observability, runbooks, support workflows
- Pricing gates and billing integration
- Beta onboarding and activation instrumentation

### 17.6 Suggested Timeline
- Week 1-2: schema + Google connector + basic inbox
- Week 3-4: response publish flow + sentiment + alerts + metrics v1
- Week 5: hardening, feature flags, entitlements
- Week 6: beta cohort (10-20 businesses), instrumentation and launch fixes

## 18. Definition of Done (MVP)

- User connects Google and at least one additional source (Yelp read-lite acceptable).
- Reviews sync automatically into one inbox.
- User can generate, edit, and publish Google replies from PHOW.
- Yelp flow supports unified triage and deep-link response handoff.
- Sentiment and theme trends available for 7-day and 30-day windows.
- Alerting, retries, and audit logs are operational.

## 19. Open Risks and Decision Gates

1. Facebook/Meta reply capabilities require app review approval and should remain behind a gate until verified.
2. Yelp reply automation depends on partner-level access and cannot be promised in MVP.
3. Provider policies and pricing can change; assign an owner for quarterly validation.

## 20. Source Links (Verified February 8, 2026)

- BrightLocal pricing: https://www.brightlocal.com/pricing/
- EmbedSocial pricing: https://embedsocial.com/pricing/
Google Business Profile docs:
- https://developers.google.com/my-business/content/overview
- https://developers.google.com/my-business/content/basic-setup
- https://developers.google.com/my-business/content/policies
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/list
- https://developers.google.com/my-business/reference/rest/v4/accounts.locations.reviews/updateReply
- https://developers.google.com/my-business/content/notifications
Yelp docs:
- https://docs.developer.yelp.com/docs/fusion-intro
- https://docs.developer.yelp.com/reference/v3_business_reviews
- https://docs.developer.yelp.com/docs/v3-rate-limiting
- https://docs.developer.yelp.com/docs/v3-oauth2
- https://docs.developer.yelp.com/reference/v3_business_review_responses_upsert
- https://docs.developer.yelp.com/docs/reporting-api-terms-and-conditions
Trustpilot service reviews API:
- https://documentation-apidocumentation.trustpilot.com/service-reviews-api
