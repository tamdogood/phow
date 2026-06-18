# Business Radar (Phase 2)

**Status:** Backend complete & verified offline · Frontend + shadcn foundation **built** (needs `npm install && npm run build` on a machine with `src/lib`) · Beachhead migration (AddCompetitorModal→Dialog, errors→toasts) = remaining
**Added:** 2026-06 · Approved plan: `~/.claude/plans/` ("PHOW Phase 2 — Business Radar + shadcn/ui Foundation")

## What it is
An AI "watchtower" per business: it continuously scans the news for things that could **hurt or help** the owner's business, triages each item with an LLM, and surfaces a prioritized, plain-language alert feed — each alert tagged with **category**, **severity**, a one-line **"why it matters to YOU"**, and a **suggested action**. This is PHOW's recurring, daily-use, retention feature and the answer to "update the owner on anything happening that could be a concern."

It also activates infrastructure that was previously built but unused (GDELT client, embeddings, the Celery pipeline).

## Architecture (mirrors the proven `search_grid` 3-tier pattern)
```
radar_subscriptions (1 per business, auto-provisioned)
        │  watch_topics built from business_type + city/state + competitors + name
        ▼
dispatch_due_radar_scans  (NEW hourly beat task — the per-entity scheduler the codebase lacked)
        │  finds active subs whose last_scanned_at is due (daily/weekly)
        ▼
run_radar_scan(subscription_id)  →  RadarService.run_scan:
        1. collect candidates  (GDELT news for the watch topics)
        2. dedupe by URL/title (+ skip URLs already alerted in last 30d)
        3. LLM triage → relevant? category · severity · relevance_score · summary · why_it_matters · suggested_action
        4. persist radar_alerts (filtered by enabled categories), update scan + last_scanned_at
        ▼
GET /api/radar/feed  ◄── dashboard widget + /radar page render the alert feed
```
Best-effort throughout (a failed collector/LLM degrades gracefully — the triage has a deterministic fallback so the feed still populates). One LLM call per scan (batched triage).

### Why GDELT-first
The backend can't use external web search; it ships the free **GDELT** global news client (`search_industry_news`, keyword-based). Watch topics fold in industry + location + supply/regulation terms + competitor names + the business name, so competitor and reputation news surface through the same news pipeline. **Note:** Places-based competitor-move *diffing* (new entrants/closures) needs baseline snapshots to avoid noise, so it's a documented next collector rather than part of the MVP.

## Data model — `supabase/migrations/010_business_radar.sql`
- `radar_subscriptions` — one per `business_profile_id` (UNIQUE): `watch_topics[]`, `categories[]`, `frequency`, `schedule_hour`, `timezone`, `status`, `last_scanned_at`.
- `radar_scans` — per-run: `status`, `candidates_found`, `alerts_created`, `error`, timings.
- `radar_alerts` — `title`, `url`, `source`, `source_domain`, `published_at`, `category` (competition/regulation/supply/demand/macro/local/reputation), `severity` (info/watch/urgent), `relevance_score`, `summary`, `why_it_matters`, `suggested_action`, `status` (new/read/dismissed), `raw` JSONB.

## Backend files (built + verified)
- `services/radar_service.py` — orchestrator: `get_or_create_for_profile`, `update_subscription`, `get_feed`, `mark_alert`, `trigger_scan`, `get_due_subscription_ids`, `run_scan` (+ `_collect_gdelt`, `_triage`/`_fallback_triage`, `_build_watch_topics`, dedupe/date helpers).
- `repositories/radar_repository.py` — CRUD for the 3 tables (+ `recent_alert_urls`, `count_unread`).
- `models/radar.py` — request models.
- `api/routes/radar.py` — endpoints (below).
- `workers/radar_tasks.py` — `run_radar_scan` + `dispatch_due_radar_scans` (beat).
- Modified: `main.py`, `api/routes/__init__.py`, `workers/celery_app.py` (include `radar_tasks`), `workers/tasks.py` (beat entry `dispatch-due-radar-scans`, hourly).
- Reused: `gdelt_client.py`, `business_profile_repository.py` (+ `TrackedCompetitorRepository`), `core/llm.py`, `workers/tasks.py::run_async`.

## API
- `GET  /api/radar/feed?business_profile_id=&status=&limit=&offset=` → `{subscription, alerts[], unread_count, latest_scan}`.
- `GET  /api/radar/subscription?business_profile_id=` → get-or-create (auto-provisions one per profile).
- `PUT  /api/radar/subscription` → `{business_profile_id, watch_topics?, categories?, frequency?, schedule_hour?, status?}`.
- `POST /api/radar/scan` → `{business_profile_id}` (trigger now).
- `POST /api/radar/alerts/{id}/read` · `POST /api/radar/alerts/{id}/dismiss`.

## Frontend (built, on shadcn)
**shadcn foundation:** `lib/utils.ts` (`cn`); new primitives under `components/ui/` — `badge.tsx`, `tabs.tsx`, `skeleton.tsx`, `dialog.tsx` (Radix + cva, new-york style); `sonner` `<Toaster/>` mounted in `app/layout.tsx`; deps added to `package.json` (`@radix-ui/react-dialog`, `@radix-ui/react-tabs`, `sonner`). The existing `.dark` shadcn CSS tokens in `globals.css` are sufficient for on-theme rendering, so `dark-card`/`widget-card` were left for domain widgets.
**Radar UI:** `lib/radar-api.ts` (client + types + `severityStyle`/`relativeTime` helpers); `components/dashboard/RadarWidget.tsx` (top-5 alerts + unread badge, slotted into `app/dashboard/page.tsx` after `CommunityWidget`); `app/radar/page.tsx` (shadcn `Tabs` by category/urgency, alert cards with severity `Badge` + why_it_matters + suggested_action + read/dismiss, "Scan now" `Button` with sonner toast + poll, settings `Dialog` for topics/categories/frequency; wrapped in `<Suspense>` for `useSearchParams`).
**Remaining:** beachhead migration — `AddCompetitorModal` → shadcn `Dialog`; convert inline error states to toasts. Domain widgets (`ReportView`, tool widgets, landing) intentionally left as-is.

> Frontend not buildable in this workspace (no `node_modules`; the user's `src/lib/{api,session,...}.ts` are gitignored/untracked). Written to match verified component contracts + the codebase's working patterns; verify with `npm install && npm run build` on the user's machine.

## Run & verify
1. Apply `010_business_radar.sql`.
2. `cd backend && uvicorn app.main:app --reload --port 8000` + `celery -A app.workers.celery_app worker` + `celery -A app.workers.celery_app beat` (Redis up).
3. `GET /api/radar/subscription?business_profile_id=<id>` (auto-creates), then `POST /api/radar/scan {business_profile_id}`; poll `GET /api/radar/feed?business_profile_id=<id>` for triaged alerts (category/severity/why_it_matters/suggested_action). Re-run → dedup keeps it stable.
4. Confirm `dispatch_due_radar_scans` dispatches due subscriptions (beat running).

**Verified offline:** watch-topic generation, URL/title dedupe (incl. already-seen), GDELT date parsing, triage fallback shape, due/scheduling logic, backend import + `black`. **External bits** (GDELT fetch, LLM triage, Supabase) follow the same patterns as the rest of the app; `@cached` degrades gracefully without Redis.

## Next additions (roadmap)
- **Competitor-move collector** (Places diff vs `tracked_competitors` with stored baseline → new entrants / closures / rating drops).
- **Local/macro collectors**: reuse `location_intelligence` (crime/health/trends) + FRED via `economic_service`.
- **Email/push digest** (needs a provider — Resend/SendGrid; currently in-app only).
- Embedding-based semantic dedup/relevance (reuse `embedding_service` + `match_embeddings`).
- "Ask about this alert" → grounded chat; daily/weekly digest summary.
