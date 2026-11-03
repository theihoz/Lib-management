# Web frontend

React + TypeScript + Vite. Thiết kế và kế hoạch PR nằm ở
[spec M0 frontend](../../docs/specs/M0-frontend-foundation.md).

Cần Node 24 LTS (có sẵn trong Dev Container). Từ thư mục này:

```bash
npm ci
npm run dev            # http://localhost:5173 (cổng cố định cho redirect Keycloak)
npm run lint && npm run format:check && npm run typecheck
npm test
npm run build          # dist/
```

## Cấu hình runtime

App tải `/config.json` trước khi render và kiểm tra bằng Zod (`src/config/config.ts`).
Thiếu trường, sai URL hoặc có khóa lạ thì app chỉ hiện trang lỗi cấu hình, không khởi
động auth hay gọi API. Bản dev nằm ở `public/config.json`; bản cho môi trường triển khai
được sinh lúc deploy (INT03). Tệp chỉ chứa giá trị công khai, không có secret.

| Trường         | Ý nghĩa                                             |
| -------------- | --------------------------------------------------- |
| `oidcUrl`      | URL gốc Keycloak, ví dụ `http://localhost:8080`     |
| `oidcRealm`    | Realm, `lib-management`                             |
| `oidcClientId` | Public client PKCE, `lib-management-web`            |
| `apiBaseUrl`   | Rỗng = cùng origin; hoặc URL http(s) tuyệt đối      |
| `mock`         | Bật chế độ mock (chỉ hiệu lực ngoài bản production) |

Trong dev, Vite proxy `/api` và `/health` sang `http://localhost:8000`
(đổi bằng biến `API_PROXY_TARGET`), nên backend không cần CORS.
