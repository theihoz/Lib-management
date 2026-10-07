# Docker và CI/CD cho FastAPI

Backend là Python 3.13 + FastAPI + PostgreSQL 17. Chỉ có health endpoints;
chưa có schema nghiệp vụ, CRUD hoặc migration. Các file web/Nginx được giữ làm
template chưa hoạt động và không tham gia Compose hoặc CI backend.

## Local với Docker

Yêu cầu Docker Engine/Desktop và Docker Compose.

```bash
cp .env.example .env
# Sửa POSTGRES_PASSWORD trước khi chạy.
docker compose up --build
# Hoặc chạy nền:
docker compose up --build -d --wait
docker compose ps
docker compose logs -f api db
docker compose down
```

API trên `127.0.0.1:8000`, tài liệu tại `/docs`; DB trên `127.0.0.1:5432`.
Có thể đổi API_PORT và POSTGRES_PORT. Trong mạng container, API dùng `db:5432`.
Mật khẩu chứa `$` phải được đặt trong dấu nháy đơn trong `.env` để giữ nguyên
ký tự. POSTGRES_PASSWORD bắt buộc, được truyền thành DB_PASSWORD riêng;
SQLAlchemy URL.create xử lý mật khẩu có `@`, `:`, `/`, khoảng trắng và `$`.

Project mặc định `lib-management`, volume `pgdata` (tên thực tế
`lib-management_pgdata`). `down` giữ volume; tránh `down -v` khi cần giữ dữ liệu.
Đổi mật khẩu trong env không đổi mật khẩu role của DB đã khởi tạo: cập nhật
role trong PostgreSQL trước khi đổi cấu hình. Không nâng major DB tự động.

Stage dev chỉ bind `apps/api/src` vào `/app/src`, reload nguồn Python; thư viện
trong `/opt/venv` không bị mount host che mất. Sau khi đổi lockfile, rebuild API.
API chạy UID/GID 10001, drop capabilities, no-new-privileges và tmpfs `/tmp`.
DB healthcheck thành công trước khi API khởi động.

## Chạy API bằng uv trên host

Cài Python 3.13 và uv 0.12.21, chạy DB với Compose rồi:

```bash
docker compose up -d --wait db
cd apps/api
uv sync --locked
# Dùng mật khẩu đã cấu hình cho DB; uv không tự đọc .env của repository.
export DB_PASSWORD='your-local-password'
export DB_USER=lib_dev DB_NAME=lib_management
uv run --locked uvicorn lib_management.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Để cập nhật dependency có chủ đích, sửa pyproject.toml, chạy `uv lock`, xem diff
lockfile, rồi `uv sync --locked`. Không sửa uv.lock thủ công.
Quality commands có trong [API README](../../apps/api/README.md).

## Production image và health

```bash
docker build --target production -f docker/api.Dockerfile -t lib-management-api:local .
```

Build context là repo root. Dockerignore loại env, Git, venv, cache, docs và
worktrees. Các stage deps/build dùng `uv sync --locked`, build wheel; production
chỉ chứa runtime dependencies và wheel cài noneditable trong `/opt/venv`,
không chứa uv, source bind mount hoặc dev tools. Process Uvicorn exec-form,
factory `lib_management.main:create_app`, một worker, `0.0.0.0:8000`, không reload.
Mật khẩu chỉ được cung cấp lúc chạy container, không qua build args.

Python `3.13-slim-bookworm`, PostgreSQL `17-bookworm`, uv `0.12.21` được pin
multi-platform index digest trong Dockerfile/Compose. Cập nhật digest cần đọc
metadata registry, review thay đổi và build/smoke lại, không dùng latest.

`GET /health/live` trả 200 `{"status":"ok"}` độc lập DB.
`GET /health/ready` chạy SELECT 1, trả 200 `{"status":"ready"}` hoặc
503 `{"status":"not_ready"}`. Readiness chưa kiểm tra 38 bảng hoặc revision
migration. DB connect timeout 2 giây, statement timeout 2000 ms.

## CI và publish

CI `.github/workflows/ci.yml` chạy khi PR, push main, dispatch hoặc được gọi
qua workflow_call. Backend luôn bắt buộc: thiếu pyproject.toml, uv.lock,
main.py hoặc .python-version làm job configuration thất bại. Không có detector
Node hoặc chế độ bootstrap. Ba job configuration → quality → container phải
đều thành công để required check `ci-result` pass; skipped/cancelled/failure
đều làm check thất bại. Concurrency của CI dùng prefix riêng với caller publish.

Quality dùng Python từ .python-version và uv 0.12.21, `uv sync --locked --group dev`,
Ruff check/format, mypy, 9 unit tests độc lập DB, 3 integration tests, build wheel.
PostgreSQL service disposable dùng cùng digest PostgreSQL 17 như Compose,
credentials fixture công khai, không có volume hoặc secret production. Integration
chỉ chạy khi `RUN_DB_INTEGRATION=1` và DB_HOST/DB_PORT/DB_USER/DB_NAME/DB_PASSWORD
trỏ vào fixture riêng; mặc định các tests này skip để unit tests không cần DB.
CI bật rõ flag và chạy integration file riêng, nên fixture hỏng làm CI fail.
Tests kiểm tra SELECT 1/readiness thành công, sai mật khẩu và port không lắng nghe
trả 503 trong dưới 5 giây, liveness vẫn 200. Sau quality, container chỉ build
production image, không push. PR từ fork chỉ có contents/read, checkout không giữ
credentials; không pull_request_target hoặc production secrets.
Dependabot theo dõi uv ở apps/api, github-actions và Dockerfile.

## Publish API thủ công lên GHCR

Workflow `Publish API image` (`.github/workflows/publish-images.yml`) chỉ có
`workflow_dispatch`, không có input ref hoặc shell. Chọn default branch trong
GitHub Actions khi chạy; job branch từ chối mọi ref khác. Job quality gọi reusable
CI trong cùng commit `github.sha`, không nhận secret production. Publish chỉ chạy
khi quality thành công, gồm cả production image build và required check ci-result.
Concurrency publish có prefix `api-image-publish`, riêng với `python-ci`.

Job publish dùng environment `image-publish`; chỉ job này có `packages: write`,
các job khác chỉ `contents: read`. Checkout pin action SHA và ref `github.sha`,
không giữ credentials. Workflow build API production trước khi login; build lỗi
không thể tới login/push. Login GHCR dùng GITHUB_TOKEN qua `--password-stdin`,
logout chạy với `always()`. Không build hoặc publish web.

Tag là `ghcr.io/<owner viết thường>/lib-management-api:sha-<full commit SHA>`
(với repository hiện tại: `ghcr.io/theihoz/lib-management-api:sha-<full commit SHA>`),
không dùng `latest`. OCI labels `org.opencontainers.image.source` và
`org.opencontainers.image.revision` ghi repository URL và commit SHA. Job summary
ghi tag và RepoDigest sau push; dùng digest để chọn chính xác image cho deployment.
Việc publish cần yêu cầu riêng của người dùng; lượt triển khai này không chạy
workflow trên GitHub, login hoặc push registry.

Maintainer phải tạo/cấu hình environment `image-publish` trên GitHub, đặt required
reviewers và deployment branch rule chỉ default branch trước lần publish thật.
Cấu hình branch protection/ruleset cho default branch: required CI check
`ci-result`, review PR và hạn chế bypass theo chính sách nhóm. Những cài đặt này
nằm ngoài repository; YAML không chứng minh reviewers hoặc branch protection đã bật.
Kiểm tra quyền GITHUB_TOKEN được phép publish GHCR và package gắn với repository.

## Trước production deployment

Publish package chưa tạo server hoặc triển khai production. Cần hoàn thành:

- Chọn hosting/container runtime, network, tài nguyên, health probes và cách rollback
  về image digest đã biết; chưa chốt hosting, frontend hoặc auth provider.
- Cấu hình domain, TLS/HTTPS và reverse proxy/load balancer, gia hạn chứng chỉ.
- Cấp runtime secrets bằng secret manager của hosting; truyền DB_HOST, DB_PORT,
  DB_USER, DB_NAME, DB_PASSWORD lúc chạy, không đưa mật khẩu vào Git, image hoặc log.
- Tạo DB role ứng dụng riêng với quyền tối thiểu, tách role migration/admin;
  hạn chế network truy cập PostgreSQL và cấu hình kết nối theo hosting.
- Khi có schema nghiệp vụ, thêm Alembic migrations, review và chạy migration bằng
  bước riêng trước rollout; bổ sung readiness kiểm tra revision phù hợp.
- Lập lịch backup, retention và vị trí lưu an toàn; thử restore, xác định RPO/RTO
  và kế hoạch rollback dữ liệu trước thay đổi schema. Volume local không thay backup.

## Nguồn kỹ thuật

- [FastAPI containers](https://fastapi.tiangolo.com/deployment/docker/)
- [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/)
- [Compose services](https://docs.docker.com/reference/compose-file/services/)

Readiness uses dedicated async psycopg connections, with at most four active probes.
A 2-second client deadline includes admission, connection establishment and reads.
On timeout the connection is closed before task cancellation, avoiding a stalled
server cancellation handshake. Health handlers are async; liveness uses no DB
or synchronous worker. The SQLAlchemy engine remains available for future work
and is disposed at shutdown, but its pool is not used for health probes.
Isolated builds pin the reviewed hatchling backend to 1.32.4; transitive build
dependencies are still resolved by the isolated builder (not fully locked).
