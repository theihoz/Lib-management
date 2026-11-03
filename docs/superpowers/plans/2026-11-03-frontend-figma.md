# Frontend Figma Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the 71 approved design screens as a responsive React app, connect current auth/health APIs and prepare typed business clients.

**Architecture:** Keep the existing Vite application. Shared shell and feature views consume a screen registry, typed API services and an in-memory OIDC session. Development-only fixtures power a separate design browser; live routes never substitute fixtures for backend responses.

**Tech Stack:** React 19, TypeScript, Vite, React Router 7, TanStack Query 5, openapi-fetch/openapi-typescript, keycloak-js 26, CSS, Vitest/Testing Library.

**Spec:** `docs/design/frontend-figma-integration.md` (approved 03/11/2026).

## Global Constraints

- Branch `frontend`; preserve pre-existing user changes; no backend business implementation.
- 71 screens, FE01–FE11; source `docs/libmanagement-figma`.
- Colors, typography, 232px sidebar, breakpoints and reduced motion follow existing frontend design direction.
- Tokens and PII never enter localStorage/sessionStorage.
- Real errors retain inputs; development fixtures never enter production output.

## Review Focus

- HTML/proxy/network errors must become readable API errors, not crash parsing.
- Retrying a command preserves its idempotency key; changing payload replaces it.
- Missing/expired/locked/unlinked sessions must not expose staff content.
- All 71 screens must render with long Vietnamese labels and empty states.
- Production must exclude design fixtures, preview-only routes and sample transaction confirmations.

### Task 1: Typed API boundary

**Files:** `apps/web/src/api/{schema.d.ts,client.ts,errors.ts,idempotency.ts,services.ts,client.test.ts}`, `apps/web/src/lib/{money.ts,datetime.ts}`, package scripts/dependencies.

**Interfaces:** `createApiClient({baseUrl,getToken,refresh,onExpired,onForbidden})`, typed `ApiServices`, `ApiError`, `createIdempotencyKey()`.

- [ ] Write/run failing tests for Bearer/request IDs, HTML errors, network failure, refresh once, stable idempotency and exact VND formatting.
- [ ] Install locked dependencies and generate schema using `npm run gen:api`.
- [ ] Implement client and module services from generated `paths`; run targeted tests and typecheck.

### Task 2: Session and production navigation

**Files:** `apps/web/src/auth/{session.tsx,keycloak.ts}`, `src/app/{routes.ts,App.tsx}`, `src/shell/Shell.tsx`, auth/navigation tests.

**Interfaces:** `useSession()` exposes session state, permissions, login/logout; `useServices()` exposes API services. `AppRoute` defines screen ID/path/permission/availability.

- [ ] Test public routes, permission checks and inactive/unlinked error classification.
- [ ] Implement Keycloak PKCE with memory-only tokens and single initialization, server-derived permissions, cache reset, route guards and logout confirmation.
- [ ] Verify existing config-error behavior and current auth/health integration.

### Task 3: Shared visual system and all design screens

**Files:** `src/ui/{styles.css,components.tsx,Icon.tsx}`, `src/features/{CatalogViews,PeopleViews,CirculationViews,FinanceViews,ManagementViews,OperationsViews}.tsx`, `src/dev/{DesignBrowser.tsx,fixtures.json}`, screen registry and tests.

**Interfaces:** `DesignScreen`, `ScreenContext {screen,preview,data}`, reusable panels/fields/table/dialog/receipt/book cover, `FeatureView` renderer.

- [ ] Test 71 unique IDs/routes and representative forms, table filtering and confirmation dialogs; run red tests.
- [ ] Implement exact design tokens, responsive shell, drawer, skip link, reduced motion and print rules.
- [ ] Build all screen kinds with shared feature-specific views, using fixture values only in the lazy development browser.
- [ ] Keep live planned modules explicitly unavailable; disable mutations until implemented and authenticated; do not fabricate receipts.
- [ ] Run component tests across all 71 fixture screens.

### Task 4: Verification and handoff

**Files:** frontend README, integration evidence, package verification scripts.

- [ ] Run schema drift check, lint, formatter, typecheck, tests and production build.
- [ ] Check production output excludes fixture markers and sample data.
- [ ] Check live frontend, design routes, React modules and proxy readiness against actual backend/PostgreSQL.
- [ ] Review React accessibility/hooks/TypeScript checklist and request independent final code review; address material findings.
- [ ] Keep dev servers running for user review; report live URLs and unverified SSO/browser limitations accurately.

Implementation proceeds inline in this session under the user's approved design and instruction to deploy the changes on `frontend`.
