# PHOW Operations Hub Sprint Backlog

## Summary
This backlog decomposes the Operations Hub into 8 demoable sprints with atomic, commit-sized tickets.
Each ticket includes required validation (automated test preferred; otherwise explicit verification artifact).
This version incorporates a real subagent review and folds in its improvements: early authz/contracts, earlier OAuth risk spike, pipeline reliability tickets, adapter conformance testing, and continuous quality gates (not deferred to final sprint).

## Subagent Review
### Prompt sent to subagent
```text
You are a staff engineer acting as a review subagent. Review this sprint backlog for PHOW Operations Hub and return only: (1) gaps, (2) sequencing risks, (3) missing test coverage, (4) concrete ticket improvements. Keep it concise and technical. BACKLOG SUMMARY: 8 sprints to deliver standalone /ops feature: Sprint1 foundations(schema+api skeleton+frontend shell+feature flags+bootstrap), Sprint2 onboarding wizard and setup tasks, Sprint3 location management and all-locations overview+metrics customization, Sprint4 local-search-grid builder with map criteria keywords scheduling email config and preview, Sprint5 report run pipeline and results heatmap, Sprint6 connections and review-generation entry with staged connectors, Sprint7 live integration adapters behind flags and OAuth, Sprint8 hardening/performance/accessibility/e2e/regression+release readiness. Each ticket is atomic with tests/validation and each sprint demoable.
```

### Improvements applied from subagent feedback
1. Added Sprint 1 tickets for tenancy/authz policy and OpenAPI contract harness.
2. Pulled forward OAuth/provider risk to Sprint 3 as a spike behind flags.
3. Added email readiness ticket before scheduling-dependent rollout.
4. Added reliability layer tickets (idempotency/retries/DLQ/replay) in Sprint 5.
5. Added adapter conformance suite in Sprint 6.
6. Converted perf/a11y/e2e into every-sprint DoD; Sprint 8 is now release cutover/regression sign-off.

## Public Interfaces Added
1. New route family under `/api/ops/*`.
2. New frontend route family under `/ops/*`.
3. New TS domain module `frontend/src/types/ops.ts`.
4. New frontend API client module `frontend/src/lib/ops-api.ts`.
5. New DB tables for onboarding, ops locations, local grid reports, report runs, run cells/rankings, metric preferences, and connections state.

## Program-Level DoD (applies to every sprint)
1. All new backend code has `pytest` coverage for success + failure path.
2. All new frontend components have unit tests (`Vitest` + RTL) where logic exists.
3. Each sprint ships at least one deterministic end-to-end path (`Playwright`) for demo.
4. OpenAPI contract snapshot is updated and contract tests pass.
5. RBAC/ownership tests pass for any new endpoint.
6. Accessibility checks run on new pages (`axe` in e2e).
7. Performance smoke check added for new heavy UI/data surfaces.

---

## Sprint 1: Platform Foundations and Contract Baseline
**Sprint goal:** runnable `/ops` shell, schema baseline, secure bootstrap endpoint, and testing scaffolding.
**Demo slice:** user can load `/ops`, call `/api/ops/bootstrap`, and see seeded placeholder state.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S1-001 | Create migration `supabase/migrations/006_operations_hub.sql` with minimal tables: `ops_onboarding`, `ops_setup_tasks`, `ops_locations`, `local_grid_reports`, `local_grid_report_runs`, `location_metric_preferences`, `platform_connections` | Migration up/down in local DB; `backend/tests/migrations/test_006_operations_hub.py` |
| OPS-S1-002 | Add `backend/app/models/ops.py` Pydantic models for bootstrap/onboarding/location/report summary DTOs | `pytest backend/tests/models/test_ops_models.py` |
| OPS-S1-003 | Add repositories: onboarding + setup task + location + report summary read model | `pytest backend/tests/repositories/test_ops_repositories.py` |
| OPS-S1-004 | Add `OpsService.bootstrap()` including legacy profile-to-ops seed logic | `pytest backend/tests/services/test_ops_service_bootstrap.py` |
| OPS-S1-005 | Add `GET /api/ops/bootstrap` endpoint in new `backend/app/api/routes/ops.py` and register router | `pytest backend/tests/api/test_ops_bootstrap.py` |
| OPS-S1-006 | Implement tenancy/authz helper (`session_id`/`user_id` ownership enforcement) and apply to bootstrap | `pytest backend/tests/api/test_ops_authz.py` |
| OPS-S1-007 | Add feature flags: `OPS_HUB_ENABLED`, `OPS_LIVE_RANKS_ENABLED`, `OPS_OAUTH_ENABLED` in config | `pytest backend/tests/core/test_ops_feature_flags.py` |
| OPS-S1-008 | Add structured logs and base counters for `/api/ops` calls (request id, latency, status) | Log assertion test `backend/tests/api/test_ops_logging.py` |
| OPS-S1-009 | Add versioned OpenAPI snapshot test for `/api/ops` | `pytest backend/tests/contracts/test_openapi_ops_snapshot.py` |
| OPS-S1-010 | Add frontend route shell: `frontend/src/app/ops/layout.tsx` and `frontend/src/app/ops/page.tsx` | `npm run test -- ops/layout.test.tsx` |
| OPS-S1-011 | Add typed API client skeleton `frontend/src/lib/ops-api.ts` and bootstrap hook | `npm run test -- ops-api/bootstrap.test.ts` |
| OPS-S1-012 | Add frontend test stack (`Vitest`, RTL) + e2e stack (`Playwright`) with one smoke test for `/ops` | `npm run test`, `npm run test:e2e -- ops-smoke.spec.ts` |

### Sprint acceptance tests
1. `/ops` loads with auth-aware shell and no console errors.
2. `/api/ops/bootstrap` returns deterministic JSON for seeded and non-seeded users.
3. Contract snapshot and smoke e2e pass in CI.

---

## Sprint 2: Onboarding Wizard and Setup Task Engine
**Sprint goal:** complete 3-step onboarding with persisted progress and checklist progression.
**Demo slice:** user completes business type, location count, goals; checklist updates to next actionable task.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S2-001 | Add onboarding endpoints `GET /api/ops/onboarding` and `PUT /api/ops/onboarding` | `pytest backend/tests/api/test_ops_onboarding_api.py` |
| OPS-S2-002 | Add server-side onboarding validator (step order, required selections, multi-select minimum) | `pytest backend/tests/services/test_onboarding_validation.py` |
| OPS-S2-003 | Add setup task generator that seeds tasks when onboarding completes | `pytest backend/tests/services/test_setup_task_generation.py` |
| OPS-S2-004 | Add `GET /api/ops/setup-tasks` endpoint and task status DTO | `pytest backend/tests/api/test_setup_tasks_api.py` |
| OPS-S2-005 | Build `OnboardingWizard` container with state machine and persisted draft state | `npm run test -- onboarding/wizard-state.test.tsx` |
| OPS-S2-006 | Build progress bar + step shell (`ProgressStepper`) matching screenshot progression logic | `npm run test -- onboarding/progress-stepper.test.tsx` |
| OPS-S2-007 | Implement Step 1 business-type tile selection UI with required gating | `npm run test -- onboarding/step1-business-type.test.tsx` |
| OPS-S2-008 | Implement Step 2 location-count tile selection UI with required gating | `npm run test -- onboarding/step2-location-count.test.tsx` |
| OPS-S2-009 | Implement Step 3 goal multi-select UI with minimum-1 rule | `npm run test -- onboarding/step3-goals.test.tsx` |
| OPS-S2-010 | Implement `/ops` checklist view (`SetupChecklist`) with locked/unlocked states | `npm run test -- ops/setup-checklist.test.tsx` |
| OPS-S2-011 | Add routing guard: incomplete onboarding redirects to `/ops/onboarding` | `npm run test -- ops/onboarding-guard.test.tsx` |
| OPS-S2-012 | Add e2e onboarding completion path and accessibility assertions | `npm run test:e2e -- onboarding-complete.spec.ts` |

### Sprint acceptance tests
1. All three steps persist on refresh.
2. Next button is correctly disabled/enabled by validation state.
3. `/ops` checklist reflects completed onboarding and next task.

---

## Sprint 3: Location Management Core + OAuth Risk Spike
**Sprint goal:** location CRUD flow and early validation of OAuth/provider integration risk behind flags.
**Demo slice:** user creates/edits/deletes locations; one provider OAuth handshake works in sandbox mode.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S3-001 | Add `GET /api/ops/locations` and `POST /api/ops/locations` endpoints | `pytest backend/tests/api/test_locations_list_create.py` |
| OPS-S3-002 | Add `PATCH /api/ops/locations/{id}` and `DELETE /api/ops/locations/{id}` | `pytest backend/tests/api/test_locations_update_delete.py` |
| OPS-S3-003 | Implement address normalization utility and canonical comparison key | `pytest backend/tests/services/test_address_normalization.py` |
| OPS-S3-004 | Add duplicate-location conflict detection and merge suggestion payload | `pytest backend/tests/services/test_location_dedup.py` |
| OPS-S3-005 | Add location source-mode schema (`connect`, `find`, `no_listing`) with branch validation | `pytest backend/tests/services/test_location_source_modes.py` |
| OPS-S3-006 | Build `LocationSourceSelector` and `LocationForm` components with field-level errors | `npm run test -- locations/location-form-validation.test.tsx` |
| OPS-S3-007 | Build `/ops/locations/new` and `/ops/locations/[id]/edit` pages | `npm run test -- locations/routes-render.test.tsx` |
| OPS-S3-008 | Build `/ops/locations` overview table with base columns and action CTAs | `npm run test -- locations/overview-table.test.tsx` |
| OPS-S3-009 | Add backend/FE integration wiring for create/edit/save with optimistic UI states | `npm run test -- locations/save-flow.integration.test.tsx` |
| OPS-S3-010 | Add OAuth spike endpoints for one provider (`/connections/google/oauth/start`, `/callback`) under `OPS_OAUTH_ENABLED` | `pytest backend/tests/api/test_oauth_spike_google.py` |
| OPS-S3-011 | Add token encryption utility and storage schema checks for spike flow | `pytest backend/tests/security/test_token_encryption.py` |
| OPS-S3-012 | Add e2e: create location + edit location + OAuth spike happy path | `npm run test:e2e -- locations-and-oauth-spike.spec.ts` |

### Sprint acceptance tests
1. Full location CRUD works with dedupe handling.
2. OAuth spike callback round-trip succeeds in sandbox/stub provider mode.
3. All routes enforce ownership checks.

---

## Sprint 4: Local Search Grid Builder + Preview + Email Readiness
**Sprint goal:** report configuration experience with strict validation and map preview.
**Demo slice:** user configures report via accordion sections and saves a valid report draft with preview.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S4-001 | Add report config endpoints: create draft + update draft (`POST/PATCH /api/ops/reports/local-grid`) | `pytest backend/tests/api/test_report_config_api.py` |
| OPS-S4-002 | Add preview endpoint `POST /api/ops/reports/local-grid/{id}/preview` with deterministic geometry generator | `pytest backend/tests/api/test_report_preview_api.py` |
| OPS-S4-003 | Add map-criteria validator (grid size, spacing, radius, center bounds) | `pytest backend/tests/services/test_map_criteria_validation.py` |
| OPS-S4-004 | Add keyword parser service (trim, dedupe, max=5, empty guard) | `pytest backend/tests/services/test_keyword_rules.py` |
| OPS-S4-005 | Add schedule normalizer (IANA timezone + UTC persistence) | `pytest backend/tests/services/test_schedule_normalization.py` |
| OPS-S4-006 | Add recipient email parser/validator with per-email errors | `pytest backend/tests/services/test_email_recipient_validation.py` |
| OPS-S4-007 | Add email readiness endpoint/config check (SPF/DKIM/bounce policy flags) | `pytest backend/tests/api/test_email_readiness.py` |
| OPS-S4-008 | Build `LocalGridBuilder` shell and `ReportAccordionSection` states | `npm run test -- reports/builder-accordion.test.tsx` |
| OPS-S4-009 | Build location/business details section UI and binding | `npm run test -- reports/section-location-details.test.tsx` |
| OPS-S4-010 | Build map criteria section and `GridMapPreview` component | `npm run test -- reports/section-map-criteria.test.tsx` |
| OPS-S4-011 | Build keyword section with live counter and invalid state handling | `npm run test -- reports/section-keywords.test.tsx` |
| OPS-S4-012 | Build general settings section (schedule + recipients + create CTA gating) and e2e draft-save flow | `npm run test:e2e -- report-builder-draft-save.spec.ts` |

### Sprint acceptance tests
1. Invalid inputs block save with precise field errors.
2. Preview map updates deterministically from config.
3. Draft report is persisted and re-openable.

---

## Sprint 5: Report Run Pipeline, Reliability Layer, Results Heatmap, Metrics Customization
**Sprint goal:** asynchronous run execution with robust failure handling and results visualization.
**Demo slice:** user runs report, sees queued/running/completed states, explores heatmap, and manages displayed metrics.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S5-001 | Add run endpoints: `POST /run`, `GET /runs`, `GET /runs/{runId}` | `pytest backend/tests/api/test_report_run_api.py` |
| OPS-S5-002 | Add run state machine (`draft -> queued -> running -> completed|failed`) with transition guards | `pytest backend/tests/services/test_run_state_machine.py` |
| OPS-S5-003 | Add Celery task for deterministic simulated ranking generation and persistence | `pytest backend/tests/workers/test_simulated_run_task.py` |
| OPS-S5-004 | Add idempotency keys for run requests | `pytest backend/tests/api/test_run_idempotency.py` |
| OPS-S5-005 | Add retry policy and terminal failure classification | `pytest backend/tests/services/test_run_retry_policy.py` |
| OPS-S5-006 | Add DLQ storage and replay endpoint for failed runs | `pytest backend/tests/api/test_run_dlq_replay.py` |
| OPS-S5-007 | Add failure-injection tests for timeout/provider-failure scenarios | `pytest backend/tests/resilience/test_run_failure_injection.py` |
| OPS-S5-008 | Build `/ops/reports/local-search-grid/[id]/results` page with `RankingsHeatmapMap` and legend | `npm run test -- reports/results-heatmap-render.test.tsx` |
| OPS-S5-009 | Add run status banner and retry action UX | `npm run test -- reports/run-status-banner.test.tsx` |
| OPS-S5-010 | Add metric preference endpoints (`GET/PUT /locations/metrics/preferences`) with max=6 + ordering | `pytest backend/tests/api/test_metric_preferences_api.py` |
| OPS-S5-011 | Build `EditMetricsPanel` with drag-reorder and persistence | `npm run test -- locations/edit-metrics-panel.test.tsx` |
| OPS-S5-012 | Add e2e flows: completed run path + failed run replay path + metric customization | `npm run test:e2e -- run-results-and-replay.spec.ts` |

### Sprint acceptance tests
1. Report runs execute asynchronously with reliable states.
2. Replay from DLQ succeeds for transient failures.
3. Results map and metric toolbar are stable across reloads.

---

## Sprint 6: Connections UX, Staged Adapters, Review-Generation Entry, Adapter Conformance
**Sprint goal:** operational connection management and review-generation launch path from Operations Hub.
**Demo slice:** user connects staged providers, sees health/status, and opens review generation with context handoff.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S6-001 | Add `GET /api/ops/connections` and `POST /api/ops/connections/{platform}/manual` | `pytest backend/tests/api/test_connections_api.py` |
| OPS-S6-002 | Add staged sync trigger endpoint and last-sync metadata model | `pytest backend/tests/api/test_connections_sync_trigger.py` |
| OPS-S6-003 | Implement adapter interface for staged connectors (google/facebook/analytics mock adapters) | `pytest backend/tests/adapters/test_staged_adapter_interface.py` |
| OPS-S6-004 | Add adapter conformance suite with fixture-driven contract checks | `pytest backend/tests/contracts/test_adapter_conformance.py` |
| OPS-S6-005 | Add connection-health computation service (active/expired/error/disconnected) | `pytest backend/tests/services/test_connection_health.py` |
| OPS-S6-006 | Build `/ops/connections` page with `ConnectionCard` grid | `npm run test -- connections/connection-cards.test.tsx` |
| OPS-S6-007 | Add connection detail panel (status reason, last sync, action CTA) | `npm run test -- connections/connection-details.test.tsx` |
| OPS-S6-008 | Add expired token/reconnect UX flow for staged mode | `npm run test -- connections/reconnect-flow.test.tsx` |
| OPS-S6-009 | Build `/ops/review-generation` entry page with task framing and CTA | `npm run test -- reviews/review-generation-entry.test.tsx` |
| OPS-S6-010 | Add deep-link/context handoff to `/app?tool=review_responder` | `npm run test -- reviews/review-generation-handoff.test.tsx` |
| OPS-S6-011 | Add backend/frontend analytics events for connect/sync/review-launch actions | `pytest backend/tests/telemetry/test_ops_events.py` |
| OPS-S6-012 | Add e2e staged connection + review generation launch flow | `npm run test:e2e -- connections-and-review-launch.spec.ts` |

### Sprint acceptance tests
1. Connection states render accurately with actionable remediation.
2. Adapter conformance suite prevents provider payload drift.
3. Review generation opens correct downstream tool with carried context.

---

## Sprint 7: Live OAuth and Live Adapters Behind Flags
**Sprint goal:** production-grade OAuth + first live provider path while preserving simulated fallback.
**Demo slice:** with flags enabled in staging, user authenticates provider and receives live-backed data.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S7-001 | Implement production OAuth start endpoint with signed `state` + nonce + expiry | `pytest backend/tests/security/test_oauth_state_nonce.py` |
| OPS-S7-002 | Implement OAuth callback code exchange and encrypted token persistence | `pytest backend/tests/api/test_oauth_callback_exchange.py` |
| OPS-S7-003 | Implement token refresh worker and revocation/error handling | `pytest backend/tests/workers/test_token_refresh.py` |
| OPS-S7-004 | Implement first live provider adapter (read path) and map to internal adapter contract | `pytest backend/tests/adapters/test_live_provider_read_adapter.py` |
| OPS-S7-005 | Implement live rank adapter with same response schema as simulated adapter | `pytest backend/tests/adapters/test_live_rank_adapter_contract.py` |
| OPS-S7-006 | Add fallback policy: automatic simulated fallback on provider outage/throttle | `pytest backend/tests/resilience/test_live_fallback_policy.py` |
| OPS-S7-007 | Add rate limiting/circuit breaker for provider client | `pytest backend/tests/resilience/test_provider_rate_limit_circuit_breaker.py` |
| OPS-S7-008 | Add contract parity test suite (simulated vs live payload compatibility) | `pytest backend/tests/contracts/test_simulated_live_parity.py` |
| OPS-S7-009 | Add frontend live OAuth UX (start, callback status, success/error states) | `npm run test -- connections/live-oauth-ui.test.tsx` |
| OPS-S7-010 | Add provenance badge UI (`simulated` vs `live`) on results surfaces | `npm run test -- reports/provenance-badge.test.tsx` |
| OPS-S7-011 | Add kill-switch and flag governance tests for runtime disable | `pytest backend/tests/core/test_ops_kill_switch.py` |
| OPS-S7-012 | Add staging e2e with provider sandbox fixtures + manual verification checklist artifact | `npm run test:e2e -- live-oauth-staging.spec.ts` and `docs/ops/staging-verification-checklist.md` |

### Sprint acceptance tests
1. Live OAuth and token lifecycle are secure and recoverable.
2. Live adapter can be toggled on/off without FE contract changes.
3. Provider failures degrade gracefully to simulated mode.

---

## Sprint 8: Release Hardening, Regression, Canary, and Cutover
**Sprint goal:** production readiness with migration safety, observability, reliability, and rollout control.
**Demo slice:** canary deployment with full regression pass and validated rollback procedure.

| Ticket | Atomic committable change | Validation |
|---|---|---|
| OPS-S8-001 | Add migration/backfill dry-run script for legacy profile/location data | `pytest backend/tests/migrations/test_backfill_dry_run.py` |
| OPS-S8-002 | Add rollback script and rollback verification tests | `pytest backend/tests/migrations/test_rollback_verification.py` |
| OPS-S8-003 | Add full cross-tenant negative test suite for `/api/ops/*` | `pytest backend/tests/security/test_ops_cross_tenant_leakage.py` |
| OPS-S8-004 | Add backend load tests for run throughput and API P95 targets | `k6` report artifact + threshold gate in CI |
| OPS-S8-005 | Add frontend performance test for large heatmap + table render | Lighthouse CI budget + React profiler artifact |
| OPS-S8-006 | Add accessibility audit suite for all `/ops` routes | `npm run test:e2e -- ops-a11y.spec.ts` (axe assertions) |
| OPS-S8-007 | Fix remaining accessibility issues found by automated/manual audit | a11y regression tests pass |
| OPS-S8-008 | Add chaos tests for provider outage, queue backlog, and replay recovery | `pytest backend/tests/resilience/test_ops_chaos.py` |
| OPS-S8-009 | Add full e2e regression matrix for onboarding->location->builder->run->results->connections | `npm run test:e2e -- ops-regression.spec.ts` |
| OPS-S8-010 | Build observability dashboard definitions and alert thresholds | dashboard JSON + alert rule tests |
| OPS-S8-011 | Add canary rollout runbook with kill-switch and rollback owner mapping | `docs/ops/canary-runbook.md` reviewed checklist |
| OPS-S8-012 | Execute release readiness checklist and publish go/no-go artifact | `docs/ops/release-signoff.md` with checklist completion |

### Sprint acceptance tests
1. Canary rollout and rollback are both proven in staging.
2. Full regression suite passes with feature flags in release configuration.
3. SLO/error budget dashboards and alerts are operational.

---

## End-to-End Demo Progression by Sprint
1. Sprint 1: `/ops` shell + bootstrap API.
2. Sprint 2: complete onboarding + checklist gating.
3. Sprint 3: location CRUD + OAuth spike.
4. Sprint 4: local grid builder + validated preview.
5. Sprint 5: async run + heatmap results + replay + metric customization.
6. Sprint 6: connections management + review-generation launch.
7. Sprint 7: live OAuth/provider integration behind flags.
8. Sprint 8: canary release readiness + rollback verification.

## Test Matrix (Required Coverage)
1. Unit tests: validators, parsers, state machines, component logic.
2. Integration tests: endpoint + repository + service orchestration.
3. Contract tests: OpenAPI snapshot + adapter conformance + simulated/live parity.
4. Security tests: authz boundaries, OAuth state/nonce, token lifecycle.
5. Resilience tests: retries, DLQ/replay, outage fallback, failure injection.
6. E2E tests: critical user journeys across `/ops` surfaces.
7. A11y tests: automated checks for every new page.
8. Performance checks: backend load thresholds and frontend render budgets.

## Assumptions and Defaults
1. Sprint count fixed at 8 (user-selected).
2. Scope is full parity flow, with staged data first and live integrations behind flags.
3. All tickets are commit-sized and independently reviewable.
4. All new APIs require ownership checks (`session_id`/`user_id`).
5. Quality gates run every sprint, not only at release.
6. This is markdown content intended for `docs/CODEX_REPUTATION_OPS_HUB_SPRINT_BACKLOG.md`.
