# Lib-management — Quản lý thư viện

Backend **Python 3.13 + FastAPI + PostgreSQL 17**, dependencies khóa bằng `uv.lock`.
Hiện có scaffold, health endpoints, Docker và CI; chưa có CRUD, schema nghiệp vụ,
đăng nhập hoặc giao diện hoàn chỉnh. C01–C09 đã được người dùng đồng ý áp dụng.

## Bắt đầu cho thành viên mới

```bash
git clone https://github.com/theihoz/Lib-management.git
cd Lib-management
```

**Code trong Dev Container (khuyến nghị):** cài Docker Desktop/Engine, Git,
Python host >=3.9 và VS Code với extension Dev Containers. Mở thư mục repository,
chọn **Dev Containers: Reopen in Container**. Toàn bộ dự án được mount vào workspace;
Python, uv, Git và dependencies Linux có sẵn. Trong terminal container:

```bash
cd apps/api
uv run --locked uvicorn lib_management.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

Swagger: <http://localhost:8000/docs>. Xem [hướng dẫn Dev Container](.devcontainer/README.md).

**Chỉ chạy app bằng Compose:**

```bash
cp .env.example .env
# Đổi POSTGRES_PASSWORD trong .env trước khi chạy.
docker compose up --build -d --wait
```

Compose này chạy API tự động, khác workspace Dev Container. Chọn một cách chạy
trên cổng 8000; hai stack có volume PostgreSQL riêng. `docker compose down` giữ dữ liệu.
Có thể [chạy API trên host](apps/api/README.md) bằng uv và DB Compose.

## Tài liệu cho team

- [Onboarding, chia công việc, Git và review](docs/operations/team-development.md)
- [Docker, biến môi trường, dữ liệu, CI/CD, xử lý lỗi](docs/operations/containers-ci.md)
- [Hợp đồng hạ tầng hiện hành](docs/operations/fastapi-infrastructure-spec.md)
- [Thiết kế DOCX, UML một trang, PDF và kế hoạch đã có](docs/README.md)
- [Bối cảnh và phạm vi dự án](PROJECT-CONTEXT.md)
- [Bằng chứng kiểm tra đã thực hiện](docs/operations/verification.md)

CI kiểm tra source/lock, lint, format, types, tests, wheel và production image.
Workflow `Publish API image` xuất bản GHCR thủ công từ default branch sau CI cùng SHA;
**publish image chưa triển khai server**. Frontend, auth provider và hosting chưa chốt.
Maintainer cần bật review PR, required check `ci-result` và environment `image-publish`
trên GitHub. Bảo vệ main đang bị GitHub Free/private chặn; xem [trạng thái và cấu hình rule](docs/operations/branch-protection.md). Environment image-publish chưa được xác nhận đã bật.

## Cấu trúc repository

```text
.devcontainer/       Workspace Linux cho team; mount toàn bộ project
.github/             CI, publish, Dependabot, PR template và payload bảo vệ main
apps/api/            FastAPI src, tests, pyproject.toml, uv.lock
docker/              Dockerfile API dev/build/production
compose.yaml         Chạy API + PostgreSQL local
PROJECT-CONTEXT.md   Mục đích, phạm vi và quyết định hiện hành
docs/
  design/            DOCX thiết kế đã có
  diagrams/          UML một canvas, chỉnh sửa bằng diagrams.net
  ui/                Prototype và design tokens (chưa là frontend app)
  operations/        Onboarding, Docker/CI, bảo vệ main, bằng chứng kiểm tra
  archive/           Kế hoạch và nguồn tham khảo lịch sử
  source-manifest.json  Nguồn, thời điểm tải và hash binary
```
