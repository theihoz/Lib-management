# CI/CD và Docker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chuẩn bị môi trường PostgreSQL local, container API/web và GitHub Actions trước khi viết nghiệp vụ.

**Architecture:** Compose mặc định chạy PostgreSQL; profile `app` bật API và web khi đã có mã nguồn. CI phân biệt bootstrap với ứng dụng có đủ hợp đồng; workflow thủ công kiểm tra chất lượng và build cả hai image trước khi publish GHCR. Chưa có đích triển khai nên xuất image là bước CD được chuẩn bị, chưa phải triển khai máy chủ.

**Tech Stack:** GitHub Actions, Docker Compose, PostgreSQL 17, Node.js 24, npm; template NestJS + React/Vite theo README. Backend N02 chưa được chốt; nếu chọn .NET phải đổi template API trước khi kích hoạt.

**Spec:** [Báo cáo thiết kế Lib-management](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit), mục 9, 13, 14 và 17.2; `README.md`; `docs/operations/containers-ci.md` là hợp đồng hạ tầng cụ thể của kế hoạch này.

## Global Constraints

- C01–C09 đã áp dụng; nhiệm vụ hạ tầng không thay đổi quy định nghiệp vụ.
- PostgreSQL theo nguồn thiết kế; migration 38 bảng/288 trường thuộc bước code sau.
- N02 chưa chốt framework API và nhà cung cấp xác thực.
- Không khôi phục các tài liệu đang bị xóa trong working tree.
- Không đưa secret thật vào Git, build argument hoặc image; cổng local chỉ bind 127.0.0.1.
- Không tự deploy, push Git hoặc chạy kiểm thử trong lần chuẩn bị này; các bước kiểm tra dưới đây dành cho lần người dùng yêu cầu xác minh.

## Review Focus

- App vắng hoàn toàn: CI thông báo bootstrap, không tuyên bố đã build app (Task 2).
- App chỉ có một phần hoặc thiếu lock/script: CI thất bại thay vì bỏ qua (Task 2).
- PostgreSQL chưa sẵn sàng: API chờ healthcheck; dữ liệu sống qua restart (Task 1).
- PR từ fork: không có quyền packages/write hay secret publish (Task 3).
- Build một image lỗi: không publish image nào; image gắn SHA đầy đủ, không dùng latest (Task 3).

## File Structure

| File | Trách nhiệm |
| --- | --- |
| `compose.yaml`, `.env.example` | Môi trường local, profile app, volume dữ liệu |
| `docker/api.Dockerfile`, `docker/web.Dockerfile` | dev/build/production stages |
| `docker/nginx.conf` | SPA fallback và proxy API nội bộ |
| `.dockerignore`, `.nvmrc` | Build context và phiên bản Node |
| `scripts/ci/app-contract.mjs` | Phát hiện bootstrap/app-ready và yêu cầu strict |
| `.github/workflows/ci.yml` | Compose config; app quality và image build nếu ready |
| `.github/workflows/publish-images.yml` | Kiểm tra, build và publish GHCR thủ công |
| `.github/dependabot.yml` | Cập nhật action SHA và base images |
| `docs/operations/containers-ci.md`, `README.md` | Cách chạy và giới hạn thực tế |

### Task 1: Môi trường local và hợp đồng container

**Files:** Create `compose.yaml`, `.env.example`, `.dockerignore`, `.nvmrc`, `docker/api.Dockerfile`, `docker/web.Dockerfile`, `docker/nginx.conf`, `docs/operations/containers-ci.md`; Modify `README.md`.

**Interfaces:** Consumes biến `POSTGRES_PASSWORD`; produces PostgreSQL `db:5432`, API `api:3000`, dev web `5173`; build context repo root, package độc lập trong `apps/api`, `apps/web`; API production `dist/main.js`, web `dist/`.

- [x] Step 1: Tạo cấu hình theo hợp đồng trên, PostgreSQL volume `pgdata`, healthcheck `pg_isready`, runtime API nonroot, nginx cổng 8080.
- [ ] Step 2: Khi được yêu cầu xác minh, chạy `docker compose --env-file .env.example config --quiet`; kỳ vọng exit 0 và không cần mã nguồn app.
- [ ] Step 3: Với `.env` đã có mật khẩu local, chạy `docker compose up -d --wait db`; kỳ vọng healthy. Tạo dữ liệu tạm, restart db, đọc lại để kiểm tra bền vững; không dùng `down -v`.
- [ ] Step 4: Sau khi có code, chạy `docker compose --profile app up --build`; kỳ vọng API `/health/ready` trả 200, web dev phục vụ cổng 5173. API đọc DB thất bại thì readiness trả 503.
- [ ] Step 5: Commit đúng các file Task 1 sau khi người dùng yêu cầu lưu Git.

### Task 2: CI phân biệt bootstrap và app-ready

**Files:** Create `scripts/ci/app-contract.mjs`, `.github/workflows/ci.yml`.

**Interfaces:** Consumes app package.json/package-lock.json; produces output `ready=true|false` qua GITHUB_OUTPUT. Mỗi app có scripts `dev`, `lint`, `typecheck`, `test:ci`, `build`; script không được rỗng. API có `dependencies` production riêng, không dùng workspace bên ngoài app.

- [x] Step 1: Viết `app-contract.mjs`: không có cả hai thư mục → bootstrap; một app/manifest/lock/script thiếu → exit 1; đủ cả hai → ready. `--strict` làm bootstrap exit 1.
- [ ] Step 2: Khi xác minh, chạy `node scripts/ci/app-contract.mjs`; kỳ vọng bootstrap trên repo hiện tại; `--strict` kỳ vọng exit 1.
- [ ] Step 3: Trong checkout fixture tạm, tạo manifest thiếu lock hoặc thiếu `test:ci`; kỳ vọng exit 1 và chỉ rõ app/trường lỗi. Không tạo test ứng dụng giả để CI xanh.
- [x] Step 4: Cấu hình PR/push CI với permissions contents/read, npm ci rồi lint/typecheck/test:ci/build, build hai Dockerfile production khi ready. Compose config luôn được kiểm tra.
- [ ] Step 5: Commit đúng các file Task 2 khi được yêu cầu.

### Task 3: Xuất image có kiểm soát

**Files:** Create `.github/workflows/publish-images.yml`, `.github/dependabot.yml`; update hướng dẫn vận hành.

**Interfaces:** Consumes default branch, app-contract strict và scripts Task 2; produces `ghcr.io/<owner>/lib-management-api:sha-<full SHA>` và image web tương ứng. Không nhận ref tùy ý từ input.

- [x] Step 1: Tạo workflow_dispatch chỉ cho default branch; chạy strict contract và quality gates trong job contents/read.
- [x] Step 2: Job packages/write chỉ chạy sau quality; build cả hai image trước docker login/push. Gắn OCI source/revision labels, ghi digest vào job summary.
- [ ] Step 3: Khi được yêu cầu xác minh, xác nhận PR không thể kích hoạt publish; bootstrap bị chặn; lỗi build image thứ hai xảy ra trước mọi push. Nếu push thứ hai lỗi registry, ghi nhận release chưa hoàn tất, không deploy.
- [x] Step 4: Cấu hình Dependabot cho GitHub Actions và Dockerfiles; tài liệu hóa môi trường `image-publish` và approval do maintainer thiết lập trong GitHub.
- [ ] Step 5: Commit đúng các file Task 3 khi được yêu cầu; chưa kích hoạt workflow hoặc thay GitHub settings trong nhiệm vụ chuẩn bị.

## Self-review

- Phạm vi chỉ hạ tầng; nghiệp vụ, migration, OIDC, worker và đích deployment thuộc kế hoạch tiếp theo.
- Các đường dẫn app, script, cổng và output thống nhất giữa Compose/Dockerfile/CI/CD.
- Năm Review Focus có bước xác minh cụ thể; chưa chạy các bước đó trong lần này.
- Không có secret thật, mật khẩu mẫu chỉ dùng thay thế local; C01–C09 không bị đổi.
