# Core Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete every missing function in the approved 10-week core with usable UI, real API/PostgreSQL and verified release gates.

**Architecture:** Existing FastAPI modular monolith, synchronous SQLAlchemy Sessions and one UoW per command; React/Vite with generated OpenAPI client, Keycloak PKCE and shared API/auth shell. Domain modules communicate through Python services sharing Session; worker handles materialized reports and private CSV artifacts.

**Tech Stack:** Python3.13/FastAPI/PostgreSQL17/Alembic, React19/TypeScript/Vite/Node24, pytest, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-11-03-core-library-design.md` (approved by user on03/11/2026).

## Global Constraints

- Lõi gồm **F01–F09, F11–F14, F16, F18–F20**; phase2 remains F10/F15/F17/F21–F24.
- Command camelCase, entity snake_case; money integer VND strings at HTTP and numeric(14,0) in PostgreSQL; API timestamps UTC, library days Asia/Ho_Chi_Minh.
- Existing C01–C09 unchanged; no arbitrary fee schedule, no active loan/hold limits. Checkout4 books/loan, initial4days, renew once +4days from old due, age12–55, card6calendar months, late1000/day/book, debt0.
- Preserve dictionary columns; D01 approved kind varchar(16), status varchar(24), version/created_at NOT NULL. Borrowing/finance snapshots immutable.
- One UoW per command; permission+ACTIVE account checked server-side; idempotency replay and audit in same commit; no mock substitutes real core acceptance.
- New migrations form one linear chain: 0003_policy → 0004_library_core → 0005_reporting. Existing identity/platform migrations stay unchanged; test DB disposable only.
- Use an isolated worktree for core implementation because another session is editing frontend/Figma in the original checkout. Do not overwrite those files or stage unrelated local changes.
- Each implementer owns only their task; no subagents, no shared-branch push. Main router/model registration/OpenAPI changes allowed within task sequentially; later tasks retain earlier routes.

## Review Focus

- Policy boundary and concurrent approvals: typed rules, `[from,to)`, no retroactivity, immutable historical decisions (Task1).
- Month-end card issue and partially returned loan renewal: calendar clamp; renew all OPEN atomically and ignore closed items (Task2).
- Payment reversal at zero debt: cap by original unreversed amount, reverse allocations atomically, prevent cross-reader links (Task2).
- Export access changed after job creation: recheck owner+permission before status/expiry/content; formula-safe CSV and stable result pagination (Task3).
- Real login and network failures: no token in storage/query, no mock production path, preserve command key on retry, 409 keeps input (Task4/5).

## Task 1: Policy F14 vertical backend foundation

**Files:** Create `apps/api/src/lib_management/policy/{__init__,models,schemas,rules,service,router}.py`, migration `0003_policy.py`, tests `test_policy_rules.py` and `integration/test_policy.py`; modify model loader/main, integration cleanup, OpenAPI. Update BE02 status only with evidence.

**Interfaces:** `policy.service.current_policy(session: Session, at: datetime) -> PolicyVersion` (422 AppError code POLICY_NOT_EFFECTIVE if absent); `policy.service.snapshot(policy: PolicyVersion) -> dict[str, Any]` detached immutable value; `policy.rules.PolicyRules` frozen typed camelCase v1 fields as approved spec, `default_rules() -> PolicyRules`. ORM table `policy_version` exact10 columns. These names are binding for Task2.

- [ ] Write failing API/PG tests for list/create/detail/approval, wrong permission, typed rules, future first approval, stale expectedVersion, retry replay/mismatch, schedule replacement, concurrent overlap, immutable snapshot/no-effective policy.
- [ ] Run focused tests and retain actual expected failing output.
- [ ] Implement typed rules, ORM/migration range exclusion, advisory schedule lock, service/API, audit/idempotency, deterministic pagination and Location. Keep same error/UoW patterns.
- [ ] Update OpenAPI only implemented F14 paths and add detail path; source manifest can be regenerated in Task5.
- [ ] Run full pytest on fresh DB, migration round-trip/alembic check, ruff/mypy/wheel; self-review and commit only task files.

## Task 2: First library workflow and remaining circulation/finance core

**Files:** Create domain packages `catalog`, `readers`, `finance`, `circulation` with focused models/schemas/service/router modules (split service into command/query modules as needed); `0004_library_core.py`; unit helpers/date/money tests and integration files per module. Modify loader/main/OpenAPI/CLI/test cleanup. No frontend changes.

**Interfaces:** import policy interfaces from Task1. Export ORM names matching dictionary (`BookEdition`, `BookCopy`, `Category`, `Author`, `Publisher`, `Location`, `Reader`, `ReaderCard`, `Loan`, `LoanItem`, `RenewalEvent`, `RenewalItem`, `ReturnEvent`, finance ledger classes). `readers.service.eligibility(session: Session, reader_id: UUID, at: datetime) -> dict[str, Any]`. Reports Task3 imports these ORM models; no HTTP inside services.

- [ ] Write failing PG/API workflow test: manager creates future policy then moves fixture clock/policy schedule through controlled setup; librarian creates refs/location/edition/copies and Reader/card; checkout4 succeeds,5 fails; return GOOD/LOST/DAMAGED; pending blocks checkout/renew but not return; manager decides assessment; collect/waive/reverse; renew all OPEN; overdue read.
- [ ] Add independent tests for year/age bounds, month clamp, same-copy race, whole-command rollback, idempotency, role/scope, partially returned renew, concurrent assessment/payment/reversal, SQL/text search input.
- [ ] Run focused tests RED, implement exact dictionary mappings and approved D01, partial unique open-copy constraint, consistent ordered locks, policy snapshot and append-only ledger. Preserve command request DTOs/status/operationId from OpenAPI; no whole-entity writable DTO.
- [ ] Implement every existing core-tagged operation for F01–F09/F11/F12/F18/F19. Explicitly defer dual-tagged `/accounts/reader-provisioning` per approved spec; add audited reader-link CLI. Add locations/list reference and staff loan lookup contract as specified; avoid phase2 reservation/storage UI.
- [ ] Update OpenAPI metadata/schema only as required by actual implemented behavior; integration fixtures truncate new tables in FK-safe order. No bypass auth in production.
- [ ] Run all tests on disposable PG, migration round trip/alembic check, ruff/mypy/wheel; self-review and commit task files.

## Task 3: Materialized reports, private artifact storage and CSV

**Files:** Create `reporting/{models,schemas,service,queries,router,handlers}.py`, `storage/{__init__,base,local}.py`, `0005_reporting.py`; tests unit CSV + PG report/export flows. Modify registry/settings/loader/main/OpenAPI/test cleanup. No frontend changes.

**Interfaces:** consume Task2 models and existing Job/outbox/Runner. New `default_registry` allowlist registers report/export handlers without circular imports; retain noop. `Storage` port writes/opens private artifacts by server UUID keys, fixed root, no client paths; local adapter and test fixture root configurable. `ReportJob`/`MediaAsset` exact dictionary fields. No task can directly expose object_key or requester supplied by client.

- [ ] Write failing API/worker tests for create202+Location, worker materialization under REPEATABLE READ, result metrics/rows stable pagination, zero rows, CSV quoting/formula injection/large amounts, job failure, no duplicate artifact on retry, revocation/scope/expiry (404 before410), content download Bearer.
- [ ] Implement typed report types LENDING_SUMMARY/OVERDUE and filters from/to; reject client asOf422. Snapshot as_of is server worker-start; count received returns only return_kind RETURNED. Persist JSON result and CSV artifacts with checksum/size, no query rerun when paging result. Request and data time distinct while queued.
- [ ] Implement report/export/job viewing using permission+ownership, `GET /report-jobs/{id}/result`, keep JSON DownloadLink and separate authenticated `/export-jobs/{id}/content` streaming text/csv; API money strings. Recheck permission before issuing URL/opening content.
- [ ] Update contract/registry/settings/migration; run focused then full PG suite, migration round trip/alembic check, lint/type/wheel; self-review and commit.

## Task 4: Complete frontend M0 and all core screens

**Files:** `apps/web/src/api`, `auth`, `shell`, `ui`, `features`, `lib`, app/router/providers, package/lock/scripts/config/test/e2e. Use existing design tokens/wireframes; inspect concurrently created frontend in original checkout as potential reusable input; copy only reviewed source and never overwrite that checkout.

**Interfaces:** generated client from final OpenAPI; same-origin /api and /health Vite proxy; existing runtime config schema. Keycloak public client uses PKCE, tokens memory only, auth/me returns account+permissions. All business API DTOs generated, no hand-maintained duplicate entity types.

- [ ] Write failing Vitest/Testing Library tests for API errors/401 once/403, idempotency, currency/date, session states and permission routes; core form actions and receipts from actual response shapes.
- [ ] Complete M0 PR2–5 and core views: policy create/diff/approval, catalog/ref/location/copies search/admin, Reader/card/eligibility, checkout/return/renew/receipt, assessment/payment/waiver/reversal, overdue, report filters/result/job/download. Clear Vietnamese labels, loading/empty/error/pending; preserve input on409.
- [ ] Each visible core action has a real API call, bounded validation and permission check; no successful local-only business state. Disable/hide phase2 and planned routes in production. Components cannot call fetch directly.
- [ ] Implement responsive shell, keyboard/focus/labels/reduced-motion and no mock markers in production. Generated client drift script+CI, no token in storage/URL/log.
- [ ] Run clean npm ci, lint/format/typecheck/Vitest/build; review multiple TSX components using react-best-practices; commit task files only.

## Task 5: Real-system E2E, release core and complete documentation

**Files:** Playwright suite/config, fixtures/script for disposable PG+Keycloak users and cleanup, web container/reverse proxy, Compose/CI, source manifest, plan/spec status and acceptance matrix, runbook README.

- [ ] Start real API/worker/web/Keycloak against isolated DB; existing container services may be used but no reset of dev data. Implement test orchestration without requiring production secrets or Docker when services already accessible.
- [ ] Run browser login → approve policy → catalog → Reader/card → borrow → return GOOD/DAMAGED/LOST → assessment/collect → renewal/overdue → report/CSV download; check DB invariants. Add no-permission/expired-session, mobile keyboard, reduced-motion checks.
- [ ] Run race/failure tests and migration round trip plus full backend/frontend checks. Build web/API production artifacts/container when runtime available; otherwise record exact external limitation while completing all runnable checks.
- [ ] Update CI core gates independently of phase2; hosting not selected automatically. Refresh manifest and documentation; mark implemented/merged/accepted distinctly with fresh commands/results and actual limits.
- [ ] Request whole-branch review, resolve important findings, rerun affected checks; integrate according to existing user authorization without force push or overwriting other-session files.
