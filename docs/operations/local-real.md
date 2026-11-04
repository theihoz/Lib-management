# Chạy bản thật trên máy cá nhân

GitHub Pages chỉ là **bản demo**: dữ liệu giả lập ngay trong trình duyệt, chọn vai trò để
"đăng nhập", không có máy chủ hay database. Bản **thật** chạy trên máy bạn bằng Docker:
mọi thao tác đọc/ghi vào PostgreSQL local, đăng nhập thật qua Keycloak.

| | GitHub Pages (demo) | Máy cá nhân (thật) |
| --- | --- | --- |
| Dữ liệu | Giả lập trong trình duyệt, mất khi tải lại | PostgreSQL 17, giữ qua các lần khởi động |
| Đăng nhập | Chọn vai trò, không mật khẩu | Keycloak OIDC + PKCE, tài khoản thật |
| API, worker, báo cáo CSV | Không có | FastAPI + worker chạy thật |
| Bundle web | `npm run build:demo` | `npm run build` (production, không chứa code mock) |

## Yêu cầu

- Docker Desktop (macOS/Windows) hoặc Docker Engine + Compose v2.23 trở lên (Linux).
- Bash: có sẵn trên macOS/Linux; Windows dùng Git Bash hoặc WSL2.
- Cổng trống: `5173` (web), `8000` (API), `8080` (Keycloak), `5432` (PostgreSQL).
  Không cần cài Python hay Node trên máy: mọi thứ build trong container.

## Một lệnh để chạy

```bash
scripts/local.sh up
```

Lần đầu mất vài phút để build image. Script sẽ:

1. Tạo `.env` từ `.env.example` nếu chưa có, sinh mật khẩu ngẫu nhiên cho PostgreSQL
   (chỉ khi database chưa được khởi tạo) và cho Keycloak. `.env` bị gitignore.
2. Kiểm tra cổng; báo rõ cổng nào đang bị chương trình khác chiếm.
3. Chạy `docker compose -f compose.yaml -f compose.local.yaml up --build -d --wait`:

```text
db (PostgreSQL) ──► migrate ──► seed ──► api ──► web (nginx, :5173)
keycloak (:8080) ─────────────────┘       └─► worker
```

- `db`: PostgreSQL 17, múi giờ UTC (nghiệp vụ dùng Asia/Ho_Chi_Minh trong code), dữ liệu ở volume
  `lib-management_pgdata`.
- `migrate`: áp dụng 6 migration Alembic → 42 bảng theo [thiết kế DB](../design/database-design.md).
- `seed`: tạo 39 permission/5 role, tạo 5 user Keycloak và liên kết với Account, rồi chạy
  `seed-demo`. Chạy lại nhiều lần không sao (idempotent: chỉ thêm dòng còn thiếu).
- `web`: bản build production phục vụ bằng nginx, proxy `/api` sang API nên không cần CORS.

Khi xong, mở <http://localhost:5173> → **Đăng nhập** → **Tiếp tục với SSO**.

| Tài khoản | Vai trò |
| --- | --- |
| `librarian.dev` | Thủ thư |
| `manager.dev` | Quản lý |
| `admin.dev` | Admin hệ thống |
| `ops.dev` | Admin vận hành |
| `reader.dev` | Độc giả |

### Dữ liệu mẫu (`seed-demo`)

Chỉ dành cho máy local, không chạy trên production:

| Dữ liệu | Nội dung |
| --- | --- |
| Quy định | Một bản ACTIVE với luật mặc định (mượn tối đa 4 cuốn, 4 ngày, thẻ 6 tháng…) |
| Danh mục | 4 nhà xuất bản, 4 thể loại, 2 kho, 8 đầu sách xuất bản 2020–2025 |
| Bản sao | 18 cuốn, mã vạch `DEMO-0001` … `DEMO-0018`, đều AVAILABLE |
| Độc giả | `DG0001`–`DG0005`, thẻ `THE-DG0001`… còn hạn 6 tháng |
| Liên kết | `reader.dev` là độc giả `DG0001` (Nguyễn Minh An) |

Thử nhanh: đăng nhập `librarian.dev` → **Quầy mượn sách** → thẻ `THE-DG0001`, mã vạch `DEMO-0001`;
rồi đăng nhập `reader.dev` để thấy phiếu mượn của mình. Xóa sạch để bắt đầu lại:
`scripts/local.sh reset` rồi `scripts/local.sh up`.

Mật khẩu chung là giá trị `KEYCLOAK_DEV_USER_PASSWORD` trong `.env`. Trang quản trị Keycloak
<http://localhost:8080> dùng user `admin` và `KEYCLOAK_ADMIN_PASSWORD`.

## Lệnh thường dùng

```bash
scripts/local.sh status          # trạng thái container
scripts/local.sh logs api        # xem log (bỏ "api" để xem tất cả)
scripts/local.sh token           # in access token của librarian.dev để gọi API thử
scripts/local.sh down            # dừng, GIỮ dữ liệu
scripts/local.sh reset           # dừng và XÓA database + Keycloak (hỏi xác nhận)
```

Gọi API bằng token, ví dụ:

```bash
curl -H "Authorization: Bearer $(scripts/local.sh token)" http://localhost:8000/api/v1/auth/me
```

Swagger: <http://localhost:8000/docs>. Kết nối DB bằng công cụ ngoài: `127.0.0.1:5432`,
user/database theo `.env` (`lib_dev` / `lib_management`).

Sau khi sửa code, chạy lại `scripts/local.sh up` để build lại. API có reload tự động vì
`apps/api/src` được mount; web cần build lại. Khi phát triển giao diện, có thể để stack chạy
rồi dùng `cd apps/web && npm run dev` — Vite cũng dùng cổng 5173 nên dừng service `web`
trước: `docker compose -f compose.yaml -f compose.local.yaml stop web`. Vite đọc
`apps/web/public/config.json` (Keycloak ở cổng 8080); đổi `KEYCLOAK_PORT` thì sửa cả tệp này.

## Xử lý lỗi

| Hiện tượng | Cách xử lý |
| --- | --- |
| `Cổng đang bị chiếm: keycloak (8080)` | Tắt chương trình dùng cổng, hoặc đặt `KEYCLOAK_PORT=8180` trong `.env`. Tương tự `API_PORT`, `POSTGRES_PORT`. Cổng web 5173 cố định vì Keycloak chỉ cho redirect về đó. |
| `migrate`/`seed` thất bại với `password authentication failed` | `.env` có mật khẩu khác lúc database được tạo. Khôi phục mật khẩu cũ, hoặc `scripts/local.sh reset` nếu không cần dữ liệu. |
| Đăng nhập xong báo "chưa có quyền"/tài khoản chưa liên kết | Chạy lại `scripts/local.sh up` để `seed` liên kết lại user. |
| Không thấy thay đổi giao diện | Chạy lại `scripts/local.sh up` (build lại image `web`), rồi tải lại trang không cache. |
| Dev Container đang chạy | Dev Container dùng stack riêng; dừng nó trước để không trùng cổng 8000/5173/8080. |

Stack này **chỉ dành cho máy cá nhân**: Keycloak chạy `start-dev` với realm dev và mọi cổng
chỉ mở trên `127.0.0.1`. Không dùng cấu hình này để triển khai cho người khác truy cập.
