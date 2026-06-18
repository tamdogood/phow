# PHOW Autonomous Improvement Loop

This is the operating manual for an agent that improves PHOW one focused, verified step at a time. You feed it the **standing prompt** below (e.g. via `/loop`); it reads the [`SCORECARD.md`](./SCORECARD.md), picks the highest-value unchecked criterion, implements it, **proves it with objective checks**, updates the scorecard, and stops for review.

## How one iteration works
1. **Read** `SCORECARD.md`, this file, `docs/AUDIT.md`, and the `CLAUDE.md` files.
2. **Check global gates** (below). A red gate is the task this iteration.
3. **Select** the single highest-value unchecked criterion (see Selection rule).
4. **Implement** it — minimal, root-cause, reuse-first, per CLAUDE.md. One criterion only.
5. **Verify** — run the criterion's `verify:` and *all* global gates; everything must pass.
6. **Update** `SCORECARD.md` (tick box, recompute the feature score) and append a Loop Log entry.
7. **Commit** on a branch with a focused message; **stop** and report diff + new scores.

## Global gates — must stay green every iteration
| Gate | Command | Notes |
|---|---|---|
| G1 compile | `cd backend && python -m compileall -q app` | no output = pass |
| G2 import | `cd backend && python -c "import app.main"` | app boots |
| G3 format | `cd backend && black --check app` | run `black app` to fix |
| G4 tests | `cd backend && python -m pytest -q` | 91+ pass, 0 fail |
| G5 fe-build | `cd frontend && npm run build` | ⛔env: needs `node_modules` + the gitignored `src/lib` |
| G6 fe-lint | `cd frontend && npm run lint` | ⛔env (same) |

A criterion is **done** only when its `verify:` passes *and* no gate regressed.

## Scoring
- Criterion tags: **[auto]** a command exits 0 · **[test]** a committed pytest exists+passes · **[manual]** reviewable behavior · **⛔env** blocked on a secret/service the agent can't provide (excluded from the denominator until unblocked).
- **Feature score = passed / (total − blocked) × 100**, shown as `passed/total`.
- **App score = mean of feature scores.** The loop's objective is to raise it without regressing gates.

## Selection rule (what to do next)
1. Any **red global gate** → fix first.
2. Else the highest-value unchecked criterion, ordered by: **impact (High→Low)** → **[auto]/[test] before [manual]** → **lowest-scoring feature** → **top of that feature's Backlog**.
3. Skip **⛔env** criteria unless you can satisfy them with a mock/stub/fixture (preferred — e.g. unit-test a pipeline with the LLM/HTTP mocked).
4. Never start a second criterion in one iteration.

## Guardrails
- Never let a global gate regress. If you can't keep them green, revert and pick something else.
- Follow CLAUDE.md (succinct, DRY, minimal diffs, Black). Add a test when you add logic.
- If a criterion needs a product decision or a secret only the owner has, **stop and ask** — don't guess.
- Keep changes scoped to the chosen criterion; note incidental findings in the Backlog instead of fixing them.

## Raising the bar
When a feature hits 100%, add 1–3 harder criteria (deeper tests, perf budget, a11y, edge cases) so the bar keeps rising. Record new criteria with a tag + `verify:`.

---

## ⭐ Standing prompt (paste this each iteration / use with `/loop`)

```
You are the PHOW Autonomous Improvement Agent. Run exactly ONE focused iteration.

1. Read docs/improvement/SCORECARD.md, docs/improvement/LOOP.md, docs/AUDIT.md, and the CLAUDE.md files.
2. Run the GLOBAL GATES. If any gate is RED, fixing it is this iteration's task.
3. Otherwise pick the SINGLE highest-value unchecked criterion using LOOP.md's Selection rule
   (impact → [auto]/[test] over [manual] → lowest-scoring feature → top of Backlog).
   Prefer criteria you can fully verify here; for ⛔env criteria, satisfy them with mocks/fixtures.
4. Implement it fully and minimally per CLAUDE.md. Do ONE criterion only. Add a test if you add logic.
5. Verify: run the criterion's `verify:` AND all global gates — everything must pass, nothing may regress.
6. Update SCORECARD.md (tick the box, recompute the feature score + app score) and append a dated
   entry to the Loop Log (criterion, what changed, verify result).
7. Commit on a branch with a focused message. STOP and report: the diff summary, the criterion closed,
   and the new scores.

Rules: never regress a global gate; never start a second criterion; if it needs a decision or a secret
only I can provide, STOP and ask instead of guessing.
```

## Loop Log
Append newest first: `YYYY-MM-DD — <feature> · <criterion id> — <what changed> — <verify result>`

- 2026-06 — SaaS iter 2 · **Scenario Lab** — deterministic what-if calculator (`scenario_lab_service` + model + `POST /api/scenario-lab/run`): price/rent/food-cost/covers levers → revenue/profit/margin/break-even deltas + insights; F&B defaults overridable. +8 tests (`test_scenario_lab_service`). Verify: black ✅, import ✅ (57 routes), `pytest -q` → **149 passed**. Directly targets the #1 2026 pain (margin squeeze). App score ~65→~67%.
- 2026-06 — SaaS iter 1 · **Monetization + Action Inbox + Cost Radar** — `core/plans.py` (Free/Pro/Multi tiers) + `entitlement_service` (EntitlementError→402) + `/api/account/*` + migration 012; Action Inbox (migration 013, auto-seeds from Daily Brief) ; Cost Radar FRED collector gated by `cost_radar` entitlement. +19 tests (`test_plans` 9, `test_action_inbox_service` 5, radar `TestCostAlert` 5). Verify: black ✅, import ✅ (56 routes), `pytest -q` → **141 passed**. App score ~59→~65%.
- 2026-06 — feature build · **Daily Brief (flagship)** + Radar signal collectors — new `daily_brief` service/repo/route/worker/migration 011 + morning beat; Radar gains competitor-move + reputation signal diffs (Places). Added `test_daily_brief_service.py` (12) + `test_radar_service.py` (19). Verify: black ✅, `import app.main` ✅ (50 routes, daily-brief live), `pytest -q` → **122 passed**. Scored Daily Brief 5/5, Radar 5/7. See [`../SAAS_STRATEGY.md`](../SAAS_STRATEGY.md).
- 2026-06 — iter 1 · Gates/G3 black — ran `black app/` (26 files reformatted); verify: `black --check app` → 117 clean, `pytest -q` → 91 passed, compile+import OK. Gate G3 RED→GREEN, no regressions.
- 2026-06 — system created (audit + scorecard seeded from `docs/AUDIT.md`).
