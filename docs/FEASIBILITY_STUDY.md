# Feasibility Study (Phase 1)

**Status:** Backend complete & verified offline · Frontend written (needs `npm run build` on a machine with `src/lib`)
**Added:** 2026-06 · Plan of record for the broader direction: `~/.claude/plans/` (see ROADMAP.md)

## What it is
PHOW's flagship pre-launch artifact: a guided, **deterministic**, comprehensive, exportable **food & drink feasibility study**. The owner gives 3 inputs (concept, location, optional scale/budget) and gets an agency-grade **GO / GO-WITH-CONDITIONS / NO-GO** report in minutes — demographics, market sizing (TAM/SAM/SOM), competition + positioning, consumer insights, economic timing, financial projection/break-even, an executive summary, recommendations, and cited sources.

It reuses the existing 9-domain `market_research` analysis services but, unlike the ad-hoc chat agent, runs a **fixed pipeline** so every report is complete and comparable.

## Why deterministic (not the ReAct agent)
The `market_research` LangGraph agent decides on a whim which of its 44 tools to call, so its output is incomplete/ephemeral. `FeasibilityService` calls the analysis services in a fixed order, assembles the exact `analysis_results` dict that `report_service.aggregate_report_data()` already consumes, and reuses `report_service` for the executive summary + verdict + recommendations. The chat agent remains for follow-up "what-if" Q&A.

## Architecture
```
POST /api/feasibility/reports ──► row (pending) ──► Celery run_feasibility_report
                                                          │
   FeasibilityService.run_pipeline (deterministic):       ▼
   A. NAICS + discover_neighborhood + demographics (build flat & nested demo)
   B. parallel: viability · competitors · positioning · economic · growth · F&B signals
   C. competitor reviews (top-5 place details) → sentiment / pain points / persona
   D. market sizing (TAM/SAM/SOM)
   E. build flat market_data bundle
   F. seasonality · SWOT · five forces · pricing · market share · financial summary
   G. entry timing
   H. synthesis via report_service (exec summary + verdict + recommendations)
   I. assemble FeasibilityReport JSONB + sources[]; persist (completed)
GET /api/feasibility/reports/{id}  ◄── frontend polls until completed, then renders
```
Every leg is best-effort (`try/except` → section marked unavailable, never aborts). Only **2 LLM calls** per report (exec summary + recommendations), both with deterministic fallbacks.

**Key correctness detail:** Census returns *nested* demographics (`income.median_household`) while SWOT/financial/consumer read *flat* (`median_income`). The pipeline builds both `flat_demo` and `nested_demo` once and feeds the right shape to each service.

## Data model — `supabase/migrations/009_feasibility_reports.sql`
Single JSONB-row table `feasibility_reports`: inputs (`concept`, `location_address`, `scale_seats`, `startup_budget`, `naics_code`), job lifecycle (`status`, `progress`, `error`), denormalized headline (`verdict`, `viability_score`, `title`), the full `report` JSONB, keyed by `session_id` (+ optional `user_id`, `business_profile_id`).

## Files
**Backend (new):** `services/feasibility_service.py` (orchestrator), `repositories/feasibility_repository.py`, `models/feasibility.py`, `api/routes/feasibility.py`, `workers/feasibility_tasks.py`, `supabase/migrations/009_feasibility_reports.sql`.
**Backend (modified):** `main.py`, `api/routes/__init__.py`, `workers/celery_app.py` (register router + task).
**Frontend (new):** `lib/feasibility-api.ts` (client + types), `app/report/page.tsx` (intake), `app/report/[id]/page.tsx` (poll + render), `components/report/ReportView.tsx`.
**Frontend (modified):** `app/globals.css` (print/PDF styles), `.gitignore` (`!frontend/src/lib/` — the Python `lib/` rule was hiding the frontend lib dir).
**Reused unchanged:** all `*_analysis_service.py`, `report_service.py`, `widget_extractor.py`, the agent tools, `MarketValidatorWidget`.

## API
- `POST /api/feasibility/reports` — `{session_id, concept, location_address, scale_seats?, startup_budget?, user_id?, business_profile_id?}` → creates row + dispatches job.
- `GET /api/feasibility/reports/{id}` — poll status + report.
- `GET /api/feasibility/reports?session_id=&user_id=` — list summaries.
- `POST /api/feasibility/reports/{id}/rerun` · `DELETE /api/feasibility/reports/{id}`.

## Run & verify
1. Apply `009_feasibility_reports.sql`.
2. `cd backend && uvicorn app.main:app --reload --port 8000` + `celery -A app.workers.celery_app worker` (Redis up).
3. `POST /api/feasibility/reports` with `{concept:"specialty coffee shop", location_address:"500 W 2nd St, Austin, TX", scale_seats:30, startup_budget:250000}`; poll `GET .../{id}` until `completed`.
4. Frontend: `npm run build` (needs `src/lib`), open `/report`, submit, watch the stepper, view the report, "Download PDF".

**Verified:** backend imports + `black`; the full synthesis/data-glue path with the real services offline (verdict GO, all 6 sections, sources). **Not verifiable in a fresh workspace:** the live network pipeline (needs Redis + API keys + Supabase) and the frontend build (no `node_modules`; needs the gitignored `src/lib`).

## Next steps (roadmap)
- Trust/sourcing UI polish + confidence chips.
- F&B depth: menu/price benchmarking (`menu_scraper.py`), Google "popular times", cuisine-level saturation.
- **What-if Scenario Lab** on a generated report (`run_financial_scenario`).
- Multi-site / multi-concept comparison; stakeholder PDF/business-plan export.
- "Ask about this report" → grounded chat.
