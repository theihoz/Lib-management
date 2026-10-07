# BE01 — Tài khoản và phân quyền

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F16, F21
**Phụ thuộc:** BE00

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Account, Role, Permission, AccountRole, RolePermission; /auth/me, /accounts, /roles.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE01.1 | Cấu hình Keycloak realm/client public PKCE, JWKS issuer/audience và liên kết issuer+sub | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE01.2 | Xây dịch vụ quyền theo Account đang hoạt động và role/permission trong DB | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE01.3 | Thêm cấp/liên kết/khóa tài khoản độc giả, quản trị quyền và audit | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE01.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- JWT sai/hết hạn nhận 401.
- ngoài scope nhận 403.
- khóa Account chặn API dù JWT còn hạn.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
