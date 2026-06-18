# PHOW Feature Scorecard

The objective system the autonomous loop drives ([`LOOP.md`](./LOOP.md) holds the protocol, gates, scoring, and standing prompt). Every feature lists checkable **criteria** — `[x]` pass / `[ ]` open — each tagged with a **type** and an **impact**:

- **type:** `auto` (a command exits 0) · `test` (a committed pytest) · `manual` (reviewable behavior)
- **impact:** `High` · `Med` · `Low`
- **⛔env** = blocked on a secret/service the sandbox can't provide; **excluded from the score denominator** until unblocked.

**App score: ~70%** · **Backend gates** (`LOOP.md`): compile ✅ · import ✅ · black ✅ · pytest ✅ **149 pass** · fe-build ⛔ · fe-lint ⛔
**Score = passed / (total − ⛔env)**, shown as `passed/total`. App score = mean of the section scores. Recompute when you tick a box.

> Line convention: `- [ ] (type, impact) statement — verify: <command/how>`

---

## A. Flagship & daily-use

### 1. Daily Brief — daily-habit engine — 5/5 (100%) · 2 ⛔env
Surface: `services/daily_brief_service.py`, `repositories/daily_brief_repository.py`, `api/routes/daily_brief.py`, `workers/daily_brief_tasks.py`, `models/daily_brief.py`, migration `011`.
- [x] (auto, High) 2 routes registered (`GET /daily-brief`, `POST /daily-brief/generate`) — verify: `python -c "import app.main"` + grep routes
- [x] (auto, High) migration 011 (1 table, unique per business/day) + trigger — verify: `grep -c update_updated_at supabase/migrations/011_*.sql`
- [x] (auto, High) morning beat dispatcher scheduled — verify: `grep dispatch-due-daily-briefs app/workers/tasks.py`
- [x] (test, High) ranking / pulse / stats / top-actions / fallback unit-tested — verify: `pytest tests/services/test_daily_brief_service.py -q`
- [x] (manual, High) synthesizes real owned signals (news + competitor moves + reputation), 1 LLM call + deterministic fallback — verify: review `_synthesize`/`_fallback_brief`
- [ ] (auto, High) ⛔env E2E: `POST /generate` → brief row with pulse + top_actions — verify: curl (Redis+keys+Supabase)
- [ ] (manual, Med) ⛔env `DailyBriefHero` renders on dashboard — verify: `npm run build`
Backlog: frontend hero + `/brief` page · email/Slack delivery (tier hook) · schedule_hour/timezone gating · "Ask about this brief" chat.

### 2. Business Radar — 6/6 (100%) · 2 ⛔env
Surface: `services/radar_service.py`, `repositories/radar_repository.py`, `api/routes/radar.py`, `workers/radar_tasks.py`, migration `010`; `frontend app/radar`, `RadarWidget`, `lib/radar-api.ts`.
- [x] (auto, High) 6 routes registered — verify: `python -c "import app.main"` + grep routes
- [x] (auto, High) migration 010 (3 tables) + trigger — verify: `grep "CREATE TABLE radar_" supabase/migrations/010_*.sql`
- [x] (auto, High) beat dispatcher scheduled — verify: `grep dispatch-due-radar-scans app/workers/tasks.py`
- [x] (test, High) helpers unit-tested: `_build_watch_topics`, `_dedupe`, `_fallback_triage`, `_is_due`, GDELT date parse — verify: `pytest tests/services/test_radar_service.py -q`
- [x] (test, High) competitor-move + reputation signal-diff collectors — verify: `pytest -q -k "TestCompetitorDiff or TestReputationAlert"`
- [x] (test, Med) Cost Radar FRED collector — `_cost_alert` ≥5% MoM, gated by `cost_radar` entitlement — verify: `pytest -q -k TestCostAlert`
- [ ] (auto, High) ⛔env E2E: scan → `/api/radar/feed` returns triaged alerts — verify: curl (Redis+keys)
- [ ] (manual, Med) ⛔env `/radar` + `RadarWidget` render; Scan-now toast + poll — verify: `npm run build`
Backlog: local/macro collectors (crime/health/trends) · email/Slack digest · embedding-based dedup · "Ask about this alert" chat.

### 3. Feasibility Study — 3/4 (75%) · 3 ⛔env
Surface: `services/feasibility_service.py`, `repositories/feasibility_repository.py`, `api/routes/feasibility.py`, `workers/feasibility_tasks.py`, migration `009`; `frontend app/report/*`, `ReportView`, `lib/feasibility-api.ts`.
- [x] (auto, High) 5 routes registered — verify: `python -c "import app.main"` + grep `/feasibility`
- [x] (auto, High) migration 009 + `update_updated_at` trigger — verify: `grep -c update_updated_at supabase/migrations/009_*.sql`
- [x] (manual, High) deterministic pipeline assembles a complete report (verdict + all sections) — verify: offline synthesis run with real services
- [ ] (test, High) synthesis-glue unit test: flat/nested demographics reconciliation, verdict mapping, `_build_sources` — verify: `pytest tests/services/test_feasibility_service.py -q`
- [ ] (auto, High) ⛔env E2E: POST report → poll → `completed` with `verdict.decision` — verify: curl + poll (Redis+keys+Supabase)
- [ ] (manual, Med) ⛔env `/report/[id]` renders all widgets + PDF export — verify: `npm run build` then open
- [ ] (manual, Low) ⛔env "Ask about this report" grounds the chat — verify: open chat from a report, ask a what-if
Backlog: multi-site comparison · stakeholder PDF / business-plan export · confidence/sourcing UI · seed Scenario Lab (§4) from a generated report.

### 4. Scenario Lab — what-if margin/break-even — 3/3 (100%) · 1 ⛔env
Surface: `services/scenario_lab_service.py`, `models/scenario_lab.py`, `api/routes/scenario_lab.py`.
- [x] (auto, High) route registered (`POST /scenario-lab/run`) — verify: `python -c "import app.main"` + grep routes
- [x] (test, High) deterministic model + levers (price/rent/food-cost/covers) + insights unit-tested — verify: `pytest tests/services/test_scenario_lab_service.py -q`
- [x] (manual, High) transparent owner economics (revenue/profit/margin/break-even covers); F&B defaults overridable — verify: review `_model`
- [ ] (manual, Med) ⛔env Scenario Lab UI (sliders → live deltas) — verify: `npm run build`
Backlog: monthly-quota metering (free 3/mo via entitlements) · persist saved scenarios · seed baseline from a feasibility report.

## B. SaaS platform

### 5. Monetization & Entitlements — SaaS backbone — 4/4 (100%) · 1 ⛔env
Surface: `core/plans.py`, `services/entitlement_service.py`, `api/routes/account.py`, migration `012`.
- [x] (auto, High) 3 account routes (`/plans`, `/entitlements`, PUT `/plan`) — verify: `python -c "import app.main"` + grep routes
- [x] (test, High) pure plan logic (resolution, features, limits, unlimited sentinel, entitlements) — verify: `pytest tests/core/test_plans.py -q`
- [x] (auto, High) migration 012 adds `plan` to business_profiles — verify: `grep plan supabase/migrations/012_*.sql`
- [x] (manual, High) entitlement enforced on a real feature (Cost Radar gated; `EntitlementError`→HTTP 402) — verify: review `radar_service._collect_signal_alerts` + `account.set_plan`
- [ ] (manual, High) ⛔env real billing (Stripe checkout + webhook drives `set_plan`) — verify: live (Stripe keys)
Backlog: Stripe integration · usage metering for monthly quotas · per-endpoint `require_capacity` gates · pricing page.

### 6. Action Inbox — insight→done retention — 3/3 (100%) · 1 ⛔env
Surface: `services/action_inbox_service.py`, `repositories/action_item_repository.py`, `api/routes/action_inbox.py`, migration `013`.
- [x] (auto, High) routes registered (list/create/`{id}/{action}`) — verify: `python -c "import app.main"` + grep routes
- [x] (test, High) dedupe-on-seed + row building unit-tested — verify: `pytest tests/services/test_action_inbox_service.py -q`
- [x] (manual, High) Daily Brief auto-seeds open items (best-effort, no dup of open) — verify: review `daily_brief_service.generate` hook
- [ ] (manual, Med) ⛔env inbox UI on dashboard (check/dismiss/add) — verify: `npm run build`
Backlog: due-dates + reminders · snooze · link item back to its source alert/brief.

### 7. Auth / Session — 1/2 (50%) · 1 ⛔env
- [x] (auto, High) `AuthContext` + supabase deps present
- [ ] (auto, High) frontend lib `session.ts`+`supabase.ts` committed (gitignore trap) — verify: `git ls-files frontend/src/lib | grep -E "session|supabase"` (owner machine)
- [ ] (manual, Med) ⛔env sign-in/up + anon session flow — verify: `npm run build`
Backlog: commit lib files (AUDIT #1).

## C. Engine & chat

### 8. Market Research engine (chat) — 2/4 (50%) · 1 ⛔env
Surface: `tools/market_research/*`, `services/{market,economic,competitive,consumer,financial,report}_*.py`.
- [x] (auto, High) tool registered + imports
- [x] (test, High) analysis-service tests pass — verify: `pytest tests/services tests/tools -q`
- [ ] (test, Med) consumer/financial/report services have unit tests — verify: pytest
- [ ] (auto, Low) `except Exception:` blocks log at debug — verify: `grep -rn "except Exception:" app/tools/market_research`
- [ ] (manual, Med) ⛔env widgets render correctly in chat — verify: build + chat a query
Backlog: widget render coverage · surface sources/confidence in chat.

### 9. Operator chat tools (Social / Review / Advisor) — 1/2 (50%) · 1 ⛔env
- [x] (auto, Med) registered + import
- [ ] (test, Med) `agent_tools` unit tests per tool — verify: pytest
- [ ] (manual, Med) ⛔env widgets render — verify: `npm run build`
Backlog: tests · widget polish to design system.

### 10. Chat core (SSE) — 1/2 (50%) · 1 ⛔env
- [x] (auto, High) `/api/chat` SSE endpoint + `chat_service`
- [ ] (test, Med) `chat_service.process_message` orchestration test (tool routing, history, persistence) — verify: pytest
- [ ] (manual, Med) ⛔env streaming renders + widget parsing — verify: `npm run build`
Backlog: orchestration tests.

## D. Supporting surfaces

### 11. Search Grid (local rank) — 2/4 (50%) · 1 ⛔env
- [x] (auto, Med) routes registered
- [x] (manual, Med) reports/runs/results pattern works (dashboard uses it)
- [ ] (auto, Med) scheduled re-runs fire — `frequency`/`schedule_hour` stored but no beat acts on them; generalize the radar dispatcher — verify: a beat task dispatches due grid reports
- [ ] (test, Med) grid-point math + score calc unit test — verify: pytest
- [ ] (manual, Med) ⛔env page renders — verify: `npm run build`
Backlog: wire scheduler · tests.

### 12. Business Profile / Onboarding — 1/2 (50%) · 1 ⛔env
- [x] (auto, Med) routes + repo present
- [ ] (test, Med) profile CRUD + `resolve-maps-url` unit tests — verify: pytest
- [ ] (manual, Med) ⛔env 3-step onboarding completes + saves — verify: `npm run build`
Backlog: tests.

### 13. Dashboard — 1/1 (100%) · 2 ⛔env
- [x] (auto, Med) route + `getDashboard` present
- [ ] (manual, Med) ⛔env renders all widgets incl. Radar + unread badge — verify: `npm run build`
- [ ] (manual, Med) ⛔env profile/community/grid/radar data all load — verify: `npm run build`
Backlog: empty/loading states polish · slot DailyBriefHero + Action Inbox.

### 14. Design System / UI (shadcn) — 2/3 (67%) · 2 ⛔env
Surface: `frontend globals.css`, `components/ui/*`, `lib/utils.ts`, `AppHeader.tsx`.
- [x] (auto, Med) `globals.css` valid + tokens present — verify: brace balance + `grep -- "--phow-surface" globals.css`
- [x] (auto, Med) cn util + primitives present (button/card/input/badge/tabs/skeleton/dialog) — verify: `ls components/ui`
- [ ] (manual, Med) surfaces consistent on tokens; no stray `bg-[#…]`/`bg-slate-*` on primary panels — verify: `grep -rn "bg-\[#" frontend/src | wc -l` trending down
- [ ] (auto, High) ⛔env build passes — verify: `npm run build`
- [ ] (auto, Med) ⛔env lint passes — verify: `npm run lint`
Backlog: beachhead (AddCompetitorModal→Dialog, errors→toasts) · migrate ad-hoc panels to `dark-card`/`widget-card` · mobile nav.

## E. Cross-cutting

### 15. Background data pipeline — 2/2 (100%) · 1 ⛔env
- [x] (auto, Med) Celery tasks + beat schedule defined
- [x] (manual, Med) clients real (crime/health/walkscore/trends/gdelt)
- [ ] (auto, Med) ⛔env collectors run + populate `location_intelligence` — verify: trigger task (keys+Redis)
Backlog: feed `location_intelligence` into radar (local/macro) + feasibility F&B signals.

### 16. Testing & Quality — 1/3 (33%)
- [x] (test, High) pytest harness + **149 tests green** — verify: `pytest -q`
- [ ] (test, High) feasibility service covered (radar ✅ + daily-brief ✅ + scenario-lab ✅ done) — verify: `pytest tests/services/test_feasibility_service.py -q`
- [ ] (test, Low) fix `test_rate_limiter` async-mock "never awaited" warnings — verify: `pytest tests/core/test_rate_limiter.py -W error::RuntimeWarning`
Backlog: `pytest-cov` + coverage floor · CI workflow running the global gates.

### 17. Architecture & Scalability — 1/5 (20%)
From the architecture audit (June 2026). Layering is clean/lean; the open items are scale + DRY.
- [x] (manual, High) clean layered Repo→Service→API, consistent patterns, thin repos — verify: audit verdict
- [ ] (auto, **High**) **DB I/O offloaded off the event loop** — 111 sync `.execute()` in async handlers block the loop — verify: `grep -rn "run_in_threadpool\|to_thread" app/repositories/base.py` (currently 0)
- [ ] (manual, Med) httpx clients not held on singletons reused across Celery event loops — verify: review `*_client.py` `__init__` vs `workers/tasks.py::run_async`
- [ ] (manual, Med) no N+1 in beat dispatchers — verify: review `daily_brief_service.get_due_profile_ids`
- [ ] (manual, Low) shared `core/text.py` / `core/llm_json.py` (no dup `_strip_fences`/`_humanize`/json-parse) — verify: `grep -rln "_strip_fences" app/services` returns 1 module
Backlog: async Supabase client (or threadpool wrapper) · split `competitive_analysis_service.py` (1132 LOC) if it grows · cache periodic re-enable.

---

## How to extend
Add a section in the same format, or add criteria to an existing one (always a `type`, `impact`, and `verify:`). When a feature hits 100%, add 1–3 harder criteria (deeper tests, perf/a11y budgets, edge cases) per `LOOP.md` → "Raising the bar".
