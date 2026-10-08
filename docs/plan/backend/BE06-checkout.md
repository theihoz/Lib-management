# BE06 — Cho mượn

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F07
**Phụ thuộc:** BE02, BE03, BE04, BE05

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Loan, LoanItem; POST /loans; tích hợp Reservation ở BE08.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE06.1 | Tạo Loan/LoanItem và partial unique cho một mục OPEN mỗi BookCopy | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE06.2 | Dựng checkout tối đa 4 cuốn/phiếu, kiểm tra eligibility lại dưới khóa | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE06.3 | Thêm idempotency, snapshot policy/dueAt và hợp đồng nhận bản sao giữ đúng người | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE06.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Hai quầy không mượn cùng copy.
- 5 cuốn bị chặn.
- lỗi bất kỳ rollback cả phiếu.
- retry trả cùng kết quả.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
