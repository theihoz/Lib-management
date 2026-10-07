# BE00 — Nền tảng backend

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** Toàn hệ thống
**Phụ thuộc:** Không

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Session/Unit of Work; Alembic; AuditLog, IdempotencyRecord, OutboxEvent, Job.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE00.1 | Lập ánh xạ 38 bảng/thuộc tính DOCX sang PostgreSQL và migration theo phụ thuộc | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE00.2 | Dựng router/service/repository, session đồng bộ mỗi request và Unit of Work liên module | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE00.3 | Chuẩn hóa lỗi, request ID, idempotency, audit và worker lease/retry | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE00.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- DB trống migrate được.
- transaction lỗi rollback.
- worker lấy lại job sau lease hết hạn.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
