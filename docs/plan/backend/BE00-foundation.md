# BE00 — Nền tảng backend

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** Toàn hệ thống
**Phụ thuộc:** Không

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

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

## Đồng bộ Docs 08/10/2026

- BE00.S1: đối chiếu model/migration với data-dictionary.json: 38 bảng/288 trường gốc + ChargeAssessment 15 trường. Bổ sung notification riêng theo BE13; schema dự kiến 42 bảng.
- BE00.S2: chốt D01 trước migration ChargeAssessment; ghi SQL type/độ rộng kind/status và NOT NULL version/created_at bằng quyết định có duyệt. Không suy ra DB nullability từ required DTO hoặc DEFAULT.
- BE00.S3: giữ ánh xạ snake_case; numeric(14,0) trong DB, tiền là chuỗi số nguyên trong API. Một Unit of Work, service sở hữu commit; repository không commit riêng.
- Nghiệm thu: từng trường có đủ 7 cột, FK/UQ/NULL có đối chiếu; 39/303 là mốc tài liệu, không phải số bảng đang tồn tại trong PostgreSQL.
