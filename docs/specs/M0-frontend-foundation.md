# Spec M0 — Nền tảng frontend, client API và đăng nhập

**Trạng thái:** Draft · **Ngày:** 2026-11-03 · **Task:** FE00, FE01 (.1–.3), INT00.2 · **Chức năng:** F16 (nền cho màn hình F01–F20)

Spec này gom các quyết định đã có thành một bản đủ cụ thể để code frontend mốc M0. Nó **không** thay nguồn chuẩn: stack và token lấy từ [decisions](../plan/decisions.md), trình bày từ [định hướng thiết kế](../plan/frontend/DESIGN-DIRECTION.md) và [motion](../plan/frontend/MOTION.md), bố cục từ [wireframe](../plan/frontend/WIREFRAMES.md), schema HTTP từ [openapi.json](../design/openapi.json), quyền từ [ma trận quyền](../design/permission-matrix.md), luồng đăng nhập từ [thiết kế identity](../design/identity-design.md). Khi spec mâu thuẫn với nguồn chuẩn, nguồn chuẩn thắng và spec phải được sửa trong cùng PR.

Phạm vi sản phẩm theo [quyết định 03/11/2026](../plan/decisions.md#quyết-định-03112026--phạm-vi-lõi-10-tuần): lõi 10 tuần F01–F09, F11–F13, F16, F18–F20. Backend tương ứng: [spec M0 backend](M0-backend-foundation.md) — hiện chỉ `GET /api/v1/auth/me` và `/health/*` đã triển khai.

## 1. Phạm vi

**Trong M0**

- Ứng dụng `apps/web` (React + TypeScript + Vite, npm lockfile), Node 24 LTS trong Dev Container.
- Client TypeScript sinh từ `docs/design/openapi.json` (openapi-typescript + openapi-fetch) và kiểm tra drift trong CI.
- Lớp gọi API chung: Bearer, `X-Request-ID`, ánh xạ `ErrorResponse`, cursor pagination, helper `Idempotency-Key`, TanStack Query.
- Design tokens, app shell nhân viên + shell portal, bộ component dùng lại, trang gallery dev để review hình tĩnh.
- Keycloak Authorization Code + PKCE (keycloak-js), token chỉ trong bộ nhớ, các trạng thái phiên, menu theo `AuthContext.permissions`.
- Motion primitives và reduced motion.
- Mock theo OpenAPI (MSW) cho phát triển sớm và test; job CI `web`.

**Ngoài M0**

- Màn hình nghiệp vụ FE02–FE09 (mỗi module một spec/PR riêng khi backend tương ứng có contract chạy được). M0 chỉ đăng ký route và placeholder dev.
- Image production, Nginx/reverse proxy, CSP và hosting: thuộc INT03.
- Phase 2: F10 (giữ chỗ), F15 (ảnh bìa), F17 (lịch sử portal), F21 (quản trị tài khoản — FE10), F22, F23/F24 (FE11).

## 2. Cấu trúc package

```
apps/web/
  index.html
  package.json, package-lock.json
  vite.config.ts            port 5173 strictPort, proxy /api và /health → http://localhost:8000
  tsconfig.json             strict, noUncheckedIndexedAccess
  eslint.config.js, .prettierrc
  playwright.config.ts
  public/
    config.json             cấu hình runtime dev (mục 3.2)
    silent-check-sso.html   trang silent SSO của keycloak-js
  src/
    main.tsx                loadConfig() → createAuthClient() → auth.init() → render
    app/
      providers.tsx         QueryClientProvider, AuthProvider, RouterProvider
      router.tsx            createBrowserRouter; layout StaffShell / PortalShell
      routes.ts             route registry (mục 6.4) — nguồn duy nhất cho router và menu
      AppErrorBoundary.tsx
    config/config.ts        Zod schema RuntimeConfig, loadConfig()
    auth/
      AuthClient.ts         interface: init, login, logout, getToken, onExpired
      keycloakClient.ts     adapter keycloak-js
      mockClient.ts         persona mock — chỉ nạp ở chế độ mock (mục 8)
      AuthProvider.tsx      máy trạng thái phiên (mục 6.2)
      guards.tsx            RequireSession, RequirePermission
      useSession.ts
    api/
      schema.d.ts           SINH TỰ ĐỘNG, không sửa tay
      client.ts             createApiClient(): openapi-fetch + middleware
      errors.ts             ApiError, isApiError, toFieldErrors
      queryClient.ts        defaults (mục 5.4)
      idempotency.ts        useIdempotencyKey()
      authMe.ts             useAuthMe(), key ['auth','me']
    shell/                  StaffShell, PortalShell, Sidebar, NavItem, PageHeader, Breadcrumb
    ui/
      tokens.css, base.css, motion.css
      components/           Button, FormField, TextField, Select, Checkbox, DataTable, LoadMore,
                            Dialog, Toast, Skeleton, EmptyState, ErrorState, StatusBadge,
                            BookTile, ReaderStrip, Receipt, JourneyBar
    pages/                  LoginPage, ForbiddenPage, NotLinkedPage, InactivePage,
                            SessionExpiredPage, NetworkErrorPage, NotFoundPage, PlaceholderPage,
                            dev/GalleryPage
    features/               trống ở M0; FE02+ thêm features/<module>/ (api.ts, pages, components)
    lib/                    money.ts, datetime.ts, cx.ts
    test/                   setup.ts, msw/handlers.ts, msw/personas.ts, render.tsx
  e2e/                      Playwright specs
```

Quy tắc bắt buộc:

- Chỉ `api/` gọi mạng. Feature dùng `apiClient` qua hook TanStack Query trong `features/<module>/api.ts`; component không gọi `fetch`.
- Kiểu request/response lấy từ `api/schema.d.ts` (`paths`, `components["schemas"]`); không tự khai báo lại DTO. Schema Zod chỉ cho form/validation phía client.
- Frontend không tự tính điều kiện nghiệp vụ (eligibility, phí, hạn trả, quyền thật). Hiển thị kết quả và lý do từ server; quyền UI chỉ để ẩn/hiện.
- Một feature không import nội bộ feature khác; dùng chung qua `ui/`, `lib/`, `api/`.
- Không `localStorage`/`sessionStorage` cho token hoặc dữ liệu PII.

## 3. Cấu hình và dependency

### 3.1 Dependency

Chốt version cụ thể trong PR 1 qua `package-lock.json`; không dùng `latest`, `^` chỉ khi lockfile được commit và CI dùng `npm ci`.

| Nhóm | Gói |
| --- | --- |
| Runtime | `react`, `react-dom` (19), `react-router` (7, data router), `@tanstack/react-query` (5), `react-hook-form`, `@hookform/resolvers`, `zod`, `openapi-fetch`, `keycloak-js` (26, khớp Keycloak 26.8 dev) |
| Build | `vite`, `@vitejs/plugin-react`, `typescript`, `openapi-typescript` |
| Chất lượng | `eslint` (9, flat config), `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `prettier` |
| Test | `vitest`, `jsdom`, `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`, `msw` (2), `@playwright/test`, `@axe-core/playwright` |

Không thêm thư viện UI kit, CSS-in-JS, animation hay font CDN. Icon: SVG inline nội bộ trong `ui/icons/` (vài icon cần thiết), không thêm bộ icon lớn.

### 3.2 Cấu hình runtime

`/config.json` được tải trước khi render và validate bằng Zod; sai/thiếu → trang lỗi cấu hình tĩnh (không gọi Keycloak). Cho phép một image chạy nhiều môi trường; file production do INT03 sinh lúc deploy.

```json
{
  "oidcUrl": "http://localhost:8080",
  "oidcRealm": "lib-management",
  "oidcClientId": "lib-management-web",
  "apiBaseUrl": "",
  "mock": false
}
```

- Chỉ chứa giá trị công khai (client public, không secret). `apiBaseUrl` rỗng = cùng origin.
- `mock: true` chỉ có hiệu lực ở bản build chế độ `development`/`e2e` (mục 8); bản `production` bỏ qua.

### 3.3 Dev Container và chạy local

- `.devcontainer/Dockerfile`: thêm Node 24 bằng `COPY --from=node:24-bookworm-slim@sha256:<digest>` (`/usr/local/bin/node`, `/usr/local/lib/node_modules/npm` + symlink `npm`/`npx`); digest chọn khi làm PR 1.
- `devcontainer.json`: `forwardPorts` thêm `5173`; extension `dbaeumer.vscode-eslint`, `esbenp.prettier-vscode`. `.devcontainer/compose.yaml`: publish `127.0.0.1:5173:5173`.
- `setup.sh`: thêm `cd apps/web && npm ci`.
- Vite dev chạy `host: 0.0.0.0`, `port: 5173`, `strictPort: true` — cổng phải đúng 5173 vì realm dev chỉ cho redirect `http://localhost:5173/*`.
- Proxy dev `/api` và `/health` → `http://localhost:8000` (API chạy cùng container) nên không cần CORS ở backend. Production cùng origin qua reverse proxy (INT03).

## 4. Design tokens và component (FE00.2)

### 4.1 Token

`ui/tokens.css` khai báo trên `:root`, đúng giá trị [DESIGN-DIRECTION](../plan/frontend/DESIGN-DIRECTION.md#token-giao-diện): `--canvas #F7F5EF`, `--surface #FFFFFF`, `--ink #17212B`, `--muted #53616B`, `--primary #174B73`, `--accent #9B4B2F`, `--border #D8DCD8`, `--success #146C43`, `--warning #8A4B08`, `--danger #B42318`, `--nav #142C35`. Thêm:

| Token | Giá trị | Lý do |
| --- | --- | --- |
| `--control-border` | `#6B7780` | Viền input/select/checkbox. `--border` chỉ đạt 1.39:1 trên surface, dưới ngưỡng 3:1 cho ranh giới control (WCAG 1.4.11); `#6B7780` đạt 4.59:1 trên surface, 4.21:1 trên canvas |
| `--space-1..6` | 4/8/12/16/24/32px | Thang spacing |
| `--radius-control` / `--radius-panel` | 8px / 12px | |
| `--font-sans` | `Arial, system-ui, sans-serif` | Body 16px, bảng nhân viên 14px, line-height 1.5 |
| `--font-serif` | `Georgia, "Times New Roman", serif` | Chỉ tiêu đề trang 28–36px |
| `--focus-ring` | `2px solid var(--primary)`, offset 3px | |
| `--target-min` | 44px | Chiều cao tối thiểu control tương tác |

`--border` vẫn dùng cho đường chia vùng (trang trí, không mang thông tin). Contrast chữ đo trước khi viết spec (tính theo công thức WCAG 2.x) — đều ≥ 4.5:1: muted 5.85 trên canvas, accent 5.60, success 5.92, warning 6.23, danger 6.03; chữ trắng trên `--nav` 14.57, trên `--primary` 9.17. PR 3 có test tự động tính lại các cặp này để token không bị đổi lệch.

Số tiền, mã, thời gian dùng `font-variant-numeric: tabular-nums`; cột số căn phải.

### 4.2 Breakpoint và shell

| Breakpoint | StaffShell | PortalShell |
| --- | --- | --- |
| ≥ 1200px | Sidebar 232px nền `--nav`; content 2 cột khi trang cần, cột tóm tắt 340px | Header gọn; grid catalog 4–5 cột |
| 768–1199px | Rail 72px (icon + tooltip + `aria-label`) | Grid 3 cột |
| < 768px | Drawer (nút ☰ ở header), 1 cột | Grid 2 cột; bottom nav có `env(safe-area-inset-bottom)` |

Shell không remount khi đổi route; chỉ vùng `<main>` đổi. Header: breadcrumb, tên hiển thị (`account.display_name`), nút Đăng xuất. Nav item active có marker cạnh trái + `aria-current="page"`, không chỉ đổi màu.

### 4.3 Component

Mỗi component có props tối thiểu, trạng thái loading/disabled/error và story trong gallery.

| Component | Hợp đồng chính |
| --- | --- |
| `Button` | `variant` primary/secondary/danger/ghost; `pending` → disabled + nhãn giữ nguyên + `aria-busy`; không đổi kích thước khi pending |
| `FormField` + `TextField`/`Select`/`Checkbox` | Label luôn hiện, `hint`, `error` nối `aria-describedby`/`aria-invalid`; dùng với RHF qua `register`/`Controller` |
| `DataTable<T>` | `columns` (header, cell, `align`, `numeric`), `rows`, `getRowId`, `loading` (skeleton đúng số cột), `empty` slot; trên mobile cuộn trong vùng bảng có caption |
| `LoadMore` | Nhận `useInfiniteQuery` result; nút "Tải thêm", ẩn khi `nextCursor` null |
| `Dialog` | `<dialog>` native + `showModal()`; tiêu đề, đối tượng, tác động; focus phần tử đầu, Escape đóng khi không pending, trả focus về trigger |
| `Toast` | Vùng `role="status"`; không lấy focus; có nút đóng; lỗi quan trọng phải có inline, toast chỉ bổ sung |
| `Skeleton`, `EmptyState`, `ErrorState` | ErrorState hiện `message`, nút Thử lại, và `request_id` (có nút sao chép) với lỗi 5xx |
| `StatusBadge` | `tone` success/warning/danger/neutral + **chữ** + icon; màu không là tín hiệu duy nhất |
| `BookTile` | Ảnh 2:3 (`aspect-ratio`, không layout shift) hoặc fallback chữ title/author; title clamp 2 dòng; số bản khả dụng |
| `ReaderStrip` | Tên/mã/thẻ + danh sách lý do điều kiện từ server; `aria-live="polite"`, không lấy focus |
| `Receipt` | Số phiếu nổi bật, danh sách sách + hạn; `@media print` bỏ shell/motion/shadow |
| `JourneyBar` | Các bước Xác định độc giả → Chọn sách → Xác nhận → Biên nhận; `aria-current="step"` |

`/dev/gallery` (chỉ build development) hiển thị mọi component và trạng thái ở 3 breakpoint, để review hình tĩnh trước khi áp dụng vào màn hình (yêu cầu FE00.D1).

### 4.4 Định dạng dữ liệu

- `lib/money.ts`: API trả tiền là chuỗi số nguyên VND → `formatVnd("12000")` = `12.000 ₫` bằng `BigInt` + `Intl.NumberFormat("vi-VN")`; không `parseFloat`/`Number`. Input tiền gửi lại chuỗi số nguyên.
- `lib/datetime.ts`: response là UTC RFC3339; hiển thị luôn theo `Asia/Ho_Chi_Minh` (giờ thư viện, C08 tính theo ngày địa phương), không theo múi giờ trình duyệt. Định dạng `dd/MM/yyyy HH:mm`.

## 5. Hợp đồng API phía client (INT00.2)

### 5.1 Sinh client và drift

- `npm run gen:api` = `openapi-typescript ../../docs/design/openapi.json -o src/api/schema.d.ts`. File sinh ra được commit.
- CI: chạy `gen:api` rồi `git diff --exit-code apps/web/src/api/schema.d.ts`; lệch → fail. OpenAPI và client đổi trong cùng commit (nghiệm thu INT00).
- Route `planned` vẫn có kiểu (để mock/phát triển sớm); màn hình chỉ được bật cho người dùng thật khi operation tương ứng `x-status=implemented`.

### 5.2 Client và middleware

`createApiClient({ baseUrl, getToken })` dùng `openapi-fetch` `createClient<paths>()` với middleware theo thứ tự:

1. `X-Request-ID`: `crypto.randomUUID()` mỗi request (khớp `^[A-Za-z0-9-]{8,100}$` của backend).
2. Bearer: `await getToken()` (adapter tự `updateToken(30)`); không có token → không gắn header (catalog đọc ẩn danh).
3. Response lỗi: parse `ErrorResponse` → ném `ApiError`. Body không phải JSON (proxy 502…) → `ApiError{code:"NETWORK_ERROR"|"INTERNAL_ERROR"}`; lỗi mạng fetch → `NETWORK_ERROR`.
4. 401: gọi `auth.refresh()` **một lần** rồi gửi lại request; vẫn 401 → phát sự kiện `session-expired`. Không retry lần hai.

`ApiError` gồm `status`, `code`, `message`, `details`, `requestId` (lấy từ body, dự phòng header `X-Request-ID`).

### 5.3 Lỗi → UI

| Tình huống | Xử lý |
| --- | --- |
| 401 `INVALID_TOKEN` (sau refresh) | Trạng thái phiên `expired` → SessionExpiredPage, giữ URL để quay lại sau đăng nhập |
| 403 `ACCOUNT_NOT_LINKED` / `ACCOUNT_INACTIVE` | Trạng thái `not_linked` / `inactive`; xóa query cache; không hiện menu |
| 403 `PERMISSION_DENIED` | Invalidate `['auth','me']` (quyền có thể vừa bị thu hồi); trang hiện ForbiddenPage hoặc lỗi inline của action |
| 404 | NotFound trong vùng nội dung (scope "own" cũng trả 404) |
| 409 `CONFLICT` / `IDEMPOTENCY_*` | Giữ input; thông báo cạnh form; `IDEMPOTENCY_IN_PROGRESS` cho phép thử lại sau `Retry-After` với **cùng** key |
| 422 `VALIDATION_ERROR` | `toFieldErrors(details)` lấy phần tử cuối của `loc` (bỏ `body`/`query`) map vào `setError` của RHF; phần không map được hiện đầu form |
| 5xx / `NETWORK_ERROR` | ErrorState có Thử lại và `request_id` |

Thông điệp hiển thị lấy `message` từ server (tiếng Việt); frontend có bảng dịch dự phòng theo `code` cho lỗi mạng/không parse được.

### 5.4 TanStack Query

- `queries`: `staleTime` 30s; `retry`: không retry `ApiError` 4xx, tối đa 2 lần cho `NETWORK_ERROR`/5xx; `refetchOnWindowFocus` true.
- `mutations`: `retry: false` luôn. Lệnh idempotent chỉ retry khi người dùng bấm lại, với cùng key.
- Query key: `[module, resource, params]`, VD `['catalog','editions',{q,cursor}]`; auth là `['auth','me']`.
- Pagination: response `{data, nextCursor}` → `useInfiniteQuery` với `getNextPageParam: p => p.nextCursor ?? undefined`, `limit` mặc định 20 (max 100).

### 5.5 Idempotency-Key

`useIdempotencyKey(payload)` trả key `crypto.randomUUID()` sinh khi người dùng bắt đầu một ý định (VD mở dialog xác nhận mượn), giữ nguyên khi retry sau lỗi mạng/409 in-progress, sinh mới khi payload đổi (so bằng JSON chuẩn hóa) hoặc sau khi lệnh thành công. Key chỉ ở state React, không lưu storage. Nút pending ở UI không thay cho idempotency server.

## 6. Xác thực và điều hướng (FE01)

### 6.1 Adapter Keycloak

`keycloakClient.ts` bọc `keycloak-js`:

```ts
keycloak.init({
  onLoad: "check-sso",
  pkceMethod: "S256",
  silentCheckSsoRedirectUri: `${location.origin}/silent-check-sso.html`,
  checkLoginIframe: false,
});
```

- Token chỉ nằm trong instance keycloak-js (bộ nhớ). Reload trang dùng silent SSO để lấy lại phiên; không `localStorage`.
- `getToken()`: `await keycloak.updateToken(30)` rồi trả `keycloak.token`; refresh lỗi → `undefined` + sự kiện `session-expired`.
- `login(returnTo)`: `keycloak.login({ redirectUri: origin + returnTo })`. Chỉ gọi khi người dùng bấm nút.
- `logout()`: xóa query cache, rồi `keycloak.logout({ redirectUri: origin + "/" })`.
- `auth.init()` chạy trong `main.tsx` **trước** khi tạo router để keycloak-js xử lý fragment callback và xóa nó khỏi URL.
- Silent SSO dựa vào cookie Keycloak cùng site với app: dev `localhost:5173`/`localhost:8080` cùng site; production phải đặt Keycloak cùng site (ghi ở điểm mở INT03).

### 6.2 Trạng thái phiên

`AuthProvider` giữ máy trạng thái:

| Trạng thái | Vào khi | UI |
| --- | --- | --- |
| `initializing` | Đang `auth.init()` hoặc gọi `/auth/me` lần đầu | Skeleton shell, không flash menu |
| `anonymous` | Không có phiên SSO | Portal catalog dùng được; route cần phiên → LoginPage |
| `authenticated` | `/auth/me` 200 | Có `account`, `permissions: ReadonlySet<string>` |
| `not_linked` | `/auth/me` 403 `ACCOUNT_NOT_LINKED` | NotLinkedPage: "Tài khoản chưa được thư viện liên kết", nút Đăng xuất |
| `inactive` | 403 `ACCOUNT_INACTIVE` ở bất kỳ request nào | InactivePage, nút Đăng xuất, xóa cache |
| `expired` | Refresh token lỗi / 401 sau refresh | SessionExpiredPage, nút Đăng nhập lại (giữ `returnTo`) |
| `network_error` | `/auth/me` lỗi mạng/5xx | NetworkErrorPage có Thử lại; **không** chuyển sang login |

Không có đường tự động redirect sang Keycloak; mọi lần login là người dùng bấm nút → không thể có vòng lặp login. `useAuthMe` dùng `refetchOnWindowFocus` nên quyền bị gỡ hoặc account bị khóa phản ánh khi quay lại tab, và mọi 403 đều kích hoạt refetch (mục 5.3).

### 6.3 Guard

- `RequireSession`: không phải `authenticated` → render trang tương ứng trạng thái (không redirect).
- `RequirePermission code="…"`: thiếu quyền → ForbiddenPage trong shell. Chỉ để hiển thị; API vẫn quyết định.
- Đổi người dùng/quyền không được flash menu cũ: menu render từ `permissions` hiện tại, khi `initializing` hiện skeleton.

### 6.4 Route registry

`app/routes.ts` là nguồn duy nhất cho router, menu và breadcrumb:

```ts
type AppRoute = {
  path: string; title: string; group: "counter" | "catalog" | "manage" | "ops" | "portal";
  permission?: string;      // undefined = công khai
  functions: string[];      // F-code
  module: string;           // FE02…
  status: "planned" | "ready";
  lazy: () => Promise<{ Component: React.ComponentType }>;
};
```

Route lõi (mục menu theo nhóm Quầy/Danh mục/Quản lý/Vận hành của wireframe):

| Path | Nhóm | Permission | F | Module |
| --- | --- | --- | --- | --- |
| `/catalog`, `/catalog/:editionId` | portal | — (ẩn danh) | F01, F18 | FE02 |
| `/staff/checkout` | Quầy | `loan.checkout` | F07, F12 | FE04 |
| `/staff/returns` | Quầy | `return.create` | F08 | FE05 |
| `/staff/renewals` | Quầy | `loan.renew` | F09 | FE06 (phần gia hạn) |
| `/staff/readers`, `/staff/readers/:id` | Quầy | `reader.read` | F06, F12 | FE03 |
| `/staff/catalog` | Danh mục | `catalog.write` | F01–F05 | FE02 |
| `/staff/finance` | Quản lý | `finance.read` | F11 | FE07 |
| `/manager/charge-assessments` | Quản lý | `assessment.decide` | F11 | FE07 |
| `/staff/overdue` | Quản lý | `overdue.read` | F19 | FE09 |
| `/manager/reports` | Quản lý | `report.read` | F13, F20 | FE09 |
| `/login`, `/me` | — | phiên | F16 | FE01 |

- `/staff` → chuyển tới route `ready` đầu tiên người dùng có quyền; không có route staff nào → `/catalog`. `/me` hiển thị tài khoản và các mục portal (M0 chỉ thông tin `AuthContext`).
- Route `planned` chỉ xuất hiện trong menu ở build development (render `PlaceholderPage` ghi module và F-code); build production lọc bỏ. Nhóm "Vận hành" trống trong lõi nên không hiện.
- Mỗi module FE02+ đổi `status` thành `ready` trong PR của nó.

## 7. Motion (FE00.3)

- `ui/motion.css`: token `--motion-fast/base/panel/page`, `--ease-out/standard/exit` đúng [MOTION.md](../plan/frontend/MOTION.md#token-motion); class `.motion-enter` (opacity 0→1, y 4px, 180ms cho staff; 8px/280ms cho portal qua biến).
- Route transition: chỉ `<main>` nhận `.motion-enter` khi `location.key` đổi; không chờ exit. Back/refetch không replay (chỉ khi pathname đổi).
- Focus: sau điều hướng do người dùng, focus `<h1>` của trang (`tabIndex=-1`); có link "Bỏ qua tới nội dung".
- Dialog 240ms vào/120ms ra; toast 180ms; nav marker 180ms. Không `transition: all`; chỉ opacity/transform.
- `@media (prefers-reduced-motion: reduce)` đặt mọi duration 0 và bỏ transform/shimmer; feedback chữ/icon giữ nguyên.

## 8. Mock và chế độ chạy

- `test/msw/handlers.ts`: handler gõ kiểu theo `paths` (VD `http.get<never, never, components["schemas"]["AuthContext"]>("/api/v1/auth/me", …)`). M0 có `/auth/me`, `/health/*`; module sau thêm handler của mình.
- `test/msw/personas.ts`: 5 persona `READER`, `LIBRARIAN`, `MANAGER`, `SYSTEM_ADMIN`, `OPS_ADMIN` với permission **sao chép đúng** `ROLES` trong `apps/api/src/lib_management/identity/rbac_seed.py`; thêm persona `NOT_LINKED`, `INACTIVE`. Đầu file ghi nguồn và ngày sao chép; ở M0 đối chiếu thủ công trong review (xem điểm mở mục 11).
- Chế độ mock (`config.mock: true` + build mode `development` hoặc `e2e`): `main.tsx` `await import("./test/msw/browser")` và dùng `mockClient` (chọn persona trên LoginPage) thay keycloak-js. Nhánh import nằm sau `if (import.meta.env.MODE !== "production")` để Rollup loại bỏ khỏi bản production.
- CI kiểm `dist/` của `vite build` (production) không chứa chuỗi đánh dấu `__LIB_MOCK__` (đặt trong `mockClient.ts`).
- Mock thành công không thay nghiệm thu với backend thật (FE00, INT01).

## 9. Kế hoạch PR

Mỗi PR: nhánh `feature/<task-id>-<tên>`, Conventional Commit, mô tả nêu task FE/D-task, phụ thuộc, màn hình, trạng thái, motion đã áp dụng, ca kiểm thử và giới hạn xác minh ([quy trình team](../operations/team-development.md)).

| PR | Task | Nội dung | Nghiệm thu (test tự động) |
| --- | --- | --- | --- |
| 1 | FE00.1 | Scaffold `apps/web`, TS strict, ESLint/Prettier, Vitest; `config.ts` + `/config.json`; Node 24 trong Dev Container, cổng 5173; job CI `web` (lint, format check, typecheck, test, build); `configuration` yêu cầu `apps/web/package-lock.json`; `ci-result` needs `web` | `npm ci && npm run build` sạch; config thiếu trường/sai URL → trang lỗi cấu hình (unit); CI fail khi lockfile lệch |
| 2 | INT00.2 | `gen:api` + bước drift CI; `client.ts`, `errors.ts`, `queryClient.ts`, `idempotency.ts`, `authMe.ts`; MSW `/auth/me`; `lib/money.ts`, `lib/datetime.ts` | Middleware gắn Bearer + `X-Request-ID` hợp lệ; `ErrorResponse` → `ApiError` đúng field; body HTML 502 → `ApiError` không crash; 401 → refresh 1 lần rồi retry, lần 2 → sự kiện expired; 4xx không retry; `toFieldErrors` map `loc`; key idempotency giữ khi retry, đổi khi payload đổi; `formatVnd("123456789012")` không mất chính xác; UTC 17:30Z hiển thị ngày hôm sau ở Asia/Ho_Chi_Minh; drift: sửa `openapi.json` không regen → CI fail |
| 3 | FE00.2 / FE00.D1 | `tokens.css`, `base.css`, StaffShell/PortalShell tĩnh, component mục 4.3, `/dev/gallery` | Test contrast các cặp token ≥ ngưỡng (4.5:1 chữ, 3:1 control); component: label/`aria-describedby`/`aria-invalid`, Dialog trả focus về trigger, Escape bị chặn khi pending, StatusBadge luôn có chữ; ảnh chụp gallery desktop/tablet/mobile đính kèm PR |
| 4 | FE01.1–.3 | `keycloakClient`, `mockClient`, `AuthProvider`, guards, route registry, menu theo quyền, LoginPage và các trang trạng thái phiên, logout | Mỗi persona thấy đúng nhóm/mục menu; `READER` vào `/staff` → `/catalog`; `/auth/me` 403 NOT_LINKED/INACTIVE → trang tương ứng, không menu; 5xx/mạng → NetworkErrorPage, không gọi `login()`; 403 PERMISSION_DENIED → refetch `/auth/me`; không có ghi `localStorage`/`sessionStorage` (spy); route `planned` vắng trong build production |
| 5 | FE00.3, FE00.D2, FE01.D2, FE00.4/FE01.4 | `motion.css`, route transition, focus heading, skip link; Playwright e2e trên build `e2e` | Playwright (Chromium): đăng nhập persona → menu đúng; điều hướng toàn bằng bàn phím, focus thấy được; viewport 390px không cuộn ngang, drawer mở/đóng bằng phím; `reducedMotion: "reduce"` không có animation đang chạy; axe không có vi phạm serious/critical trên shell, gallery và các trang phiên; dist production không chứa `__LIB_MOCK__` |

PR 2 và PR 3 làm song song sau PR 1. PR 4 cần PR 2 (+ component tối thiểu của PR 3). PR 5 cần PR 3 và PR 4.

## 10. Kiểm thử và CI

- Unit/component: Vitest + jsdom + Testing Library, MSW `setupServer` trong `test/setup.ts`, `onUnhandledRequest: "error"`.
- E2E CI: Playwright chạy `vite preview` của build `e2e` (mock), chỉ Chromium. E2E với Keycloak + API thật chạy local trong Dev Container (không chạy trong CI ở M0) và ghi kết quả vào PR.
- Job CI `web` (trong `.github/workflows/ci.yml`, song song `quality`): `actions/setup-node` Node 24 cache npm → `npm ci` → `gen:api` + diff → `lint` → `format:check` → `typecheck` → `test` → `build` → kiểm marker mock → `playwright install --with-deps chromium` → `test:e2e`. Không secret, quyền `contents: read`.
- Sau PR 5: cập nhật FE00/FE01 trong [mục lục frontend](../plan/frontend/README.md) và AT16 trong [acceptance-matrix](../quality/acceptance-matrix.md) chỉ khi PR merge, kèm link CI run.

Kiểm tra local trong Dev Container (từ `apps/web`):

```bash
npm ci
npm run gen:api && git diff --exit-code src/api/schema.d.ts
npm run lint && npm run format:check && npm run typecheck
npm test
npm run build
npm run dev            # http://localhost:5173, API ở :8000, Keycloak ở :8080
```

Smoke thủ công với hệ thống thật sau PR 4: chạy API (`uv run --locked uvicorn lib_management.main:create_app --factory`, xem [README API](../../apps/api/README.md)), `uv run --locked python ../../.devcontainer/keycloak/create_dev_users.py --link` (từ `apps/api`), đăng nhập bằng `librarian.dev` → thấy nhóm Quầy/Danh mục; `manager.dev` → nhóm Quản lý; `reader.dev` → về `/catalog`; khóa account bằng SQL (`status='LOCKED'`) rồi focus lại tab → InactivePage; user Keycloak chưa `--link` → NotLinkedPage.

## 11. Điểm mở

| Mã | Nội dung | Ảnh hưởng M0 |
| --- | --- | --- |
| — | F14 (quy định) ngoài lõi nhưng BE02/checkout cần PolicyVersion ACTIVE: tạo bằng seed/CLI hay mở FE09 phần policy sớm | Không; quyết định trước M2 |
| — | Portal lõi: `/me/loans` (F17), giữ chỗ (F10), thông báo (F24) đều phase 2 → portal lõi chỉ có catalog và `/me` cơ bản | Không; xác nhận với chủ dự án |
| — | `/staff/renewals` cần endpoint tra cứu loan theo barcode/độc giả; OpenAPI hiện chỉ có `GET /loans/{id}` và `GET /readers/{id}/history` (F17) | Không; giải quyết ở spec FE06/BE08 |
| — | Backend chưa có `seed-rbac --dry-run --json` để đối chiếu persona tự động | Đối chiếu thủ công trong review PR 4 |
| — | Hosting, reverse proxy, CSP, `config.json` production, Keycloak cùng site cho silent SSO | Không; INT03 |
| — | Version/digest Node 24 và các gói npm | Chọn khi làm PR 1 |
