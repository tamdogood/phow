# PHOW Logic Audit

**Date:** June 2026 · **Scope:** backend (fully runnable here) + static frontend review.
**Method:** `compileall`, `import app.main`, `black --check`, `pytest`, migration↔code table diff, router/worker wiring, stub/secret/except scans.

## Verdict
**Backend logic is sound and tested.** Everything compiles, the app imports, **91/91 tests pass**, all 8 routers and 4 Celery workers are wired, and every table referenced in code has a migration. The frontend is coherent by inspection but **cannot be built/verified in this workspace** (no `node_modules`; 4 lib files are gitignored). Top risks: untracked frontend lib files, no tests on the two new features, and formatting drift.

## What passed ✅
| Check | Result |
|---|---|
| `python -m compileall app` | clean (no syntax errors) |
| `python -c "import app.main"` | OK — 42 API routes |
| `pytest -q` | **91 passed**, 26 warnings, 3.4s |
| Routers registered | 8/8 (chat, tools, business_profile, dashboard, community, search_grid, feasibility, radar) |
| Celery worker modules included | 4/4 (tasks, search_grid_tasks, feasibility_tasks, radar_tasks) + beat entry for radar dispatcher |
| Migrations ↔ code tables | every `.table("…")` in code has a `CREATE TABLE` (22 tables) |
| Stubs / TODO / NotImplemented | none in `backend/app` |
| Key deps in `requirements.txt` | fastapi, celery, redis, supabase, langchain(+openai/anthropic), httpx, tenacity, geohash, pytrends, sse-starlette ✓ |

## Findings (by severity)
| # | Sev | Finding | Fix |
|---|---|---|---|
| 1 | **High** | `frontend/src/lib/{api,session,supabase,google-maps}.ts` are **gitignored** (Python `lib/` rule) → not version-controlled, absent from fresh clones; frontend can't build without them. (`utils,feasibility-api,radar-api` were added tracked.) | Commit them from the owner's machine (the `!frontend/src/lib/` un-ignore is already in `.gitignore`). |
| 2 | Med | **No automated tests** for the two new features (FeasibilityService, RadarService). They're verified only by throwaway offline scripts. | Add `tests/services/test_feasibility_service.py` + `test_radar_service.py` (pure-logic: glue, dedupe, triage fallback, verdict). |
| 3 | Med | **`black --check` fails on 26 files** (pre-existing drift; CLAUDE.md mandates Black). | `black app/` and keep it a CI/loop gate. |
| 4 | Med | Frontend has **no build/lint verification** available here (no `node_modules`). | After #1, `npm install && npm run build && npm run lint` on the owner's machine; make it a loop gate. |
| 5 | Low | `tests/core/test_rate_limiter.py` emits "coroutine never awaited" RuntimeWarnings (mock not awaited). | Fix the async mock in the test. |
| 6 | Low | Several `except Exception:` swallow errors silently in `market_research/*_tools.py`. | Log at debug in the except blocks. |
| 7 | Info | **Functional gaps by design (MVP):** email/push delivery not implemented; radar competitor-move + local/macro collectors deferred; embedding-based dedup not wired; `search_grid` `frequency`/`schedule_hour` still not acted on (only the new radar dispatcher schedules). | Tracked in `improvement/SCORECARD.md` backlog. |
| 8 | Info | Tables `business_history`, `llm_responses`, `tool_activities` exist but are lightly/never used by current code paths. | Wire LLM/tool tracking, or drop if unused. |

## Not verifiable here (need the owner's env)
- Live pipelines (feasibility, radar, collectors) — need Redis + Google/Census/FRED/Yelp keys + Supabase with migrations applied. `@cached` degrades gracefully without Redis.
- Frontend rendering/build — needs `node_modules` + the gitignored lib files.

These map 1:1 to gates/criteria in [`improvement/SCORECARD.md`](./improvement/SCORECARD.md); the autonomous loop is defined in [`improvement/LOOP.md`](./improvement/LOOP.md).
