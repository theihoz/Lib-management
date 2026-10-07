# BE05 — Sổ phí và duyệt phí

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F11; hỗ trợ F08, F12
**Phụ thuộc:** BE01, BE02, BE04

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

FineCharge, Payment, PaymentAllocation, Waiver, PaymentReversal, AllocationReversal, WaiverReversal; bổ sung ChargeAssessment; /fine-charges, /payments, /ledger-reversals.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE05.1 | Thiết kế sổ phí append-only, tiền numeric(14,0), tính dư nợ từ ledger | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE05.2 | Tạo hồ sơ hỏng/mất PENDING, thủ thư đề xuất và quản lý xác nhận hoặc kết thúc không thu với lý do | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE05.3 | Triển khai thu từng phần, phân bổ, miễn/đảo và idempotency | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE05.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không thu quá dư.
- duyệt đồng thời chỉ tạo một phí.
- không xóa ledger.
- PENDING chặn checkout/renew/hold nhưng không return.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
