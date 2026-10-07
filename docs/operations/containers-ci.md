# Docker và CI/CD — giai đoạn chuẩn bị code

## Trạng thái

Repo hiện chưa có mã nguồn API/web hoặc migration. PostgreSQL là dịch vụ dùng được ngay sau khi cấu hình mật khẩu và khởi động Docker. Dockerfile ứng dụng là hợp đồng chuẩn bị theo React/Vite + NestJS trong README; N02 vẫn chưa chốt lựa chọn .NET/NestJS. Nếu chọn .NET, thay API Dockerfile và job quality API trước khi thêm code.

Thiết kế nghiệp vụ chuẩn: [Google Docs Lib-management](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit). C01–C09 đã được chấp nhận. Không tạo schema 38 bảng bằng các init SQL giả trong nhiệm vụ này.

## 1. Chạy PostgreSQL local

Yêu cầu Docker Engine/Desktop với Compose v2. Node local theo `.nvmrc` nếu chạy script bằng máy host.

```bash
cp .env.example .env
# Sửa POSTGRES_PASSWORD trong .env thành mật khẩu local của bạn.
docker compose up -d --wait db
docker compose ps
docker compose logs --tail=50 db
```

Kết nối từ host: `127.0.0.1:5432`, database `lib_management`, user `lib_dev`, mật khẩu trong `.env`. Từ API container dùng `db:5432`. Nếu đổi cổng, sửa `POSTGRES_PORT`.

```bash
docker compose exec db psql -U lib_dev -d lib_management
docker compose down
```

`down` giữ volume `pgdata`. `down -v` xóa dữ liệu nên chỉ dùng khi chủ động bỏ database local. Đổi POSTGRES_PASSWORD sau khi volume đã khởi tạo không tự đổi mật khẩu role PostgreSQL; đổi role trong DB hoặc chủ động tạo môi trường local mới.

Ảnh PostgreSQL dùng nhánh `17-bookworm` để nhận cập nhật bản vá; tag này không bất biến. API dùng Node `24.21.0-bookworm-slim`, web runtime `nginx-unprivileged:1.28-alpine`. Trước khi phát hành production, chốt base image digest và chính sách cập nhật; image ứng dụng xuất GHCR được ghi digest riêng. Dependabot theo dõi Dockerfiles và GitHub Actions; tag Compose cần maintainer theo dõi.

## 2. Hợp đồng khi thêm code

Tạo cả hai app cùng một PR bootstrap. Thư mục `apps/api` hoặc `apps/web` xuất hiện mà chưa đủ hợp đồng sẽ làm CI thất bại; không tạo thư mục app rỗng chỉ để giữ chỗ.

| Thuộc tính | API | Web |
| --- | --- | --- |
| Thư mục | `apps/api` | `apps/web` |
| Package | package.json + package-lock.json độc lập | package.json + package-lock.json độc lập |
| Scripts bắt buộc | dev, lint, typecheck, test:ci, build | dev, lint, typecheck, test:ci, build |
| Dev | Bind 0.0.0.0:3000 | Vite 0.0.0.0:5173 |
| Build output | dist/main.js, dependencies runtime trong dependencies | dist/index.html và assets |
| Runtime | node dist/main.js, user node | nginx nonroot cổng 8080 |
| Health | GET /health/live và /health/ready ngoài prefix /api/v1 | GET /health/live ở nginx |

`test:ci` chạy một lần, không watch; ban đầu là suite tự chứa, không cần DB ngoài. Integration test có PostgreSQL riêng sẽ được thêm khi code/migration có thật. Không dùng `echo success`, `--if-present` hoặc bỏ kiểm tra để làm CI xanh.

API đọc `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME`, `DB_PASSWORD` riêng, không ghép mật khẩu bằng nội suy URL. Readiness trả 200 khi DB và migration sẵn sàng, 503 nếu chưa sẵn sàng. API xử lý SIGTERM để đóng kết nối. Migration chạy bằng bước riêng có quyền thích hợp, không tự chạy cạnh tranh trong mỗi replica.

Web đọc `import.meta.env.VITE_API_BASE_URL`. Dev mặc định `http://localhost:3000/api/v1`; API CORS chỉ cho origin cấu hình. Production build dùng `/api/v1`, nginx giữ nguyên đường dẫn `/api/` khi proxy tới `api:3000`. Deployment sau này phải cung cấp DNS service `api`; chạy riêng image web cần cấu hình upstream phù hợp. Không đặt khóa bí mật vào biến VITE vì chúng nằm trong JavaScript tải về trình duyệt.

Build context là repo root. `.dockerignore` loại env, node_modules, tài liệu và Git trước khi COPY. `.env` được Git ignore; cấu hình local không chứa khóa R2 hoặc OIDC thật.

## 3. Bật ứng dụng khi đã có code

```bash
node scripts/ci/app-contract.mjs --strict
docker compose --profile app up --build
```

Web: `http://localhost:5173`. API: `http://localhost:3000`. DB chỉ bind localhost; web không được nối mạng backend của DB.

Hai named volume node_modules tránh dùng thư viện host trong container. Sau khi đổi package-lock, cập nhật thư viện trong volume trước khi chạy lại:

```bash
docker compose --profile app build api web
docker compose run --rm --no-deps api npm ci
docker compose run --rm --no-deps web npm ci
docker compose --profile app up
```

Dockerfile có stages `dev`, `build`, `production`. Build production từ repo root:

```bash
docker build --target production -f docker/api.Dockerfile -t lib-management-api:local .
docker build --target production -f docker/web.Dockerfile -t lib-management-web:local .
```

Compose hiện chỉ dành cho development. Production cần đích deploy, HTTPS, secret manager, DB role không superuser, migration, backup/restore và cấu hình runtime; các phần này chưa được quyết định.

## 4. GitHub Actions

### CI

Chạy trên PR, push main hoặc thủ công:

1. Kiểm tra mô hình Compose với `.env.example`, không bật container.
2. Nếu cả hai app chưa tồn tại: báo **BOOTSTRAP**, bỏ qua job ứng dụng rõ ràng.
3. Nếu app xuất hiện nhưng thiếu package/lock/script: thất bại, không bỏ qua.
4. Nếu đủ: mỗi app chạy npm ci → lint → typecheck → test:ci → build → build production image.
5. Job `ci-result` tổng hợp kết quả; dùng làm required check khi maintainer bật branch protection.

CI bootstrap xanh chỉ chứng minh cấu hình hạ tầng vượt qua kiểm tra cấu hình, chưa chứng minh ứng dụng chạy. CI không có packages/write; checkout không giữ credentials. Action được pin SHA, Dependabot đề xuất cập nhật.

### Publish image — bước CD chuẩn bị

Maintainer vào Actions → **Publish container images** → Run workflow từ default branch:

1. Chặn nhánh khác default branch.
2. Gọi CI với `require_app=true`, nên repo chưa code bị chặn.
3. Job publish dùng environment `image-publish`. Maintainer cần tạo environment và bật required reviewers nếu muốn có approval gate; file YAML không tự thiết lập reviewers.
4. Build thành công **cả API và web** trước khi login/push.
5. Dùng GITHUB_TOKEN với packages/write chỉ trong job publish; tag `sha-<full commit SHA>` và OCI source/revision.
6. Ghi digest mỗi image trong run summary. Không dùng latest; deployment sau này dùng digest.

Tên package: `ghcr.io/theihoz/lib-management-api` và `ghcr.io/theihoz/lib-management-web` trên repo hiện tại. Workflow tính owner lowercase nên vẫn dùng được sau khi chuyển repo.

Hai lần push registry không phải giao dịch nguyên tử: nếu lần thứ hai lỗi, run thất bại và lần đầu có thể đã tồn tại. Không deploy một cặp chưa hoàn tất; chỉ chọn hai digest từ một run thành công. Image push chưa phải deploy máy chủ. Chưa cấu hình SSH/server/cloud do chưa có đích deploy.

## 5. Kế hoạch xác minh

Các lệnh dưới đây được chuẩn bị, chưa chạy trong lần tạo cấu hình này:

```bash
docker compose --env-file .env.example --profile app config --quiet
node scripts/ci/app-contract.mjs
node scripts/ci/app-contract.mjs --strict
```

Kỳ vọng hiện tại: Compose config exit 0; contract thường báo BOOTSTRAP; strict exit 1. Sau khi có code, chạy CI và smoke health/SPA deep links. Kiểm tra restart DB giữ dữ liệu, missing lock/script chặn CI, và fork PR không có quyền publish.

## Nguồn kỹ thuật

- [Docker Compose profiles](https://docs.docker.com/compose/how-tos/profiles/)
- [Compose services và healthcheck](https://docs.docker.com/reference/compose-file/services/)
- [Node.js release schedule](https://github.com/nodejs/Release)
- [GitHub: Publishing Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images)
- [GitHub Container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
