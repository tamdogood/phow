# PHOW — Progress & Plan

**Last updated:** June 16, 2026
**Companion docs:** [`SAAS_STRATEGY.md`](./SAAS_STRATEGY.md) (business model & positioning) · [`FEASIBILITY_STUDY.md`](./FEASIBILITY_STUDY.md) · [`BUSINESS_RADAR.md`](./BUSINESS_RADAR.md) · [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) · [`AUDIT.md`](./AUDIT.md) · [`improvement/SCORECARD.md`](./improvement/SCORECARD.md) + [`improvement/LOOP.md`](./improvement/LOOP.md) (autonomous loop) · [`ROADMAP.md`](./ROADMAP.md) (product vision)

This is the single source-of-truth for where PHOW is and where it's going.

---

## 1. Strategic direction

PHOW serves small business owners who can't afford a market-research agency or a data team. Two complementary jobs, **food & drink first**, with **Google as the real-world data spine**:

1. **Pre-launch research (episodic):** make the existing 9-domain `market_research` engine *best-in-class* by delivering a complete, deterministic, exportable **Feasibility Study** (the "$15k agency study, in minutes"). → Phase 1.
2. **Post-launch monitoring (recurring/daily):** proactively warn owners about anything that could affect them — the **Business Radar**. → Phase 2.
3. **Daily habit + monetization (the SaaS layer):** a **Daily Brief** distills each day's real signals (news + competitor moves + your reputation + input costs) into a pulse + the top 1-3 actions — the retention engine — over a **tiered plan model** (Free/Pro/Multi). → Phase 3.

Positioning: *"Your AI analyst — from 'should I open?' to 'what should I do today?'"* The Brief is the habit layer; the moat is the proprietary signal beneath it. See [`SAAS_STRATEGY.md`](./SAAS_STRATEGY.md) — why the Brief alone isn't the business, and how PHOW beats Podium/Birdeye/Thryv on price + outward intelligence.

---

## 2. Status snapshot

| Capability | Layer | Status | Verified |
|---|---|---|---|
| **Feasibility Study** | Backend (deterministic pipeline, `/api/feasibility/*`, migration 009) | ✅ Built | ✅ Offline synthesis test + import + black |
| Feasibility Study | Frontend (`/report`, `/report/[id]`, `ReportView`, PDF) | ✅ Written | ⏳ Needs `npm run build` on a machine with `src/lib` |
| **Business Radar** | Backend (GDELT→dedupe→LLM-triage pipeline, `/api/radar/*`, migration 010, beat scheduler) | ✅ Built | ✅ Offline pipeline test + import + black |
| Business Radar | Frontend (`/radar`, `RadarWidget`, settings) | ✅ Written (shadcn) | ⏳ Needs `npm run build` |
| **shadcn/ui foundation** | `cn` util + primitives (badge/tabs/skeleton/dialog) + sonner | ✅ Built | ⏳ Needs `npm install` (new deps) |
| **Dark theme design system** | `globals.css` overhaul (unified tokens + surface system + base polish) + rebuilt `AppHeader` | ✅ Built | ✅ CSS structure validated · ⏳ visual check via `npm run build` |
| Per-business Celery scheduler | `dispatch_due_radar_scans` (hourly beat) | ✅ Built | ✅ due-logic unit-checked |
| **Radar daily-signal collectors** | Backend (competitor-move + reputation + Cost Radar; feed the Brief) | ✅ Built | ✅ pure diff/threshold unit tests |
| **Daily Brief** (flagship) | Backend (`/api/daily-brief`, migration 011, morning beat) | ✅ Built | ✅ ranking/pulse/fallback unit tests |
| **Monetization & Entitlements** | Backend (`core/plans.py`, `/api/account/*`, migration 012) | ✅ Built | ✅ plan-logic unit tests |
| **Action Inbox** | Backend (`/api/action-inbox`, migration 013, seeds from Brief) | ✅ Built | ✅ dedupe/row unit tests |

**Backend test suite: 141 passing** (compile + import + black all green; 56 API routes).

**Two standing caveats (both environmental, not code):**
- The frontend can't be built in a fresh workspace: no `node_modules`, and the owner's `frontend/src/lib/{api,session,utils,...}.ts` were gitignored by the Python `lib/` rule (now fixed with `!frontend/src/lib/`, but those files still need to be committed from the owner's machine).
- The live backend pipelines need Redis + real API keys + Supabase; only the deterministic/pure logic is verified here. `@cached` degrades gracefully without Redis.

---

## 3. Phase 1 — Feasibility Study ✅ (shipped)

A guided, deterministic F&B feasibility report with a **GO / GO-WITH-CONDITIONS / NO-GO** verdict, financials, competition, demographics, economic timing, recommendations, cited sources, and one-click PDF. Reuses all existing analysis services + `report_service` (no ad-hoc ReAct agent), so every report is complete and comparable.

**Full detail:** [`FEASIBILITY_STUDY.md`](./FEASIBILITY_STUDY.md).

---

## 4. Phase 2 — Business Radar + shadcn 🟡 (backend done, frontend written)

Per-business AI watchtower: scans news (GDELT) for things that could affect the business, **LLM-triages** each into category · severity · "why it matters to you" · suggested action, and surfaces a prioritized alert feed (dashboard widget + `/radar` page). One radar auto-provisions per business; auto-daily scans via the **new per-business beat scheduler** (the codebase previously had only global cron) + "Scan now". Built on a fresh shadcn/ui foundation.

**Full detail:** [`BUSINESS_RADAR.md`](./BUSINESS_RADAR.md).

**Remaining in Phase 2:**
- Beachhead shadcn migration: `AddCompetitorModal` → `Dialog`; inline errors → toasts.
- Commit `frontend/src/lib/`; `npm install` (new deps: `@radix-ui/react-dialog`, `@radix-ui/react-tabs`, `sonner`); `npm run build` to validate the TSX.

---

## 4b. Phase 3 — Daily Brief + SaaS monetization ✅ (backend shipped, verified)

The layer that turns the tools into a *daily-use SaaS business*. All backend, **141 tests passing**.

- **Daily Brief (flagship daily-habit engine)** — one brief per business per day: ranks the day's Radar signals → 1 LLM pass → **pulse (calm/watch/alert) + narrative + top 1-3 actions**, deterministic fallback so a brief always exists. Morning beat pre-generates it. `/api/daily-brief`, migration 011. *Synthesizes real owned signals, not generic news.*
- **Radar deepened with daily-changing signals** — **competitor-move** collector (Places diff vs `tracked_competitors`: new entrants / closures / rating drops), **reputation** collector (your own Google rating/review drift), and **Cost Radar** (FRED F&B input-cost swings ≥5% MoM — the #1 2026 margin pain), all feeding the Brief. Pure diff/threshold logic unit-tested.
- **Monetization & Entitlements (the SaaS backbone)** — `core/plans.py` (**Free $0 / Pro $59 / Multi $149** + limits + feature flags), `EntitlementService` (`EntitlementError`→HTTP 402), `/api/account/{plans,entitlements,plan}`, migration 012. Cost Radar is gated by the `cost_radar` entitlement (first live tier gate). `PUT /plan` is the Stripe seam.
- **Action Inbox (retention loop)** — the Brief's top actions become checkable tasks (auto-seeded; dedupes vs still-open). `/api/action-inbox`, migration 013.

**Full strategy:** [`SAAS_STRATEGY.md`](./SAAS_STRATEGY.md). **Remaining (gated on owner secrets/decisions):** Stripe billing (keys, behind `PUT /plan`); Review Autopilot *send* + GBP Optimizer (Google Business Profile OAuth); Demand Forecast (events + weather API); frontend surfaces — DailyBriefHero, Action Inbox UI, pricing page (need `npm`). ✅ **Scenario Lab shipped** (`/api/scenario-lab/run`). Still buildable now without secrets: **Review Autopilot draft logic**, **Weekly Business Review**.

---

## 5. Forward plan (Phase 3+)

Ordered by leverage; most reuse the Radar signal-source + LLM-triage framework or the Feasibility pipeline.

**A. Deepen Business Radar (highest near-term value)**
- ✅ **Competitor-move + reputation + Cost Radar collectors** — *shipped* (Places diff vs `tracked_competitors`; own-rating drift; FRED input-cost swings), all feeding the Daily Brief.
- **Local & macro collectors** — wire the already-collected `location_intelligence` (crime/health/trends) into scans (FRED cost signals already done).
- **Digest delivery** — daily/weekly email or Slack summary (needs an email provider: Resend/SendGrid; currently in-app only).
- **Embedding-based relevance/dedup** — reuse `embedding_service` + `match_embeddings` for semantic clustering (provider note: needs an OpenAI key).
- **"Ask about this alert"** → grounded chat (pass alert context into the chat agent).

**B. Deepen Feasibility Study**
- ✅ **What-if Scenario Lab** — *shipped* (`POST /api/scenario-lab/run`): price/rent/food-cost/covers levers → profit/margin/break-even deltas + insights; transparent F&B model, fully unit-tested.
- Multi-site & multi-concept comparison (run the pipeline ×N, rank).
- Stakeholder exports (lender/landlord/investor PDF, business-plan section).
- F&B depth: menu/price benchmarking (`menu_scraper.py`), Google "popular times", cuisine-level saturation; trust/sourcing UI.

**C. Data spine & platform**
- **Google Business Profile connect** (owner-authorized): reviews, search/discovery views, calls — powers Radar reputation signals + a real "your business" dashboard.
- **shadcn full adoption** — migrate high-traffic surfaces (dashboard, chat, business-setup, report) incrementally; standardize on tokens.
- Generalize the per-business scheduler to also drive `search_grid` scheduled runs (its `frequency`/`schedule_hour` are currently unused).

*(See [`ROADMAP.md`](./ROADMAP.md) for the broader tool vision — Review Responder, Social Media Coach, etc.)*

---

## 6. How to run & verify (both features)

```bash
# 1. Database — apply the new migrations
supabase db push   # adds migrations 009-013 (feasibility, radar, daily_briefs, account plan, action_items)

# 2. Backend (needs Redis up for Celery)
cd backend
uvicorn app.main:app --reload --port 8000
celery -A app.workers.celery_app worker --loglevel=info
celery -A app.workers.celery_app beat --loglevel=info   # drives radar auto-scans

# 3. Frontend (on a machine that has frontend/src/lib)
cd frontend
npm install          # picks up @radix-ui/react-dialog, @radix-ui/react-tabs, sonner
npm run build
npm run dev

# 4. Smoke tests
#   Feasibility: POST /api/feasibility/reports {concept,location_address} → poll → /report/[id]
#   Radar:       GET /api/radar/subscription?business_profile_id=ID (auto-creates)
#                POST /api/radar/scan {business_profile_id} → GET /api/radar/feed → /radar?bid=ID
#   Brief:       POST /api/daily-brief/generate {business_profile_id} → GET /api/daily-brief?business_profile_id=ID
#   Account:     GET /api/account/plans · GET /api/account/entitlements?business_profile_id=ID · PUT /api/account/plan {plan:"pro"}
#   Actions:     GET /api/action-inbox?business_profile_id=ID  (auto-seeded by each brief)
```

Backend checks already passing in-repo: `python -c "import app.main"`, `black --check app/`, and the offline pipeline tests for both features.

---

## 7. New files (this work)

**Backend:** `services/{feasibility_service,radar_service}.py`, `repositories/{feasibility_repository,radar_repository}.py`, `models/{feasibility,radar}.py`, `api/routes/{feasibility,radar}.py`, `workers/{feasibility_tasks,radar_tasks}.py`, `supabase/migrations/{009_feasibility_reports,010_business_radar}.sql`. Modified: `main.py`, `api/routes/__init__.py`, `workers/celery_app.py`, `workers/tasks.py` (beat entry).
**Backend (Phase 3):** `core/plans.py`, `services/{daily_brief_service,entitlement_service,action_inbox_service}.py`, `repositories/{daily_brief_repository,action_item_repository}.py`, `models/daily_brief.py`, `api/routes/{daily_brief,account,action_inbox}.py`, `workers/daily_brief_tasks.py`, `supabase/migrations/{011_daily_briefs,012_account_plans,013_action_items}.sql`. Modified: `radar_service.py` (competitor/reputation/cost collectors + entitlement gate), `google_maps.py` (`business_status` field), `main.py` + `routes/__init__.py` + `celery_app.py` + `workers/tasks.py` (registrations + morning beat). Tests: `tests/core/test_plans.py`, `tests/services/{test_daily_brief_service,test_radar_service,test_action_inbox_service}.py`.

**Frontend:** `lib/{utils,feasibility-api,radar-api}.ts`, `components/ui/{badge,tabs,skeleton,dialog}.tsx`, `components/report/ReportView.tsx`, `components/dashboard/RadarWidget.tsx`, `app/report/{page,[id]/page}.tsx`, `app/radar/page.tsx`. Modified: `app/layout.tsx` (Toaster), `app/globals.css` (print), `app/dashboard/page.tsx` (Radar widget), `package.json`, root `.gitignore`. *(Phase 3 frontend — DailyBriefHero, Action Inbox, pricing — still to build.)*
