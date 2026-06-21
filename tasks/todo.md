# PHOW Phase 3 — Toward a SaaS business (iterative build)

Goal: implement the prioritized feature plan + the monetization layer that makes PHOW a *business*, keeping all global gates green every step. Strategy in `docs/SAAS_STRATEGY.md`; feature backlog from the brainstorm.

## Iteration 1 (this batch) — monetization + margin + actionability ✅ verified
- [x] **Plans & Entitlements** (the missing SaaS backbone): `core/plans.py` (Free/Pro/Multi + limits + features), `services/entitlement_service.py` (EntitlementError→402), `api/routes/account.py` (`/plans`, `/entitlements`, PUT `/plan`), migration `012` (`plan` on business_profiles), `tests/core/test_plans.py` (9)
- [x] **Action Inbox** (insight→done, retention): migration `013_action_items.sql`, repo/service/route, auto-seeds from Daily Brief `top_actions` (dedupe vs open), `test_action_inbox_service.py` (5)
- [x] **Margin Defender — Cost Radar** (#1 2026 pain): FRED F&B commodity collector in `radar_service` → supply alerts on ≥5% MoM moves; **gated by `cost_radar` entitlement**; pure `_cost_alert` + tests (5); feeds the Brief
- [x] Verify: black ✅ · `import app.main` ✅ (56 routes) · `pytest` ✅ **141 passed** (was 122)
- [x] Update SCORECARD + Loop Log + memory

**Review (iter 1):** shipped the monetization layer (tiers/limits/entitlements + `/api/account/*`, EntitlementError→HTTP 402) — the piece that was missing for this to be a *business*; the Action Inbox that turns the Brief's advice into checkable tasks (retention loop); and Cost Radar (Margin Defender) wired through the new entitlement gate. +19 tests, all gates green. **Not verifiable here:** live FRED/Supabase, frontend. **Next:** Scenario Lab (offline-testable), Review Autopilot draft logic, then the frontend surfaces (DailyBriefHero, Action Inbox, pricing page) + billing (Stripe) behind the PUT `/plan` seam.

## Iteration 2+ — buildable now (no secrets) + items needing external creds
- [x] **Scenario Lab** ✅ (SaaS iter 2) — `scenario_lab_service` + `POST /api/scenario-lab/run`; transparent what-if (price/rent/food-cost/covers → profit/margin/break-even); 8 tests; suite **149 green**
- [x] **Review Autopilot → Reputation Hub (GBP)** — shipped this iteration (see Iteration 3 below)
- [ ] **Demand Forecast** (events + weather + seasonality) — needs events/weather API
- [ ] **GBP Optimizer**, **Weekly Business Review**, **email/Slack digest** (Resend), **grounded "ask about my business" chat**
- [ ] Frontend: DailyBriefHero, Action Inbox, pricing page, entitlement-aware UI

## Iteration 3 — Reputation Hub on Google Business Profile ✅ (backend verified)

The "Protect your reputation" Hub: connect Google Business Profile via OAuth, auto-sync reviews,
unified inbox, AI reply drafts (3 tones), publish replies to Google, sentiment + analytics.
A manual "Add review" path makes it usable before Google API access is approved.

- [x] Migration `014_reputation_hub.sql` — `review_connections` + `reviews` (sentiment & response folded in; 2 tables)
- [x] `core/crypto.py` (Fernet) + config (GBP OAuth, encryption key, `frontend_url`) + `cryptography` dep + `.env.example`
- [x] `clients/google_business_client.py` — OAuth + Accounts/Locations/Reviews(v4)/Reply + review normalization
- [x] `repositories/review_repository.py` + `services/reputation_service.py` (reuses keyword sentiment classifier; LLM for drafts)
- [x] `api/routes/reviews.py` (10 routes) + `deps` + `main` + `routes/__init__`
- [x] `workers/reputation_tasks.py` `sync_all_reviews` + 15-min beat + celery include
- [x] Frontend: `lib/reviews-api.ts`, `app/reviews/page.tsx`, dashboard `ReputationWidget`, AppHeader "Reputation" nav
- [x] `tests/services/test_reputation_service.py` (10): normalize, draft-parse, sentiment, analytics, OAuth url
- [x] Verify: black ✅ (154 files) · `import app.main` ✅ (67 routes, 10 review) · pytest ✅ **159 passed**

**Review (iter 3):** Shipped the Google-first Reputation Hub end to end on the backend — the item previously flagged as "Review Autopilot — SEND needs GBP OAuth." Kept minimal per house style: 2 tables (sentiment + owner response folded into `reviews`), reused the existing keyword sentiment classifier, Fernet-encrypted tokens at rest. **Verified here:** backend import, formatting, 159 tests (incl. 10 new offline tests). **Not verifiable here:** live Google OAuth/sync/publish (needs Google API allowlisting + `business.manage` verification + creds), Supabase `014` apply, and the frontend build (no node_modules; gitignored `src/lib`). **To ship:** apply `014`; set `GOOGLE_OAUTH_*` + `REVIEW_TOKEN_ENCRYPTION_KEY` + `FRONTEND_URL`; request Google Business Profile API access; `npm install && npm run build`; commit `frontend/src/lib/reviews-api.ts`. **Pre-approval:** the manual "Add review" path exercises sentiment→draft→publish locally. **Next:** Yelp read-lite + deep-link reply; multi-location; daily digest email; surface Hub "needs reply" in the Daily Brief / Action Inbox.

---

# PHOW Phase 2 — Business Radar + shadcn

Plan: `~/.claude/plans/...` · Docs: `docs/BUSINESS_RADAR.md`, `docs/FEASIBILITY_STUDY.md`

## Backend — Business Radar (DONE, verified)
- [x] Migration `010_business_radar.sql` (subscriptions + scans + alerts)
- [x] `repositories/radar_repository.py`
- [x] `models/radar.py`
- [x] `services/radar_service.py` (get_or_create_for_profile + run_scan: GDELT collect → URL/title dedupe → LLM triage w/ fallback → persist)
- [x] `workers/radar_tasks.py` (run_radar_scan + dispatch_due_radar_scans beat — the new per-entity scheduler)
- [x] `api/routes/radar.py` + registered (main.py / routes/__init__.py / celery_app.py include + tasks.py beat entry)
- [x] Offline pipeline test (watch-topics, dedupe, date parse, triage fallback, due logic) — passed
- [x] black --check + `import app.main` (6 radar routes registered)

## shadcn foundation (DONE)
- [x] `lib/utils.ts` (cn)
- [x] primitives `components/ui/`: badge, tabs, skeleton, dialog (Radix + cva, new-york)
- [x] sonner `<Toaster/>` in `app/layout.tsx` + deps in package.json (radix dialog/tabs, sonner)
- [x] existing `.dark` shadcn tokens reused (no rip-out of dark-card/widget-card)
- [ ] beachhead migration: AddCompetitorModal → Dialog; inline errors → toasts (REMAINING)

## Frontend — Radar (DONE, on shadcn; not buildable here)
- [x] `lib/radar-api.ts` (client + types + helpers)
- [x] `components/dashboard/RadarWidget.tsx` + slotted into dashboard
- [x] `app/radar/page.tsx` (Tabs feed + Scan now + settings Dialog; Suspense-wrapped)

## Docs (DONE — per request)
- [x] `docs/FEASIBILITY_STUDY.md`, `docs/BUSINESS_RADAR.md`

## Review
**Built:** the full Business Radar backend (deterministic GDELT→dedupe→LLM-triage→alerts pipeline + the per-business beat scheduler the codebase lacked), exposed at `/api/radar/*`; the shadcn foundation (cn util, 4 primitives, sonner) and a Radar UI fully built on shadcn (dashboard widget + `/radar` page); both features documented in `docs/`.

**Verified here:** backend imports + black; radar deterministic pipeline (watch-topics, dedupe, date parse, triage fallback, scheduling) via offline test. **Not verifiable here:** live pipeline (Redis broker + GDELT/LLM/Supabase) and the frontend build (no node_modules; gitignored `src/lib`).

**To ship:** apply `010_business_radar.sql`; run backend + `celery worker` + `celery beat` (Redis up); `cd frontend && npm install && npm run build` on a machine with `src/lib`; smoke-test `/radar` (Scan now → triaged alerts). Commit `frontend/src/lib/` (now un-ignored).

**Next:** beachhead shadcn migration; competitor-move + local/macro collectors; email digest; embedding-based dedup; "Ask about this alert" chat.
