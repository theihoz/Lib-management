# Spec Gap Completion Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking. One PR per task, each green on `ci-result` before the next starts unless marked parallel.

**Goal:** Close every gap between the group specs (requirements sheet, Lab 2 v2, Lab 3, Lab 4) and the code: core gaps G1–G8 first, contract/E2E quality Q1–Q2 alongside, then phase 2 P1–P7.

**Spec:** `docs/superpowers/specs/2026-11-04-spec-gap-completion.md` (Approved 04/11/2026: D1–D4 as proposed; D5–D6 proposed defaults).

**Architecture:** unchanged — FastAPI modular monolith with one UoW per command, PostgreSQL 17 + Alembic linear chain (next revision `0009_*`), React/Vite with generated OpenAPI client, worker for jobs.

## Global Constraints

- Migrations continue the chain after `0008_category_rules`; each task adds at most one revision, reversible, tested by the business suite's downgrade/upgrade round trip.
- Every new or changed operation: update `docs/design/openapi.json` (`x-status: implemented` only when served and tested), `npm run gen:api`, mock demo if a screen depends on it.
- Rules come from `PolicyVersion.rules` (schema v2); never hard-code a QĐ value in a route.
- Business tests use the disposable DB (`RUN_BUSINESS_DB_TESTS=1`); never run `RUN_DB_INTEGRATION` against the dev DB.
- Update `docs/specs/source-rules.md` and `docs/quality/acceptance-matrix.md` in the same PR as the behavior.

## Order and dependencies

| Wave | Tasks | Notes |
| --- | --- | --- |
| 1 | Task 1 (Q1), Task 2 (G1), Task 3 (G2) | Q1 first so later tasks flip `x-status` honestly |
| 2 | Task 4 (G3), Task 5 (G4) | G4 uses G2 labels and G3 balances |
| 3 | Task 6 (G5), Task 7 (G6), Task 8 (Q2) | Q2 E2E covers waves 1–3 |
| 4 | Task 9 (G7), Task 10 (G8) | UI-heavy, parallel |
| 5 | Task 11 (P1), Task 12 (P3) | Completes YC#10, YC#17 portal |
| 6 | Task 13 (P5), Task 14 (P2), Task 15 (P4) | P2/P4 need R2/Keycloak admin credentials in env |
| 7 | Task 16 (P7), Task 17 (P6) | Blocked on SMTP / backup storage decisions (D6) |

## Task 1: Q1 — truthful contract status

**Files:** create `scripts/openapi_status.py`; modify `docs/design/openapi.json`, `apps/api/tests/test_openapi_drift.py`, `README.md`.

- [ ] Script compares design operations with `create_app().openapi()` and rewrites `x-status`.
- [ ] Drift test fails if a served operation is `planned` or an `implemented` one is not served.
- [ ] README "Trạng thái hiện tại": correct served count (63/85 today).

## Task 2: G1 — copy status

**Files:** migration `0009_copy_maintenance.py`; `catalog/{schemas,service,router}.py`; web `features/live/Catalog.tsx` (Copies); tests in `tests/business/test_library_flows.py`.

- [ ] Failing tests: allowed/blocked transitions, ON_LOAN/HELD/RETIRED locked (409), stale version 409, replay, AVAILABLE allocates READY reservation.
- [ ] `PATCH /copies/{id}` with transition table, reason rule, lock order, audit.
- [ ] UI dialog + Vietnamese labels (D1).

## Task 3: G2 — card block/unblock

**Files:** `readers/{schemas,service,router}.py`, `circulation/service.py` (reason `CARD_BLOCKED`), web `Readers.tsx`.

- [ ] Tests: block → checkout 422 `CARD_BLOCKED`; unblock; REVOKED/expired cannot be unblocked.
- [ ] `PATCH /reader-cards/{id}`; derived "Hết hạn" label in API view and UI.

## Task 4: G3 — manual fine proposal

**Files:** migration `0010_manual_assessment.py`; `circulation/{models,schemas,router}.py`; web `Finance.tsx`.

- [ ] Tests: propose MANUAL → PENDING blocks borrowing; decide 0/positive; loanItem of another reader 422; 403 without permission.
- [ ] `POST /charge-assessments`; decision creates `FineCharge.reason='MANUAL'`.
- [ ] UI form on reader finance; manager queue shows kind "Thủ công".

## Task 5: G4 — full reader profile

**Files:** `circulation/{router,views}.py` (`readerId` filters, `balance`), web `Readers.tsx` (ReaderProfile).

- [ ] Tests: filters scope, balance after payment/waiver/reversal.
- [ ] Four profile sections with empty/error states; BM12 columns.

## Task 6: G5 — book search and deactivation

**Files:** `catalog/service.py`, `catalog/router.py`, web `Catalog.tsx`.

- [ ] Tests: author match, category subtree filter, INACTIVE hidden publicly, deactivate blocked with copies on loan.
- [ ] Category tree filter UI; "Ngừng dùng ấn bản".

## Task 7: G6 — reader self-renewal

**Files:** `identity/rbac_seed.py`, `circulation/router.py`, `docs/design/permission-matrix.md`, web portal `/me`.

- [ ] Tests: own loan renews; other reader's loan 404; overdue/debt/reserved reasons shown.
- [ ] Portal renew button with result message; `seed-rbac` updates existing roles.

## Task 8: Q2 — Playwright E2E in repo and CI

**Files:** `apps/web/e2e/*.spec.ts`, `apps/web/playwright.config.ts`, `apps/web/package.json` (`@playwright/test`), `.github/workflows/ci.yml` (job `e2e`, part of `ci-result`), `.devcontainer/Dockerfile` (Chromium deps).

- [ ] Port the verified scratch flows (login ×3, checkout/return, report/CSV, QĐ26, policy draft/approve) plus Tasks 2–7.
- [ ] CI brings the stack up with `scripts/local.sh up`, uploads traces on failure.

## Task 9: G7 — dashboard

**Files:** `reporting/router.py` (+ service SQL reuse), web new `features/live/Dashboard.tsx`, `app/screens.ts`.

- [ ] `GET /dashboard` tests (counts match report SQL, permission).
- [ ] Staff landing page.

## Task 10: G8 — Ctrl+K command palette

**Files:** web `shell/CommandPalette.tsx`, shell integration, tests.

- [ ] Vitest: shortcut, permission-filtered navigation, no request for blank keyword, keyboard navigation.

## Task 11: P1 — reservations (F10)

**Files:** `circulation/{router,service}.py`, rule `maxActiveLoansAndHolds` in `PolicyRules` (rules schema v3 with v2 compatibility), worker job `RESERVATION_EXPIRY`, web FE06 + FE08.

- [ ] Tests: available copy 409, limit 4, FIFO, expiry hands to next, cancel, pickup.
- [ ] Worker schedule + UI.

## Task 12: P3 — my history (F17)

**Files:** `circulation/router.py` (`/me/loans` status/paging), web portal tabs.

## Task 13: P5 — acquisition and disposal (F22)

**Files:** new `acquisition/{models,schemas,service,router}.py` over existing tables, web FE10.

- [ ] Tests: totals computed, QĐ03 per line, approval/posting creates N copies atomically, double posting 409.

## Task 14: P2 — covers (F15)

**Files:** migration `cover_asset_id`, `reporting/storage.py` → shared `platform/storage.py` with R2 adapter, catalog media routes, web FE02.09.

- [ ] Tests with local adapter: magic bytes, size limit D5, finalize attaches; R2 adapter unit-tested with a fake S3.

## Task 15: P4 — accounts and roles (F16/F21)

**Files:** `identity/{router,service}.py`, Keycloak admin adapter, web FE10.

- [ ] Tests with fake Keycloak adapter: provisioning idempotent by email, last admin protected, blocked account rejected next request.

## Task 16: P7 — notifications (F24)

**Files:** `notifications/*`, outbox consumers, SMTP adapter, Mailpit in `compose.local.yaml`, portal notifications.

## Task 17: P6 — backup/restore (F23)

**Files:** worker `BACKUP` handler, restore allowlist, `jobs/{id}/replay`, web FE11.

## Done when

- Every row in `docs/specs/source-rules.md` points to code + test (no "Phase 2" rows left).
- OpenAPI: 85/85 `implemented`, drift test two-way green.
- Acceptance matrix AT01–AT24 at least Partial with E2E evidence; README status updated.
