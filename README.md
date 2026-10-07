# Phần mềm quản lý thư viện

Lib-management đang ở giai đoạn thiết kế và chuẩn bị code. [Báo cáo thiết kế chuẩn](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit) đã áp dụng C01–C09.

## Môi trường local

```bash
cp .env.example .env
# Sửa POSTGRES_PASSWORD trong .env.
docker compose up -d --wait db
```

Compose mặc định chỉ chạy PostgreSQL. API/web chưa có mã nguồn; profile `app` được bật khi có đủ hai package trong `apps/api`, `apps/web`.

Template hiện theo TypeScript, React/Vite, NestJS, PostgreSQL. Backend N02 còn chờ xác nhận; không xem template NestJS là quyết định đã chốt.

## CI/CD và Docker

- [Hướng dẫn container, hợp đồng app và CI/CD](docs/operations/containers-ci.md)
- [Kế hoạch triển khai hạ tầng](docs/superpowers/plans/2026-10-07-ci-cd-docker.md)
- CI kiểm tra cấu hình ngay; quality/build app chỉ chạy khi mã nguồn đáp ứng hợp đồng.
- Publish GHCR thủ công trên default branch sau quality gates; chưa deploy lên máy chủ.
