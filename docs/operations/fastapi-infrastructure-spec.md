# Đặc tả hạ tầng FastAPI

Ngày: 2026-10-07. Trạng thái: hợp đồng hạ tầng hiện hành; đã triển khai scaffold.

## Nguồn và phạm vi

- Người dùng chọn Python + FastAPI + PostgreSQL, thay lựa chọn backend NestJS trong template chưa commit.
- [Báo cáo thiết kế](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit): giữ C01–C09 và tên dữ liệu chuẩn. 38 bảng/288 trường được triển khai ở nhiệm vụ nghiệp vụ sau.
- Chuẩn bị một API tối thiểu chạy được, PostgreSQL local, Docker dev/production và GitHub Actions. Chỉ có health endpoints; không tạo CRUD, đăng nhập, schema nghiệp vụ hay frontend.
- Frontend và reverse proxy chưa được chọn; template Node/Nginx không hoạt động đã được dọn. Tài liệu DOCX/UML/PDF được giữ làm nguồn tham khảo.
- Chưa có đích deploy; CD của mốc này là publish image GHCR thủ công sau CI thành công.

## Hợp đồng kỹ thuật

| Thành phần | Quyết định |
| --- | --- |
| Python | 3.13; requires-python = >=3.13,<3.14; .python-version = 3.13 |
| Package | apps/api/pyproject.toml và uv.lock; package src/lib_management |
| Runtime | FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy 2.x, psycopg 3.x |
| Dependencies | Chốt phiên bản cụ thể bằng uv.lock tại triển khai; uv và action pin release/SHA đã kiểm tra từ upstream, image pin digest |
| Công cụ CI | Ruff check/format, mypy, pytest, build wheel |
| PostgreSQL | Giữ major 17 và volume hiện có; không nâng major, không xóa volume |
| API | api:8000; host mặc định 127.0.0.1:8000; prefix nghiệp vụ tương lai /api/v1 |
| DB | db:5432; host mặc định 127.0.0.1:5432 |
| Liveness | GET /health/live → 200, {"status":"ok"}; không gọi DB |
| Readiness | GET /health/ready → 200, {"status":"ready"} khi SELECT 1 thành công; lỗi DB → 503, {"status":"not_ready"} |
| Timeout | Readiness client deadline = 2 giây, gồm chờ admission/connect/read; tối đa 4 probe; DB connect_timeout = 2 giây; statement_timeout = 2000 ms |
| Cấu hình | DB_HOST, DB_PORT, DB_USER, DB_NAME, DB_PASSWORD; password bắt buộc, không đưa vào log/response |
| App factory | create_app(settings: Settings \| None = None) -> FastAPI |
| Image | dev/build/production; runtime UID/GID 10001; một process Uvicorn, bind 0.0.0.0:8000 |
| Publish | ghcr.io/theihoz/lib-management-api:sha-<full commit SHA>; ghi digest; không latest |

Readiness hiện chỉ chứng minh kết nối DB. Khi có migration nghiệp vụ, bổ sung kiểm tra revision Alembic trong một nhiệm vụ riêng; không tuyên bố schema đã sẵn sàng trong mốc này. Alembic migration chạy bằng bước riêng, không chạy tự động trong mỗi replica.

## Tiêu chí hoàn thành sau triển khai

1. Docker Compose khởi động API và DB bằng một lệnh, API reload khi sửa src; DB giữ dữ liệu khi restart.
2. Runtime production không root, không bind source, không có secret trong image; Dockerignore loại .env, .git, .venv và tài liệu khỏi context.
3. Health contract có kiểm tra thành công/thất bại; invalid config dừng startup, lỗi DB không làm liveness thất bại.
4. CI PR/push main không skip vì thiếu web; thiếu code/lockfile hoặc lock stale phải fail. CI không có packages/write và không dùng secret production.
5. CI có PostgreSQL disposable riêng; lint, format, typecheck, tests, wheel và production image build phải thành công trước publish.
6. Publish chỉ workflow_dispatch từ default branch, chất lượng kiểm tra cùng SHA, chỉ job publish có packages/write; environment image-publish do maintainer cấu hình reviewers nếu cần.
7. Tài liệu hướng dẫn chạy, cập nhật dependency, health, dữ liệu volume, publish và giới hạn deployment khớp cấu hình thực tế.

## Nguồn kỹ thuật

- [FastAPI containers](https://fastapi.tiangolo.com/deployment/docker/): build từ Python image, dùng exec-form startup.
- [uv Docker integration](https://docs.astral.sh/uv/guides/integration/docker/): cache dependencies và dùng môi trường ảo trong image.
- [uv locking/sync](https://docs.astral.sh/uv/concepts/projects/sync/): dùng --locked khi đã có toàn bộ manifest để phát hiện lock stale; --frozen không kiểm tra độ mới của lock.
- [SQLAlchemy PostgreSQL](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html): psycopg dialect và URL.create để xử lý ký tự đặc biệt trong password.

## Dev Container cho team

`.devcontainer/compose.yaml` tách workspace và PostgreSQL khỏi Compose app. Toàn bộ repository được bind mount; Git worktree mount thêm metadata chung. Dependencies workspace Linux ở `/home/developer/.venv`, không dùng venv host. Workspace dùng đường dẫn cố định `/workspaces/lib-management`; initialize chạy qua Docker để không phụ thuộc Python host trên Windows. Xem [hướng dẫn team](team-development.md) và [Docker/CI](containers-ci.md).

Build backend pin Hatchling 1.32.4; dependencies build gián tiếp vẫn do isolated builder giải quyết, chưa bảo đảm build tái lập hoàn toàn.
