# BE07 — Nhận trả và ghi nhận tình trạng

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F08
**Phụ thuộc:** BE05, BE06

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

ReturnEvent; POST /returns; BookCopy, FineCharge, ChargeAssessment.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE07.1 | Dựng trả từng LoanItem, đóng mục và cập nhật copy trong một giao dịch | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE07.2 | Tính phí trễ từ localDate và snapshot, tạo ChargeAssessment cho hỏng/mất | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE07.3 | Ghi outbox phân bổ giữ chỗ; giữ thanh toán ở giao dịch riêng | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE07.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Nợ/thẻ hết hạn vẫn nhận trả.
- retry không nhân ReturnEvent/phí.
- GOOD→AVAILABLE hoặc giữ chỗ, DAMAGE→REPAIR, LOST→LOST.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
