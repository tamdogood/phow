# PHOW Reputation Hub — Sprint Plan

## Overview

7 sprints decomposing the Reputation Hub feature into atomic, committable tasks. Each sprint produces a demoable, runnable increment. Every task has explicit validation criteria.

**Reference docs:**
- Feature spec: `docs/CLAUDE_REPUTATION_DOC.md`
- Full plan: `.claude/plans/jolly-dreaming-dragon.md`
- Existing specs: `docs/PHOW_REPUTATION_HUB_REQUIREMENTS.md`, `docs/COMBINED_PHOW_REVIEW_MANAGEMENT_SPEC.md`

**Pre-Sprint Prerequisite:** Verify Google Business Profile API access is approved (application review can take weeks). If not, all Google client tasks use mock responses behind a feature flag.

---

## Sprint 1: Foundation — Database + Backend Skeleton + Frontend Shell

**Goal:** Migration applied with all tables. Backend has `/api/reviews/health` returning 200. Frontend has navigable `/reputation` route with 5 tabbed placeholder pages. Dashboard has "Reputation" nav link.

**Demo:** Navigate to `http://localhost:3000/reputation`, see tabbed layout. `curl http://localhost:8000/api/reviews/health` returns `{"status":"ok"}`.

---

### Task 1.1 — Create database migration `006_reputation_hub.sql`

**What:** Create migration with 8 tables, all indexes, unique constraints, and `updated_at` triggers.

**Files:** `supabase/migrations/006_reputation_hub.sql` (new)

**Tables:**
| Table | Key Columns | Constraints |
|---|---|---|
| `review_sources` | `id UUID PK`, `business_profile_id`, `source TEXT`, `external_account_id`, `encrypted_access_token`, `encrypted_refresh_token`, `token_expires_at`, `status TEXT DEFAULT 'pending'`, `last_sync_at`, timestamps | `UNIQUE(business_profile_id, source)` |
| `reviews` | `id UUID PK`, `business_profile_id`, `source`, `external_review_id`, `rating INT`, `review_text`, `author_name`, `review_created_at`, `review_url`, `raw_payload JSONB`, `response_status TEXT DEFAULT 'new'`, `synced_at`, timestamps | `UNIQUE(source, external_review_id)` |
| `review_responses` | `id UUID PK`, `review_id UUID FK→reviews`, `tone`, `draft_text`, `final_text`, `publish_mode`, `publish_status DEFAULT 'draft'`, `published_at`, `idempotency_key TEXT`, `error_message`, timestamps | |
| `review_sentiment` | `id UUID PK`, `review_id UUID FK→reviews`, `sentiment_label`, `confidence DECIMAL(3,2)`, `themes TEXT[]`, `model_version`, timestamps | `UNIQUE(review_id)` |
| `review_sync_jobs` | `id UUID PK`, `business_profile_id`, `source`, `job_type`, `status DEFAULT 'pending'`, `started_at`, `completed_at`, `error_message`, `metrics JSONB`, timestamps | |
| `review_activity_log` | `id UUID PK`, `business_profile_id`, `action`, `entity_type`, `entity_id`, `actor`, `details JSONB`, timestamps | |
| `review_alert_settings` | `id UUID PK`, `business_profile_id UNIQUE`, `low_rating_threshold INT DEFAULT 3`, `enable_email_digest BOOL DEFAULT true`, `digest_frequency TEXT DEFAULT 'daily'`, `enable_realtime_alerts BOOL DEFAULT true`, timestamps | |
| `review_notifications` | `id UUID PK`, `business_profile_id`, `type`, `title`, `message`, `review_id UUID FK→reviews`, `is_read BOOL DEFAULT false`, timestamps | |

**Indexes:**
- `reviews(business_profile_id, review_created_at DESC)`
- `reviews(business_profile_id, response_status)`
- `reviews(source, external_review_id)`
- `review_notifications(business_profile_id, is_read, created_at DESC)`
- `review_sync_jobs(business_profile_id, created_at DESC)`

**Validation:** Apply migration. Verify all 8 tables exist via `\dt`. Attempt duplicate insert on `reviews(source, external_review_id)` — fails with unique violation. Attempt duplicate on `review_sources(business_profile_id, source)` — fails.

---

### Task 1.2 — Add config settings + encryption module

**What:** Add OAuth/encryption env vars to `Settings`. Create `backend/app/core/encryption.py` with Fernet-based encrypt/decrypt. Add `cryptography` to `requirements.txt`.

**Files:**
- `backend/app/core/config.py` (modify) — add: `google_business_client_id: str = ""`, `google_business_client_secret: str = ""`, `meta_app_id: str = ""`, `meta_app_secret: str = ""`, `review_encryption_key: str = ""`, `review_sync_interval_minutes: int = 15`
- `backend/app/core/encryption.py` (new) — `encrypt_token(plaintext: str, key: str) -> str`, `decrypt_token(ciphertext: str, key: str) -> str` using `cryptography.fernet.Fernet`
- `backend/requirements.txt` (modify) — add `cryptography`

**Validation:** `python -c "from app.core.encryption import encrypt_token, decrypt_token; key='...'; assert decrypt_token(encrypt_token('secret', key), key) == 'secret'"` passes. `python -c "from app.core.config import get_settings; print(get_settings().review_encryption_key)"` prints empty string.

---

### Task 1.3 — Create Pydantic models for reviews

**What:** Request/response models following `models/chat.py` pattern.

**Files:** `backend/app/models/reviews.py` (new)

**Models:**
- `ReviewSourceOut(BaseModel)` — `id, source, status, external_account_id, connected_at, last_sync_at`
- `ReviewFilter(BaseModel)` — `source: str | None`, `response_status: str | None`, `min_rating: int | None`, `max_rating: int | None`, `search: str | None`, `cursor: str | None`, `limit: int = 20`
- `DraftRequest(BaseModel)` — `tone: str = "professional"`
- `PublishRequest(BaseModel)` — `final_text: str`, `idempotency_key: str`
- `AlertSettingsUpdate(BaseModel)` — `low_rating_threshold: int | None`, `enable_email_digest: bool | None`, `digest_frequency: str | None`, `enable_realtime_alerts: bool | None`

**Validation:** `python -c "from app.models.reviews import ReviewFilter; print(ReviewFilter())"` works without error.

---

### Task 1.4 — Create review routes skeleton + register in main.py

**What:** Create `reviews.py` router with `/health` endpoint. Register in `__init__.py` and `main.py`.

**Files:**
- `backend/app/api/routes/reviews.py` (new) — `router = APIRouter(prefix="/reviews", tags=["reviews"])` with `GET /health`
- `backend/app/api/routes/__init__.py` (modify) — add `from .reviews import router as reviews_router` + export
- `backend/app/main.py` (modify) — import `reviews_router`, add `app.include_router(reviews_router, prefix="/api")`

**Validation:** `curl http://localhost:8000/api/reviews/health` returns `{"status":"ok"}` with 200.

---

### Task 1.5 — Add TypeScript interfaces for Reputation Hub

**What:** All review-related types.

**Files:** `frontend/src/types/index.ts` (modify)

**Interfaces:**
- `ReviewSource` — `id, business_profile_id, source, status, external_account_id, connected_at, last_sync_at`
- `Review` — `id, business_profile_id, source, external_review_id, rating, review_text, author_name, review_created_at, review_url, response_status, synced_at, sentiment?: ReviewSentiment`
- `ReviewSentiment` — `sentiment_label, confidence, themes: string[]`
- `ReviewResponseDraft` — `id, review_id, tone, draft_text, final_text, publish_mode, publish_status, published_at, idempotency_key, error_message, created_at`
- `ReviewNotification` — `id, type, title, message, review_id, is_read, created_at`
- `ReviewAnalyticsSummary` — `total_reviews, avg_rating, rating_distribution: Record<number,number>, response_rate, avg_response_time_hours, sentiment_breakdown: {positive, neutral, negative}`
- `AlertSettings` — `low_rating_threshold, enable_email_digest, digest_frequency, enable_realtime_alerts`

**Validation:** `npm run build` passes with no type errors.

---

### Task 1.6 — Create frontend reputation layout with tab navigation

**What:** Shared layout with header + horizontal sub-nav tabs.

**Files:** `frontend/src/app/reputation/layout.tsx` (new)

**Details:** `"use client"` component. Uses `usePathname()` for active tab highlight. Tabs: Inbox (`/reputation`), Analytics (`/reputation/analytics`), Competitors (`/reputation/competitors`), Connections (`/reputation/connections`), Settings (`/reputation/settings`). Uses `dark-header` for header, pill-style tabs. Renders `{children}`.

**Validation:** Navigate to `http://localhost:3000/reputation` — see header + tabs. Clicking tabs changes URL and highlights active tab.

---

### Task 1.7 — Create 5 placeholder pages

**What:** Simple placeholder `"use client"` pages for all sub-routes.

**Files:**
- `frontend/src/app/reputation/page.tsx` (new) — "Review Inbox"
- `frontend/src/app/reputation/analytics/page.tsx` (new) — "Analytics"
- `frontend/src/app/reputation/competitors/page.tsx` (new) — "Competitors"
- `frontend/src/app/reputation/connections/page.tsx` (new) — "Connections"
- `frontend/src/app/reputation/settings/page.tsx` (new) — "Settings"

Each renders a centered `dark-card` with page title and "Coming soon" text.

**Validation:** Navigate to each URL — placeholder renders. `npm run build` passes.

---

### Task 1.8 — Add "Reputation" nav link to dashboard header

**What:** Insert "Reputation" link in the dashboard header nav between "Community" and "My Business".

**Files:** `frontend/src/app/dashboard/page.tsx` (modify — lines 309-320)

**Details:** Add `<Link href="/reputation" className="px-4 py-2 text-white/70 hover:text-white text-sm font-medium transition-colors">Reputation</Link>` between the Community and My Business links.

**Validation:** Visit `/dashboard` — see "Reputation" link. Clicking navigates to `/reputation`.

---

## Sprint 2: Backend Data Layer — Repositories + Connection Service + Connections UI

**Goal:** Full CRUD repos for all review tables. Connection service handles OAuth URL generation and token storage with encryption. Connections page shows platform cards with connect/disconnect. Business profile ownership validated on all endpoints.

**Demo:** Visit `/reputation/connections` — see 3 platform cards. Click "Connect" on Google — OAuth URL returned. `curl GET /api/reviews/connections` returns connection list.

---

### Task 2.1 — Create `review_source_repository.py`

**What:** CRUD for `review_sources` table.

**Files:**
- `backend/app/repositories/review_source_repository.py` (new)
- `backend/app/repositories/__init__.py` (modify — add export)

**Methods:**
- `create(business_profile_id, source, **kwargs) -> dict`
- `get_by_business(business_profile_id) -> list[dict]`
- `get_by_business_and_source(business_profile_id, source) -> dict | None`
- `update_tokens(source_id, encrypted_access_token, encrypted_refresh_token, token_expires_at) -> dict | None`
- `update_status(source_id, status) -> dict | None`
- `update_last_sync(source_id) -> dict | None`
- `delete(source_id) -> bool`

**Validation:** pytest test: create source, retrieve it, update tokens, delete it — all assertions pass.

---

### Task 2.2 — Create `review_repository.py`

**What:** CRUD for `reviews` + `review_responses` with cursor-based inbox pagination. Handle upsert for re-synced reviews (update if `review_text` or `rating` changed).

**Files:**
- `backend/app/repositories/review_repository.py` (new)
- `backend/app/repositories/__init__.py` (modify — add export)

**Methods:**
- `upsert_review(**kwargs) -> dict` — insert or update on `(source, external_review_id)`
- `get_inbox(business_profile_id, source?, response_status?, min_rating?, max_rating?, search?, cursor?, limit=20) -> tuple[list[dict], str | None]` — cursor = `review_created_at` ISO string; query chaining with `.lt("review_created_at", cursor)`, `.order("review_created_at", desc=True)`, `.limit(limit + 1)`; if result has limit+1 rows, pop last and use its `review_created_at` as `next_cursor`
- `get_by_id(review_id) -> dict | None`
- `get_count_by_business(business_profile_id) -> int`
- `update_response_status(review_id, status) -> dict | None`
- `create_response(review_id, tone, draft_text, **kwargs) -> dict`
- `get_responses(review_id) -> list[dict]`
- `update_response_publish(response_id, final_text, publish_status, published_at?, error_message?) -> dict | None`
- `get_response_by_idempotency_key(idempotency_key) -> dict | None` — for duplicate publish prevention

**Validation:** pytest test: upsert review, query inbox with cursor pagination (insert 5, limit=2, verify 3 pages), upsert same review with changed text — verify update not duplicate.

---

### Task 2.3 — Create `review_sentiment_repository.py`

**What:** CRUD for `review_sentiment`.

**Files:**
- `backend/app/repositories/review_sentiment_repository.py` (new)
- `backend/app/repositories/__init__.py` (modify — add export)

**Methods:**
- `upsert(review_id, sentiment_label, confidence, themes, model_version) -> dict`
- `get_by_review(review_id) -> dict | None`
- `get_by_business(business_profile_id, days=30) -> list[dict]` — join with `reviews` to filter by business + date

**Validation:** pytest test: upsert sentiment, retrieve it, upsert again (same review_id) — verify update, count stays 1.

---

### Task 2.4 — Create `review_notification_repository.py`

**What:** CRUD for `review_notifications` + `review_alert_settings`.

**Files:**
- `backend/app/repositories/review_notification_repository.py` (new)
- `backend/app/repositories/__init__.py` (modify — add export)

**Methods:**
- `create_notification(business_profile_id, type, title, message?, review_id?) -> dict`
- `get_notifications(business_profile_id, unread_only=False, limit=50) -> list[dict]`
- `get_unread_count(business_profile_id) -> int`
- `mark_read(notification_id) -> bool`
- `mark_all_read(business_profile_id) -> int`
- `get_alert_settings(business_profile_id) -> dict | None`
- `upsert_alert_settings(business_profile_id, **kwargs) -> dict`

**Validation:** pytest test: create notification, list it, mark read, verify `is_read=true`. Upsert alert settings, retrieve — matches.

---

### Task 2.5 — Create `connection_service.py` with ownership validation

**What:** OAuth flow orchestration, token encrypt/decrypt, connection management. Include a shared `verify_business_ownership(business_profile_id, session_id)` helper used by all endpoints.

**Files:**
- `backend/app/services/reviews/__init__.py` (new)
- `backend/app/services/reviews/connection_service.py` (new)
- `backend/app/services/__init__.py` (modify — add export)

**Methods:**
- `get_connections(business_profile_id) -> list[dict]` — returns sources without raw tokens
- `start_oauth(business_profile_id, source) -> str` — builds OAuth URL for Google (client_id, redirect_uri, scopes: `business.manage`). For Yelp: returns instructions (API key input). For Facebook: returns Meta OAuth URL.
- `handle_callback(business_profile_id, source, code) -> dict` — exchange code for tokens via httpx, encrypt with `encrypt_token()`, store via repo, set `status='connected'`
- `disconnect(business_profile_id, source) -> bool`
- `refresh_token_if_needed(source_record) -> dict` — check `token_expires_at`, refresh if within 5min of expiry
- `verify_business_ownership(business_profile_id, session_id, db) -> bool` — query `business_profiles` table to confirm `session_id` matches

**Validation:** Unit test: `start_oauth("google")` returns URL containing `accounts.google.com/o/oauth2`. Encrypt/decrypt round-trip on tokens. `verify_business_ownership` returns False for wrong session_id.

---

### Task 2.6 — Add connection endpoints to reviews route + deps.py

**What:** REST endpoints for connection management with ownership checks.

**Files:**
- `backend/app/api/routes/reviews.py` (modify)
- `backend/app/api/deps.py` (modify — add `get_connection_service`)

**Endpoints:**
- `GET /connections?session_id=...` — look up business_profile by session, return connections
- `POST /connections/{source}/start?session_id=...` — returns `{"oauth_url": "..."}`
- `POST /connections/{source}/callback` — body: `{session_id, code}` — returns source record
- `DELETE /connections/{source}?session_id=...` — disconnect

All endpoints validate business ownership via `connection_service.verify_business_ownership()`.

**Validation:** `curl POST /api/reviews/connections/google/start?session_id=test` returns OAuth URL. `curl GET /api/reviews/connections?session_id=test` returns `[]`. Wrong session_id returns 403.

---

### Task 2.7 — Add connection API functions to frontend

**What:** API client functions for connections.

**Files:** `frontend/src/lib/api.ts` (modify)

**Functions:**
- `fetchReviewConnections(sessionId: string): Promise<ReviewSource[]>`
- `startOAuthConnection(sessionId: string, source: string): Promise<{oauth_url: string}>`
- `handleOAuthCallback(sessionId: string, source: string, code: string): Promise<ReviewSource>`
- `disconnectSource(sessionId: string, source: string): Promise<void>`

**Validation:** `npm run build` passes.

---

### Task 2.8 — Build Connections page with ConnectionCard

**What:** Replace connections placeholder with platform cards showing connection status.

**Files:**
- `frontend/src/app/reputation/connections/page.tsx` (modify)
- `frontend/src/components/reputation/ConnectionCard.tsx` (new)

**Details:** Page fetches connections via `fetchReviewConnections`. Renders 3 `ConnectionCard` components (Google, Yelp, Facebook). Each card shows: platform logo/icon, name, status badge (Connected=emerald, Disconnected=gray, Expired=amber), last sync time, connect/reconnect/disconnect actions. Connect button calls `startOAuthConnection` and opens URL in new window. Disconnect is behind `...` overflow menu. Security info banner at top (`bg-blue-500/10`). Uses `dark-card` styling.

For Yelp card: shows API key input field instead of OAuth button. Label: "Read-only: reply via Yelp website".

**Validation:** Navigate to `/reputation/connections` — see 3 platform cards. Click "Connect" on Google — new window opens to OAuth URL. Disconnect available for connected sources.

---

## Sprint 3: Review Sync + Inbox

**Goal:** Platform clients fetch reviews. Celery syncs on schedule. Inbox page shows real reviews with filters and cursor pagination. Seed data available for development.

**Demo:** Trigger sync via UI. Reviews appear in inbox. Filter by source, rating, status. Paginate. Search.

---

### Task 3.1 — Create seed data script

**What:** Script that populates the DB with realistic sample reviews across Google, Yelp, and Facebook sources for development/demo.

**Files:** `backend/scripts/seed_reviews.py` (new)

**Details:** Inserts: 1 `review_sources` record per platform (mock connected), 50 `reviews` (mixed sources, ratings 1-5, varied dates over 90 days, varied `response_status`), 20 `review_sentiment` records. Uses realistic review text (restaurant/retail themed).

**Validation:** Run `python scripts/seed_reviews.py` — 50 reviews in DB. Query `reviews` table — varied sources, ratings, dates.

---

### Task 3.2 — Create Google Business client

**What:** Client for Google My Business API — list reviews, reply to review. Mock fallback when no credentials.

**Files:**
- `backend/app/clients/reviews/__init__.py` (new)
- `backend/app/clients/reviews/google_business_client.py` (new)

**Methods:**
- `list_reviews(account_id, location_id, page_token?) -> dict` — GET `mybusiness.googleapis.com/v4/.../reviews` with Bearer auth
- `reply_to_review(account_id, location_id, review_id, comment) -> dict` — PUT `.../reviews/{id}/updateReply`
- `_get_mock_reviews() -> dict` — returns 10 synthetic reviews when `settings.google_business_client_id` is empty

Uses `httpx.AsyncClient`. Handles 401 (raise `AuthExpiredError`), 429 (raise `RateLimitError`).

**Validation:** With no credentials: `client.list_reviews(...)` returns synthetic reviews. Verify response shape matches expected schema.

---

### Task 3.3 — Create Yelp review client

**What:** Read-only client for Yelp Fusion API. Documents the 3-review limitation prominently.

**Files:** `backend/app/clients/reviews/yelp_review_client.py` (new)

**Methods:**
- `get_reviews(business_id, sort_by="yelp_sort") -> dict` — GET `api.yelp.com/v3/businesses/{id}/reviews` with API key auth. **NOTE: Yelp API returns max 3 reviews.**
- `get_reply_deeplink(business_alias) -> str` — returns `https://biz.yelp.com/biz/{alias}/reviews`
- `_get_mock_reviews() -> dict` — 3 synthetic Yelp reviews when no API key

**Validation:** Mock mode returns 3 reviews. Verify shape matches Yelp API docs.

---

### Task 3.4 — Create Meta review client stub

**What:** Placeholder for Facebook/Meta reviews (Phase 2).

**Files:** `backend/app/clients/reviews/meta_review_client.py` (new)

**Methods:**
- `get_reviews(page_id) -> dict` — returns `{"reviews": [], "message": "Meta integration Phase 2"}`
- `reply_to_review(...)` — raises `NotImplementedError`

**Validation:** Import and call — returns empty list.

---

### Task 3.5 — Create review sync service (pull + upsert)

**What:** Service that pulls reviews from connected platforms and upserts into `reviews` table. Includes normalizer per platform. Post-sync hook point for sentiment (no-op initially).

**Files:** `backend/app/services/reviews/review_aggregation_service.py` (new)

**Methods:**
- `sync_source(source_record) -> dict` — decrypt token, instantiate appropriate client, fetch reviews, normalize each, upsert via repo. Returns `{"synced": N, "new": M, "errors": []}`. Creates `review_sync_jobs` record (started → completed/failed). Calls `_post_sync_hook(new_review_ids)` — no-op for now.
- `sync_all(business_profile_id) -> list[dict]` — get all connected sources, sync each.
- `_normalize_google_review(raw, source_record) -> dict` — maps Google fields to `reviews` schema
- `_normalize_yelp_review(raw, source_record) -> dict` — maps Yelp fields
- `_post_sync_hook(new_review_ids) -> None` — extensibility point for sentiment/alerts (Sprint 5)

**Validation:** With mock data: call `sync_source(mock_google_source)` — reviews inserted in DB. Call again — upsert, no duplicates. Check `review_sync_jobs` has a record.

---

### Task 3.6 — Create review inbox service (query + filter)

**What:** Service for inbox queries, delegating to review_repository.

**Files:** `backend/app/services/reviews/review_aggregation_service.py` (modify — add methods)

**Methods:**
- `get_inbox(business_profile_id, filters: dict) -> tuple[list[dict], str | None, int]` — delegates to `ReviewRepository.get_inbox()`. Joins sentiment data if available. Returns (reviews, next_cursor, total_count).
- `get_review_detail(review_id) -> dict | None` — review + sentiment + response history

**Validation:** Seed 50 reviews. Call `get_inbox(bp_id, limit=10)` — returns 10 reviews + cursor. Call again with cursor — returns next 10. Filter by source="google" — only Google reviews.

---

### Task 3.7 — Create sync Celery task + beat schedule

**What:** Celery tasks for sync + token refresh. Register in beat schedule.

**Files:**
- `backend/app/workers/review_tasks.py` (new)
- `backend/app/workers/celery_app.py` (modify — add to `include` list + beat_schedule)

**Tasks:**
- `sync_reviews_for_source(source_id)` — `bind=True, max_retries=3`. Gets source record, calls `sync_source()`. On `AuthExpiredError`: update source status to `token_expired`, create notification.
- `sync_all_reviews()` — fetches all `review_sources` with `status='connected'`, dispatches `sync_reviews_for_source.delay()` for each.
- `refresh_expiring_tokens()` — queries sources where `token_expires_at` is within 30min, calls `connection_service.refresh_token_if_needed()`.

**Beat schedule:** `sync-reviews` every 15min calling `sync_all_reviews`. `refresh-tokens` every 30min calling `refresh_expiring_tokens`.

**Validation:** Call `sync_all_reviews.delay()` — reviews sync. Check beat schedule is registered in `celery_app.conf.beat_schedule`.

---

### Task 3.8 — Add sync and inbox REST endpoints

**What:** Endpoints for manual sync trigger, inbox retrieval, and review detail.

**Files:**
- `backend/app/api/routes/reviews.py` (modify)
- `backend/app/api/deps.py` (modify — add `get_review_aggregation_service`)

**Endpoints:**
- `POST /sync?session_id=...` — triggers `sync_all()`, returns results
- `GET /inbox?session_id=...&source=...&response_status=...&min_rating=...&max_rating=...&search=...&cursor=...&limit=20` — returns `{"reviews": [...], "next_cursor": ..., "total_count": N}`
- `GET /{review_id}?session_id=...` — full review detail

All validate business ownership.

**Validation:** `curl POST /api/reviews/sync?session_id=...` triggers sync. `curl GET /api/reviews/inbox?session_id=...` returns reviews. Pagination works with cursor param.

---

### Task 3.9 — Add inbox API functions to frontend

**What:** Fetch functions for sync, inbox, review detail.

**Files:** `frontend/src/lib/api.ts` (modify)

**Functions:**
- `syncReviews(sessionId): Promise<any>`
- `fetchReviewInbox(sessionId, params: {source?, response_status?, min_rating?, max_rating?, search?, cursor?, limit?}): Promise<{reviews: Review[], next_cursor: string | null, total_count: number}>`
- `fetchReviewDetail(reviewId, sessionId): Promise<Review>`

**Validation:** `npm run build` passes.

---

### Task 3.10 — Build Inbox page with ReviewCard + InboxFilters

**What:** Replace inbox placeholder with filterable review list and cursor pagination.

**Files:**
- `frontend/src/app/reputation/page.tsx` (modify)
- `frontend/src/components/reputation/ReviewCard.tsx` (new)
- `frontend/src/components/reputation/InboxFilters.tsx` (new)
- `frontend/src/components/reputation/EmptyState.tsx` (new)

**Details:**
- `InboxFilters`: platform toggle buttons (multi-select), star rating toggles, response status dropdown, search input (debounced 300ms), "Clear filters" button
- `ReviewCard`: horizontal `dark-card` row — platform icon, star rating (amber), author name, date, review text (2-line truncate), sentiment dot, response status badge (amber "Needs Response" / emerald "Responded" / blue pulse "New"). Clickable (onClick prop).
- Inbox page: manages filter state, fetches `fetchReviewInbox` with filters, renders cards. "Load more" button using cursor pagination. "Sync Now" button. Summary bar: "47 reviews | 12 need response | Avg 4.3 stars".
- `EmptyState`: reusable component with icon, title, description, CTA button. Used for: no connections → "Connect your first platform" CTA to `/reputation/connections`; no reviews → "No reviews yet. Reviews appear after next sync."; no filter matches → "No reviews match your filters" + "Clear filters".
- Loading: 3 skeleton `dark-card` placeholders with `animate-shimmer`.

**Validation:** Open `/reputation` — see filter bar + review cards. Filter by source — list updates. Click "Load more" — next page loads. "Sync Now" refreshes. Empty state shows when appropriate.

---

## Sprint 4: AI Response Generation + Review Detail Slide-over

**Goal:** Clicking a review opens slide-over with full detail. AI generates draft responses in 3 tones. User can edit and publish to Google or deep-link to Yelp. Idempotency prevents double-publish.

**Demo:** Click review → slide-over opens → "Generate AI Responses" → 3 drafts appear → edit one → publish → status updates to "Responded".

---

### Task 4.1 — Create review response service

**What:** LLM draft generation + publish flow with idempotency and platform-aware behavior.

**Files:**
- `backend/app/services/reviews/review_response_service.py` (new)
- `backend/app/services/reviews/__init__.py` (modify — add export)
- `backend/app/services/__init__.py` (modify — add export)

**Methods:**
- `generate_drafts(review_id) -> list[dict]` — fetch review, generate 3 drafts (professional/friendly/apologetic) using LLM. Each draft: max 4096 chars (Google limit). System prompt includes: review text, rating, business name, platform constraints. Guardrails: no fabricated promises, no unsafe phrasing, no personal attacks. Saves 3 `review_responses` records.
- `publish_response(response_id, final_text, idempotency_key) -> dict` — check idempotency key first (return existing response if found). If Google source: call `GoogleBusinessClient.reply_to_review()`. If Yelp: set `publish_mode='deeplink'`, return deep link URL. Update `review_responses` + `reviews.response_status`. Log to `review_activity_log`.
- `_build_draft_prompt(review, tone) -> str` — tone-specific prompt template

**Validation:** Call `generate_drafts(review_id)` — 3 drafts in DB, all ≤4096 chars. Call `publish_response` twice with same idempotency_key — second call returns same response (no duplicate). Yelp review → returns deeplink URL instead of API publish.

---

### Task 4.2 — Add draft and publish endpoints

**What:** REST endpoints for generating drafts and publishing.

**Files:**
- `backend/app/api/routes/reviews.py` (modify)
- `backend/app/api/deps.py` (modify — add `get_review_response_service`)

**Endpoints:**
- `POST /{review_id}/draft?session_id=...` — body: `DraftRequest` — returns list of 3 drafts
- `POST /{review_id}/publish?session_id=...` — body: `PublishRequest` — returns updated response with `publish_status`

**Validation:** `curl POST /api/reviews/{id}/draft?session_id=...` returns 3 drafts. `curl POST /api/reviews/{id}/publish` with idempotency_key returns published status. Repeat with same key — same response, no duplicate.

---

### Task 4.3 — Add frontend API functions for drafts/publish

**What:** API client functions.

**Files:** `frontend/src/lib/api.ts` (modify)

**Functions:**
- `generateDrafts(reviewId, sessionId, tone?): Promise<ReviewResponseDraft[]>`
- `publishResponse(reviewId, sessionId, body: {final_text, idempotency_key}): Promise<ReviewResponseDraft>`

**Validation:** `npm run build` passes.

---

### Task 4.4 — Build ReviewDetailPanel slide-over

**What:** Slide-over panel for full review detail with AI response generation.

**Files:** `frontend/src/components/reputation/ReviewDetailPanel.tsx` (new)

**Details:**
- Props: `review: Review | null`, `isOpen: boolean`, `onClose: () => void`, `onStatusUpdate: (reviewId, status) => void`
- Desktop: `fixed inset-y-0 right-0 w-[480px]` with backdrop blur. Mobile: full-screen (`w-full`).
- **Review section:** platform icon + label, star rating (filled amber / empty `text-white/10`), author name, date, external link icon, full review text, sentiment badge + theme tags
- **AI Response section:** "Generate AI Responses" button → loading spinner → 3 tone cards (Professional/Friendly/Apologetic). Each card: tone label, draft text, "Use This" button
- **Edit area:** textarea populated when "Use This" clicked, character counter (e.g., "342/4096" — red when exceeded, publish disabled)
- **Action row:** "Publish to Google" (`bg-white text-black`) for Google source. "Open on Yelp" (`bg-white/10`) + "Copy" (`bg-white/5`) for Yelp. "Regenerate" button.
- **Publish states:** spinner → green checkmark animation → "Published" badge. Error: inline red message with retry.
- **Response history:** collapsible section showing previous drafts

**Validation:** Open panel — review displays correctly. Click "Generate" — 3 drafts appear. Select one — populates textarea. Edit text — character counter updates. Publish — status changes. Yelp review — shows "Open on Yelp" instead of "Publish".

---

### Task 4.5 — Wire ReviewDetailPanel into Inbox page

**What:** Connect slide-over to inbox page state.

**Files:** `frontend/src/app/reputation/page.tsx` (modify)

**Details:** Add state: `selectedReview`, `isPanelOpen`. ReviewCard onClick → set selectedReview + open panel. Pass `onStatusUpdate` callback to update review's `response_status` in local list after publish. On close → clear selection.

**Validation:** Full flow: click review in inbox → panel opens → generate drafts → publish → panel shows "Published" → close panel → inbox card now shows "Responded" badge.

---

## Sprint 5: Sentiment Analysis + Analytics Dashboard

**Goal:** Every synced review gets automatic LLM sentiment classification (positive/neutral/negative + themes). Analytics page shows rating distribution, volume trends, sentiment breakdown, platform comparison, and top themes.

**Demo:** Open `/reputation/analytics` — see populated charts from seeded/synced review data.

---

### Task 5.1 — Create sentiment service

**What:** LLM-based sentiment classification and theme extraction.

**Files:**
- `backend/app/services/reviews/sentiment_service.py` (new)
- `backend/app/services/reviews/__init__.py` (modify — add export)

**Methods:**
- `classify_review(review_id) -> dict` — fetch review, call LLM (temperature ~0) with structured prompt requesting JSON: `{sentiment_label, confidence, themes}`. Parse response, upsert to `review_sentiment`.
- `classify_batch(review_ids) -> list[dict]` — classify multiple, sequential to avoid rate limits.
- `_build_classification_prompt(review_text, rating) -> str` — prompt requesting JSON output with allowed values: `sentiment_label` in [positive, neutral, negative], `confidence` 0-1, `themes` from [service_speed, food_quality, staff_friendliness, cleanliness, pricing, ambiance, value, location, wait_time, other]

**Validation:** Call `classify_review` with a clearly positive 5-star review — sentiment_label = "positive", confidence > 0.8. Call with 1-star complaint about slow service — "negative", themes includes "service_speed".

---

### Task 5.2 — Integrate sentiment into sync pipeline + Celery task

**What:** After syncing new reviews, automatically trigger sentiment classification.

**Files:**
- `backend/app/services/reviews/review_aggregation_service.py` (modify — implement `_post_sync_hook`)
- `backend/app/workers/review_tasks.py` (modify — add `classify_reviews_batch` task)

**Details:** `_post_sync_hook(new_review_ids)` dispatches `classify_reviews_batch.delay(new_review_ids)`. Celery task: `classify_reviews_batch(review_ids)` — calls `sentiment_service.classify_batch()`.

**Validation:** Trigger sync — new reviews get sentiment records within seconds (via Celery). Check `review_sentiment` table has entries for new reviews.

---

### Task 5.3 — Create analytics service

**What:** Aggregation queries for analytics charts.

**Files:**
- `backend/app/services/reviews/analytics_service.py` (new)
- `backend/app/services/reviews/__init__.py` (modify — add export)

**Methods:**
- `get_summary(business_profile_id) -> dict` — `total_reviews`, `avg_rating`, `rating_distribution` (1-5 → count), `response_rate` (% not 'new'), `avg_response_time_hours`, `sentiment_breakdown` (positive/neutral/negative counts)
- `get_trends(business_profile_id, days=30) -> dict` — daily data points: `{date, avg_rating, count, sentiment_positive, sentiment_negative}`
- `get_top_themes(business_profile_id, days=30, limit=10) -> list[dict]` — aggregate themes from `review_sentiment.themes`, return `{theme, count, positive_count, negative_count}`
- `get_platform_comparison(business_profile_id) -> list[dict]` — per source: `{source, count, avg_rating, sentiment_positive_pct}`

**Validation:** With 50 seeded reviews + sentiment: `get_summary` returns valid aggregates. `get_trends(days=30)` returns daily data points. `get_top_themes` returns ranked themes.

---

### Task 5.4 — Add analytics endpoints

**What:** REST endpoints for analytics data.

**Files:**
- `backend/app/api/routes/reviews.py` (modify)
- `backend/app/api/deps.py` (modify — add `get_review_analytics_service`)

**Endpoints:**
- `GET /analytics/summary?session_id=...`
- `GET /analytics/trends?session_id=...&days=30`
- `GET /analytics/themes?session_id=...&days=30&limit=10`
- `GET /analytics/platforms?session_id=...`

**Validation:** `curl` each endpoint — returns populated data.

---

### Task 5.5 — Add frontend API functions for analytics

**Files:** `frontend/src/lib/api.ts` (modify)

**Functions:**
- `fetchAnalyticsSummary(sessionId): Promise<ReviewAnalyticsSummary>`
- `fetchAnalyticsTrends(sessionId, days?): Promise<{data_points: Array<...>}>`
- `fetchTopThemes(sessionId, days?, limit?): Promise<Array<...>>`
- `fetchPlatformComparison(sessionId): Promise<Array<...>>`

**Validation:** `npm run build` passes.

---

### Task 5.6 — Build Analytics page layout + summary cards

**What:** Analytics page layout with 4 top-row ScoreCards (reuse pattern from dashboard).

**Files:** `frontend/src/app/reputation/analytics/page.tsx` (modify)

**Details:** Fetches `fetchAnalyticsSummary` on mount. Top row: 4 `dark-card` score cards:
1. Overall Rating — large number, color-coded (green≥4, yellow≥3, red<3)
2. Total Reviews — count + "+N this month"
3. Response Rate — percentage
4. Avg Sentiment — "82% Positive"

Period selector pills (7d / 30d / 90d) that re-fetch trends data. Loading: independent skeleton per section.

**Validation:** Navigate to `/reputation/analytics` — see 4 metric cards with real data. Toggle period — data refreshes.

---

### Task 5.7 — Build analytics chart components

**What:** 4 chart components for analytics page.

**Files:**
- `frontend/src/components/reputation/RatingDistributionChart.tsx` (new) — horizontal bar chart (div-based, `bg-amber-400` fill on `bg-white/5` track per star 1-5)
- `frontend/src/components/reputation/SentimentTrendChart.tsx` (new) — stacked bar chart showing daily positive/neutral/negative. Div-based or simple SVG. emerald/gray/red bars.
- `frontend/src/components/reputation/ThemeBreakdown.tsx` (new) — horizontal bars labeled by theme name, bar width by count, color by net sentiment (green=positive, red=negative). Max 10.
- `frontend/src/components/reputation/PlatformComparisonCard.tsx` (new) — table: source icon, avg rating, review count, sentiment bar.

Integrate all into analytics page in a 2-column grid layout.

**Validation:** All 4 charts render with real data. Empty states show "No data yet" with dashed border. Charts are readable and use correct colors.

---

## Sprint 6: Competitors + Notifications + Alerts

**Goal:** Competitors page compares your review metrics against tracked competitors. Notification system alerts on low-rating reviews. Settings page configures thresholds. Bell icon shows unread count.

**Demo:** See competitor comparison. Trigger a low-rating review sync → notification appears in bell. Configure settings.

---

### Task 6.1 — Add competitor review metrics to analytics service

**What:** Extend analytics service with competitor comparison using existing `tracked_competitors` data.

**Files:** `backend/app/services/reviews/analytics_service.py` (modify)

**Methods:**
- `get_competitor_comparison(business_profile_id) -> dict` — fetch your review metrics (from `reviews` table) + tracked competitors (from `tracked_competitors` table, reusing their `rating`, `review_count`, `strengths`, `weaknesses`). Returns `{your_metrics: {...}, competitors: [{name, rating, review_count, strengths, weaknesses}]}`. No new external API calls.

**Validation:** With tracked competitors in DB: `get_competitor_comparison` returns your metrics alongside competitors.

---

### Task 6.2 — Add competitor endpoint

**Files:** `backend/app/api/routes/reviews.py` (modify)

**Endpoint:** `GET /competitors?session_id=...` — returns competitor comparison.

**Validation:** `curl` returns comparison data.

---

### Task 6.3 — Add frontend API + build Competitors page

**Files:**
- `frontend/src/lib/api.ts` (modify — add `fetchCompetitorComparison`)
- `frontend/src/app/reputation/competitors/page.tsx` (modify)
- `frontend/src/components/reputation/CompetitorComparisonTable.tsx` (new)

**Details:** Table/grid rows: "You" (first, highlighted blue) + each competitor. Columns: name, avg rating, total reviews, sentiment. Highlight where you lead (green) or trail (red). Reuse strength/weakness tag pattern from dashboard's `CompetitorCard`. EmptyState: "Track competitors in Dashboard to compare" + link to `/dashboard`.

**Validation:** Navigate to `/reputation/competitors` — see comparison table. Your business in first row (blue). Competitors below. No competitors → shows empty state with link.

---

### Task 6.4 — Create notification generation in sync pipeline

**What:** After sync, check new reviews against alert thresholds and generate notifications.

**Files:**
- `backend/app/workers/review_tasks.py` (modify — add `check_and_notify` task)
- `backend/app/services/reviews/review_aggregation_service.py` (modify — extend `_post_sync_hook`)

**Details:** `check_and_notify(business_profile_id, new_review_ids)` — fetch alert settings, for each new review check `rating <= low_rating_threshold`, create notification if triggered. Batch: if 10+ new reviews in single sync, create single notification "47 new reviews imported" instead of flooding. Chain after `classify_reviews_batch` in `_post_sync_hook`.

**Validation:** Set threshold to 3. Sync a 1-star review → notification in `review_notifications`. Sync 20 reviews at once → single batch notification.

---

### Task 6.5 — Add notification + alert settings endpoints

**Files:** `backend/app/api/routes/reviews.py` (modify)

**Endpoints:**
- `GET /notifications?session_id=...&unread_only=false` — notification list + `unread_count`
- `POST /notifications/{notification_id}/read?session_id=...`
- `POST /notifications/read-all?session_id=...`
- `GET /alerts/settings?session_id=...`
- `PUT /alerts/settings?session_id=...` — body: `AlertSettingsUpdate`

**Validation:** `curl` each endpoint. Create notification, mark read, verify count.

---

### Task 6.6 — Add notification/settings frontend API functions

**Files:** `frontend/src/lib/api.ts` (modify)

**Functions:** `fetchNotifications`, `markNotificationRead`, `markAllNotificationsRead`, `fetchAlertSettings`, `updateAlertSettings`

**Validation:** `npm run build` passes.

---

### Task 6.7 — Build Settings page

**Files:** `frontend/src/app/reputation/settings/page.tsx` (modify)

**Details:** Fetches current alert settings. Form with: low rating threshold selector (1-5), email digest toggle + frequency (daily/weekly), real-time alerts toggle. Save button calls `updateAlertSettings`. Success toast feedback. `dark-card` for form sections.

**Validation:** Visit `/reputation/settings` — form shows defaults. Change threshold, save — persists on reload.

---

### Task 6.8 — Build NotificationBell in reputation layout

**Files:**
- `frontend/src/app/reputation/layout.tsx` (modify)
- `frontend/src/components/reputation/NotificationBell.tsx` (new)

**Details:** Bell icon in reputation header. Polls `fetchNotifications(sessionId, true)` every 30s. Red badge with unread count (hidden if 0). Click opens dropdown panel: recent notifications with timestamp + platform icon + brief text. Unread items: `bg-white/5` highlight + blue left border. "Mark all read" link. Click notification → could navigate to review.

**Validation:** Trigger low-rating review sync → bell shows count. Click → see notification. "Mark all read" → count disappears.

---

## Sprint 7: Polish, Error Handling, Production Hardening

**Goal:** Activity logging, email digest, error handling with retry, loading/error/empty states on all pages, responsive design, final integration verification. Feature is production-ready.

**Demo:** Full end-to-end walkthrough at all screen sizes. No broken states.

---

### Task 7.1 — Add activity logging across all services

**What:** Log significant actions to `review_activity_log`.

**Files:**
- `backend/app/services/reviews/connection_service.py` (modify)
- `backend/app/services/reviews/review_aggregation_service.py` (modify)
- `backend/app/services/reviews/review_response_service.py` (modify)

**Details:** After each significant action, insert into `review_activity_log`: connection events (connect/disconnect), sync events (start/complete/fail), draft generation, publish events. Each entry: `action`, `entity_type`, `entity_id`, `actor` (business_profile_id), `details` (JSONB).

**Validation:** Perform connect, sync, draft, publish — verify `review_activity_log` has entries for each.

---

### Task 7.2 — Create email digest Celery task (stub)

**What:** Daily/weekly digest summarizing new reviews.

**Files:** `backend/app/workers/review_tasks.py` (modify)

**Task:** `send_review_digests()` — query businesses with `enable_email_digest=true`, compute: new reviews since last digest, rating changes, unresponded count. Format as HTML. **Stub the actual send** (log content). Beat schedule: daily at 8am UTC.

**Validation:** Manually call task — verify it processes businesses and logs digest content.

---

### Task 7.3 — Add error handling + retry logic to clients and sync

**What:** Typed exceptions, proper error handling, retry with backoff.

**Files:**
- `backend/app/clients/reviews/google_business_client.py` (modify)
- `backend/app/clients/reviews/yelp_review_client.py` (modify)
- `backend/app/services/reviews/review_aggregation_service.py` (modify)
- `backend/app/workers/review_tasks.py` (modify)

**Details:** Define exceptions: `AuthExpiredError`, `RateLimitError`, `PlatformError`. Clients raise typed exceptions on 401/429/5xx. Sync service catches, logs to `review_sync_jobs.error_message`. On `AuthExpiredError`: update source status to `token_expired`, create notification. Celery: `max_retries=3`, exponential backoff (`countdown=60 * 2^retries`).

**Validation:** Simulate 401 from Google → source status = "token_expired", notification created. Simulate 429 → task retries with backoff.

---

### Task 7.4 — Add loading/error/empty states to all pages

**What:** Polish all reputation pages.

**Files:** All 5 page files + components (modify)

**Details:** Per page:
- **Loading:** skeleton `dark-card` placeholders with `animate-shimmer`
- **Error:** error card with retry button
- **Empty:** contextual EmptyState component (no connections, no reviews, no matches, no competitors)

Follow `dashboard/page.tsx` loading pattern.

**Validation:** Disconnect network → error states. Clear data → empty states. Reconnect → loading → content.

---

### Task 7.5 — Add responsive design to all components

**What:** Mobile-friendly at 375px width.

**Files:** layout.tsx, all page files, ReviewCard, ReviewDetailPanel, InboxFilters (modify)

**Details:**
- Tab nav: horizontal scroll on mobile
- ReviewDetailPanel: `w-full` on mobile instead of `w-[480px]`
- InboxFilters: stack vertically on mobile
- Analytics grid: single column on mobile
- Charts: responsive width

Use Tailwind responsive prefixes (`sm:`, `md:`, `lg:`).

**Validation:** Chrome DevTools 375px — all pages usable. Tabs scroll. Panel fills screen. Cards stack.

---

### Task 7.6 — Final build verification + formatting

**What:** Verify everything builds and is formatted.

**Files:** None new

**Steps:**
1. `cd backend && black --check app/` — no formatting issues
2. `cd frontend && npm run build` — passes
3. `cd frontend && npm run lint` — passes
4. Manual E2E: connect platform (mock) → sync → inbox → filter → detail → generate drafts → publish → analytics → competitors → notifications → settings
5. Verify all endpoints respond correctly (health, connections, sync, inbox, detail, draft, publish, analytics/*, competitors, notifications, alerts/settings)

**Validation:** All commands pass. All manual test steps succeed. No console errors.

---

## File Index

### New Files (35 total)

**Backend (19):**
```
supabase/migrations/006_reputation_hub.sql
backend/app/core/encryption.py
backend/app/models/reviews.py
backend/app/repositories/review_source_repository.py
backend/app/repositories/review_repository.py
backend/app/repositories/review_sentiment_repository.py
backend/app/repositories/review_notification_repository.py
backend/app/clients/reviews/__init__.py
backend/app/clients/reviews/google_business_client.py
backend/app/clients/reviews/yelp_review_client.py
backend/app/clients/reviews/meta_review_client.py
backend/app/services/reviews/__init__.py
backend/app/services/reviews/connection_service.py
backend/app/services/reviews/review_aggregation_service.py
backend/app/services/reviews/review_response_service.py
backend/app/services/reviews/sentiment_service.py
backend/app/services/reviews/analytics_service.py
backend/app/workers/review_tasks.py
backend/scripts/seed_reviews.py
```

**Frontend (16):**
```
frontend/src/app/reputation/layout.tsx
frontend/src/app/reputation/page.tsx
frontend/src/app/reputation/analytics/page.tsx
frontend/src/app/reputation/competitors/page.tsx
frontend/src/app/reputation/connections/page.tsx
frontend/src/app/reputation/settings/page.tsx
frontend/src/components/reputation/ReviewCard.tsx
frontend/src/components/reputation/InboxFilters.tsx
frontend/src/components/reputation/EmptyState.tsx
frontend/src/components/reputation/ReviewDetailPanel.tsx
frontend/src/components/reputation/ConnectionCard.tsx
frontend/src/components/reputation/RatingDistributionChart.tsx
frontend/src/components/reputation/SentimentTrendChart.tsx
frontend/src/components/reputation/ThemeBreakdown.tsx
frontend/src/components/reputation/PlatformComparisonCard.tsx
frontend/src/components/reputation/CompetitorComparisonTable.tsx
frontend/src/components/reputation/NotificationBell.tsx
```

### Modified Files (10)
```
backend/app/core/config.py
backend/app/main.py
backend/app/api/deps.py
backend/app/api/routes/__init__.py
backend/app/repositories/__init__.py
backend/app/services/__init__.py
backend/app/workers/celery_app.py
frontend/src/types/index.ts
frontend/src/lib/api.ts
frontend/src/app/dashboard/page.tsx
```

---

## Task Count Summary

| Sprint | Tasks | Focus |
|--------|-------|-------|
| 1 | 8 | Foundation: DB + skeleton + shell |
| 2 | 8 | Data layer + connections |
| 3 | 10 | Sync pipeline + inbox |
| 4 | 5 | AI responses + detail panel |
| 5 | 7 | Sentiment + analytics |
| 6 | 8 | Competitors + notifications |
| 7 | 6 | Polish + hardening |
| **Total** | **52** | |
