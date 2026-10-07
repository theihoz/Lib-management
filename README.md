# Phần mềm quản lý thư viện

Backend dùng Python 3.13, FastAPI và PostgreSQL 17. [Báo cáo thiết kế chuẩn](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit) giữ C01–C09; schema 38 bảng được triển khai sau.

## Chạy local

```bash
cp .env.example .env
# Sửa POSTGRES_PASSWORD trong .env.
docker compose up --build
```

API: http://localhost:8000; OpenAPI: http://localhost:8000/docs.
Compose chạy API có reload và PostgreSQL; DB chỉ mở cổng localhost.
`docker compose down` giữ dữ liệu trong volume `pgdata`.

Có thể chạy API bằng uv trên host theo [apps/api/README.md](apps/api/README.md).
[Hướng dẫn Docker và CI/CD](docs/operations/containers-ci.md) mô tả cấu hình,
lockfile và giới hạn deployment. Các file frontend/Nginx là template chưa hoạt động.
Readiness chỉ kiểm tra kết nối PostgreSQL, chưa kiểm tra 38 bảng.
Production deployment chưa được cấu hình.

Publish API lên GHCR bằng workflow thủ công `Publish API image` từ default branch,
sau CI trên cùng SHA. Tag `sha-<full commit SHA>` và digest được ghi trong job summary.
Maintainer cần cấu hình reviewers của environment `image-publish` và branch protection
trên GitHub trước publish thật. Publish image chưa triển khai máy chủ; xem checklist
hosting, HTTPS, runtime secrets, migrations và backup trong hướng dẫn vận hành.
[PROJECT-CONTEXT.md](PROJECT-CONTEXT.md) ghi phạm vi và các quyết định chưa chốt.
