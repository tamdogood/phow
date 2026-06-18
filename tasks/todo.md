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
- [ ] **Review Autopilot** (draft replies; pure draft logic testable; SEND needs GBP OAuth)
- [ ] **Demand Forecast** (events + weather + seasonality) — needs events/weather API
- [ ] **GBP Optimizer**, **Weekly Business Review**, **email/Slack digest** (Resend), **grounded "ask about my business" chat**
- [ ] Frontend: DailyBriefHero, Action Inbox, pricing page, entitlement-aware UI

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
