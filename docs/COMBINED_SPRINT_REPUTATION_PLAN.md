# COMBINED_SPRINT_REPUTATION Plan (Lean, Decision-Complete)

## Summary
Create a single merged implementation doc at:

- `docs/COMBINED_SPRINT_REPUTATION_PLAN.md`

This merged plan will:
- Use `docs/PHOW_REPUTATION_HUB_REQUIREMENTS.md` as the source of truth for scope/DoD.
- Use `docs/CLAUDE_REPUTATION_DOC.md` as the source of truth for architecture/file patterns.
- Keep Claude's useful feature decomposition.
- Import Codex backlog strengths: early authz + OpenAPI contracts, feature flags, reliability layer, conformance tests, and continuous quality gates.
- Stay lean by removing redundancy and duplicate implementation tracks.

User-selected defaults applied:
- Scope includes competitors now.
- Delivery shape is 6 sprints with hardening gates each sprint.

## What to Keep vs Drop (Merge Rules)
- Keep:
  - Review domain tables/services/routes/types from Claude plan.
  - Repo/service/DI/router/frontend API patterns from architecture doc.
  - Program-level quality gates from Codex backlog.
  - Early OAuth risk handling behind flags.
- Drop:
  - Any `/ops/*` feature scope unrelated to reputation hub.
  - Placeholder-only tasks that do not move MVP behavior.
  - Duplicate services that overlap responsibilities.
- Consolidate:
  - One ingestion pipeline, one query path, one response workflow, one sentiment/analytics pipeline.
  - One set of endpoint contracts and one type system for FE/BE.

## Public Interfaces (Final Contract)

### Backend routes (`/api/reviews`)
- `GET /health`
- `GET /connections`
- `POST /connections/{source}/start`
- `POST /connections/{source}/callback`
- `DELETE /connections/{source}`
- `POST /sync`
- `GET /inbox`
- `GET /{review_id}`
- `POST /{review_id}/draft`
- `POST /{review_id}/publish`
- `GET /analytics/summary`
- `GET /analytics/trends`
- `GET /analytics/themes`
- `GET /analytics/platforms`
- `GET /competitors`
- `GET /notifications`
- `POST /notifications/{notification_id}/read`
- `POST /notifications/read-all`
- `GET /alerts/settings`
- `PUT /alerts/settings`
- `GET /usage` (plan + draft usage + limit status)

### Error taxonomy (uniform)
- `auth_expired`
- `rate_limited`
- `policy_blocked`
- `validation_failed`
- `ownership_forbidden`
- `idempotency_conflict`
- `provider_unavailable`

### Frontend types (`frontend/src/types/index.ts`)
- `ReviewSource`, `Review`, `ReviewResponseDraft`, `ReviewSentiment`
- `ReviewNotification`, `AlertSettings`
- `ReviewAnalyticsSummary`, `ReviewTrendPoint`, `ThemeMetric`, `PlatformMetric`
- `CompetitorComparison`
- `UsageSummary`

## Data/Schema (Single Migration Set)
Implement `supabase/migrations/006_reputation_hub.sql` with:
- `review_sources`
- `reviews`
- `review_responses`
- `review_sentiment`
- `review_sync_jobs`
- `review_activity_log`
- `review_alert_settings`
- `review_notifications`

Required constraints/indexes:
- Uniques on `(business_profile_id, source)` and `(source, external_review_id)`
- Inbox/query indexes from requirements
- Publish/idempotency support index on `review_responses.idempotency_key`

## 6-Sprint Execution Plan

## Sprint 1: Foundation + Contracts + Secure Baseline
- Migration + models + router skeleton.
- Config + encryption module + feature flags:
  - `REPUTATION_HUB_ENABLED`, `REPUTATION_LIVE_CONNECTORS_ENABLED`, `REPUTATION_OAUTH_ENABLED`
- Ownership/authz helper wired into first endpoints.
- OpenAPI snapshot/contract tests for `/api/reviews/*`.
- Frontend route shell:
  - `/reputation`, `/reputation/analytics`, `/reputation/competitors`, `/reputation/connections`, `/reputation/settings`
- Dashboard nav adds "Reputation".

Exit criteria:
- `/api/reviews/health` live.
- Contract + authz tests passing.
- Routes render and navigate.

## Sprint 2: Connections + Source Lifecycle
- Repositories for sources/reviews/sentiment/notifications.
- `ConnectionService` with OAuth start/callback/disconnect/token encryption.
- Google OAuth path (flagged), Yelp key/deeplink flow, Meta stub.
- Connections UI with status/reconnect/disconnect and ownership-safe calls.
- Token expiry handling baseline.

Exit criteria:
- Connect/disconnect flow works for mocked Google + Yelp mode.
- Tokens encrypted at rest.
- Wrong-owner requests return 403.

## Sprint 3: Sync Pipeline + Unified Inbox
- Clients:
  - Google list reviews (+ mock fallback)
  - Yelp read-lite (3-review limitation handled)
  - Meta phase-2 stub
- `ReviewAggregationService`:
  - normalize + upsert + dedupe
  - create sync job records
- Celery tasks + beat schedule (15-min sync, token-refresh worker).
- Inbox endpoints with filters/search/cursor pagination.
- Inbox UI with filter bar, cards, empty/loading/error states, sync-now.

Exit criteria:
- Scheduled + manual sync populates inbox.
- Pagination/filters/search deterministic.
- Duplicate sync does not duplicate rows.

## Sprint 4: Response Workflow + Guardrails + Idempotent Publish
- `ReviewResponseService`:
  - generate 3 tones (`professional`, `friendly`, `apologetic`)
  - platform-aware constraints
  - publish path: Google API / Yelp deeplink fallback
- Idempotency key enforcement on publish.
- Review detail slide-over with draft generation/edit/publish.
- Activity logging for connect/sync/draft/publish actions.
- Policy-safe response guardrails.

Exit criteria:
- End-to-end: inbox review -> generate -> edit -> publish/deeplink.
- Double-submit publish prevented.
- Response state and audit log updated correctly.

## Sprint 5: Sentiment + Analytics + Competitors + Notifications + Usage Limits
- `SentimentService` (deterministic prompting, theme extraction).
- Pipeline hook: classify new reviews post-sync.
- Analytics service + endpoints:
  - summary/trends/themes/platforms
- Competitor comparison endpoint/page using existing `tracked_competitors` data only (no new connector scope).
- Notification generation for low-rating and batch events.
- Alert settings + bell/dropdown UX.
- Usage metering + plan limit enforcement for AI drafts (`$29/$39/$44` tiers).

Exit criteria:
- 7/30-day sentiment + rating trends visible.
- Low-rating alerts and read/read-all flows work.
- Competitor page operational from existing data.
- Draft usage limits enforced by plan.

## Sprint 6: Hardening, Reliability, Release Readiness
- Retry/backoff/circuit-breaker across connectors.
- DLQ + replay for failed sync/publish jobs.
- Cross-tenant security tests and policy checks.
- Performance targets:
  - inbox p95 < 1.5s
  - draft generation p95 < 4s
- Accessibility checks for all reputation pages.
- Full e2e regression + canary/rollback runbook + release checklist artifacts.

Exit criteria:
- Reliability/observability gates green.
- Canary + rollback validated.
- MVP DoD from requirements fully satisfied.

## Program-Level Quality Gates (Every Sprint)
- Backend tests: success + failure for each new service/route.
- Frontend tests: logic-bearing components covered.
- At least one deterministic e2e path per sprint.
- OpenAPI snapshot updated and passing.
- Ownership/RBAC tests for new endpoints.
- Accessibility checks on new pages.
- Performance smoke for heavy surfaces.

## Test Cases and Scenarios

### Core functional
- Connect Google and Yelp-lite; disconnect/reconnect.
- Manual + scheduled sync; dedupe correctness.
- Inbox filters (`unreplied`, negative, source, date range, search).
- Draft generation in 3 tones; edit and publish/deeplink.
- Idempotent publish behavior.
- Sentiment labels + themes persisted.
- Analytics summary/trends/themes/platforms.
- Competitor comparison rendering with/without tracked competitors.
- Notification threshold behavior and digest scheduling.
- Usage limit enforcement and over-limit errors.

### Failure/security
- Expired auth -> `auth_expired` + reconnect path.
- Provider 429/5xx -> retry/backoff and terminal classification.
- Cross-tenant access attempts blocked.
- Invalid payloads -> `validation_failed`.
- Provider blocked/policy issues -> `policy_blocked`.

## Assumptions and Defaults
- Final merged file path: `docs/COMBINED_SPRINT_REPUTATION_PLAN.md`.
- Competitor module is included, but lean (read from existing competitor data only).
- Meta full write capability remains post-MVP gate.
- Yelp publish stays deeplink unless partner access is approved later.
- Human confirmation is always required before publish.
- No multi-location hierarchy in MVP.
