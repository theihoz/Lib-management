# Lib-management — Quản lý thư viện

Phần mềm quản lý thư viện: quầy mượn/trả cho nhân viên và portal cho độc giả.
Monorepo gồm backend FastAPI và frontend React, phát triển trong một Dev Container chung.

> **Demo hay bản thật?** Trang [GitHub Pages](https://theihoz.github.io/Lib-management/) chỉ là
> **bản demo**: dữ liệu giả lập trong trình duyệt, chọn vai trò để đăng nhập, không có database.
> Muốn dùng **bản thật** (PostgreSQL, Keycloak, API, worker) trên máy cá nhân, chạy một lệnh:
> `scripts/local.sh up` — xem [Bắt đầu](#bắt-đầu).

| Phần | Công nghệ | Thư mục |
| --- | --- | --- |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17; dependencies khóa bằng `uv.lock` | [`apps/api`](apps/api/README.md) |
| Frontend | React 19, TypeScript, Vite; dependencies khóa bằng `package-lock.json` | [`apps/web`](apps/web/README.md) |
| Đăng nhập | Keycloak OIDC, Authorization Code + PKCE; quyền lưu trong DB ứng dụng | `.devcontainer/keycloak` |

## Trạng thái hiện tại (mốc M0)

**Đã có**

- Backend nền tảng ([spec M0 backend](docs/specs/M0-backend-foundation.md)): hợp đồng lỗi
  `ErrorResponse`, request ID, cursor pagination, Unit of Work, idempotency, audit log,
  outbox và worker job có lease/retry; migration 9 bảng identity/platform.
- Xác thực: kiểm tra JWT Keycloak, Account ACTIVE và 39 permission/5 role từ DB;
  endpoint `GET /api/v1/auth/me`; CLI `seed-rbac`, `bootstrap-admin`.
- Lõi thư viện (code, CI xanh; chưa nghiệm thu E2E): danh mục/bản sao/vị trí, độc giả và thẻ,
  eligibility, mượn/trả/gia hạn, phí (assessment, thu, miễn, đảo), quá hạn, báo cáo + CSV
  qua worker và storage private, policy có phiên bản (F14); CLI `link-reader-account`.
  66/85 operation OpenAPI được phục vụ; 19 còn lại thuộc phase 2.
- Frontend ([spec M0 frontend](docs/specs/M0-frontend-foundation.md)): Keycloak PKCE, client sinh từ
  OpenAPI, route/menu theo permission, 36 màn thuộc lõi; cấu hình runtime `/config.json` kiểm tra bằng Zod.
- GitHub Pages triển khai **bản demo** tĩnh (mock API trong trình duyệt) sau khi toàn bộ CI đạt;
  bản thật chạy local bằng `scripts/local.sh up`.
- Dev Container có Python, uv, Node 24, PostgreSQL và Keycloak dev; CI cho cả backend và frontend.

**Chưa có**

- Phase 2: giữ chỗ F10, bìa F15, lịch sử portal F17, quản trị tài khoản F21, nhập/thanh lý F22,
  backup/restore F23, thông báo F24.
- Playwright E2E với Keycloak + API + PostgreSQL thật, Lighthouse và benchmark NFR
  ([audit](docs/quality/2026-11-03-spec-conformance-audit.md)).
- React Hook Form (quyết định công nghệ); form hiện dùng Zod trực tiếp.
- Hosting/deployment production chưa được quyết định; publish image không có nghĩa là đã triển khai.

Phạm vi 10 tuần: F01–F09, F11–F14, F16, F18–F20; phần còn lại thuộc phase 2
([quyết định 03/11/2026](docs/plan/decisions.md#quyết-định-03112026--phạm-vi-lõi-10-tuần)).
Quy tắc C01–C09 đã được chủ dự án đồng ý áp dụng.

## Bắt đầu

```bash
git clone https://github.com/theihoz/Lib-management.git
cd Lib-management
```

Chọn một trong ba cách. Chỉ chạy một cách tại một thời điểm vì chúng dùng chung cổng
5173/8000/8080.

| Cách | Dùng khi | Cần cài |
| --- | --- | --- |
| 1. Bản thật bằng một lệnh | Dùng thử/demo đầy đủ với dữ liệu thật trên máy | Docker |
| 2. Dev Container | Viết code backend + frontend | Docker, VS Code + Dev Containers |
| 3. Chỉ backend bằng Compose | Thử API, không cần đăng nhập | Docker |

### Cách 1 — Bản thật trên máy cá nhân (một lệnh)

```bash
scripts/local.sh up
```

Lệnh tự tạo `.env` với mật khẩu ngẫu nhiên, rồi khởi động PostgreSQL, Keycloak, migration,
seed quyền + 5 tài khoản, API, worker và bản build production của web. Khi báo xong:

| Dịch vụ | Địa chỉ |
| --- | --- |
| Ứng dụng | <http://localhost:5173> |
| API + Swagger | <http://localhost:8000/docs> |
| Keycloak | <http://localhost:8080> |

Đăng nhập bằng `librarian.dev`, `manager.dev`, `admin.dev`, `ops.dev` hoặc `reader.dev`;
mật khẩu là `KEYCLOAK_DEV_USER_PASSWORD` trong `.env`. Dừng bằng `scripts/local.sh down`
(giữ dữ liệu). Windows: chạy trong Git Bash hoặc WSL2.

Toàn bộ lệnh (`status`, `logs`, `token`, `reset`), đổi cổng và xử lý lỗi:
[hướng dẫn chạy bản thật](docs/operations/local-real.md).

### Cách 2 — Dev Container (khuyến nghị để code)

Cài Docker Desktop/Engine, Git, VS Code với extension Dev Containers (Windows: Docker Desktop
Linux containers trên WSL2). Mở thư mục repository, chọn **Dev Containers: Rebuild and Reopen
in Container**. Container đã có Python, uv, Node 24 và chạy sẵn `uv sync` + `npm ci`.

Trong terminal container:

```bash
# Backend: migration, quyền, user Keycloak dev
cd apps/api
uv run --locked alembic upgrade head
uv run --locked python -m lib_management.cli seed-rbac
uv run --locked python ../../.devcontainer/keycloak/create_dev_users.py --link
uv run --locked uvicorn lib_management.main:create_app --factory --host 0.0.0.0 --port 8000 --reload

# Frontend (terminal khác)
cd apps/web
npm run dev
```

Địa chỉ giống Cách 1; frontend là Vite dev server có hot reload.
Chi tiết, cách lấy token thử và xử lý lỗi: [hướng dẫn Dev Container](.devcontainer/README.md).

### Cách 3 — Chỉ chạy backend bằng Compose

```bash
cp .env.example .env
# Đổi POSTGRES_PASSWORD trong .env trước khi chạy.
docker compose up --build -d --wait
```

Compose chạy `db` → `migrate` (một lần) → `api` + `worker`, không có Keycloak và web.
`OIDC_ISSUER` để trống thì route cần đăng nhập trả 503, health vẫn chạy.
Dùng chung database với Cách 1. Có thể [chạy API trên host](apps/api/README.md) bằng uv và DB Compose.

### Bản demo trên GitHub Pages

Workflow `Deploy web to GitHub Pages` build `npm run build:demo` và ghi `config.json` với
`mock: true`: mọi lời gọi API được trả lời ngay trong trình duyệt theo OpenAPI, đăng nhập bằng
cách chọn vai trò. Bản build production (`npm run build`) loại bỏ hoàn toàn code mock; CI kiểm
tra điều này. Nếu đặt biến repository `PAGES_OIDC_URL` (và `PAGES_API_BASE_URL`), Pages build
bản production trỏ tới API đó thay vì demo.

## Kiểm tra trước khi mở PR

```bash
# apps/api
uv run --locked ruff check . && uv run --locked ruff format --check . && uv run --locked mypy src
uv run --locked pytest

# apps/web
npm run lint && npm run format:check && npm run typecheck && npm test && npm run build
```

CI (`.github/workflows/ci.yml`) chạy các bước trên, thêm integration test PostgreSQL,
migration round trip và build production image. Check bắt buộc của `main` là `ci-result`.
Workflow `Publish API image` xuất bản GHCR thủ công từ default branch sau CI cùng SHA.

## Tài liệu

- [Spec triển khai](docs/specs/README.md) — bản đủ chi tiết để code từng mốc
- [Kế hoạch backend/frontend/tích hợp](docs/plan/README.md), [quyết định](docs/plan/decisions.md)
- [Thiết kế: DB, OpenAPI, quyền, identity, kiến trúc](docs/design/README.md)
- [Onboarding, chia việc, Git và review](docs/operations/team-development.md)
- [Chạy bản thật trên máy cá nhân](docs/operations/local-real.md)
- [Docker, biến môi trường, CI/CD](docs/operations/containers-ci.md)
- [Bối cảnh và phạm vi dự án](PROJECT-CONTEXT.md)
- [Bằng chứng kiểm tra đã thực hiện](docs/operations/verification.md)

## Cấu trúc repository

```text
.devcontainer/       Workspace Linux cho team: Python, Node, PostgreSQL, Keycloak dev
.github/             CI, publish image, Dependabot, payload bảo vệ main
apps/api/            FastAPI: src/lib_management, migrations, tests, uv.lock
apps/web/            React + Vite: src, public/config.json, package-lock.json
docker/              Dockerfile API, image web (nginx), cấu hình nginx
compose.yaml         db + migrate + api + worker local
compose.local.yaml   Thêm Keycloak, seed, web production cho bản thật local
scripts/local.sh     Một lệnh chạy/dừng/reset bản thật local
PROJECT-CONTEXT.md   Mục đích, phạm vi và quyết định hiện hành
docs/
  specs/             Spec triển khai theo mốc (M0 backend, M0 frontend)
  design/            DOCX, DB, API/OpenAPI, quyền, identity, events, bảo mật
  plan/              Kế hoạch module backend/frontend/tích hợp, wireframe, motion
  diagrams/          UML (diagrams.net)
  quality/           Ma trận nghiệm thu F01–F24
  operations/        Onboarding, Docker/CI, bảo vệ main, bằng chứng kiểm tra
  archive/           Kế hoạch và nguồn tham khảo lịch sử
```

Không ghi secret vào repository, tài liệu hoặc image; credentials chỉ cung cấp lúc chạy.
