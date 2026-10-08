# BE05 — Sổ phí và duyệt phí

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F11; hỗ trợ F08, F12
**Phụ thuộc:** BE01, BE02, BE04

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

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

## Đồng bộ bảng ChargeAssessment

- BE05.S1: dùng đủ 15 trường tại data-dictionary.md §39; D01 phải được chốt trước tạo migration, không tự chọn kiểu/NULL.
- BE05.S2: PENDING có các trường quyết định và fine_charge_id NULL; ASSESSED có approved_amount>0, decided_by/decided_at/decision_reason và fine_charge_id; CLOSED_NO_CHARGE có approved_amount=0, thông tin quyết định và fine_charge_id NULL. CHECK phải chỉ rõ IS NULL/IS NOT NULL.
- BE05.S3: reader_id/proposed_by/decided_by/decided_at lấy phía server; kiểm tra return/loan cùng độc giả dưới khóa. Duyệt tạo FineCharge và audit cùng transaction; version xử lý 409 theo API.
- BE05.S4: ChargeAssessment response là projection an toàn, không bắt buộc công khai toàn bộ cột DB; mô tả mapping theo api-contract.md. Giữ PENDING chặn mượn/gia hạn/đặt trước, không chặn trả.
