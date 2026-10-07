# BE09 — Lịch sử, tra cứu và quá hạn

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F17, F18, F19
**Phụ thuộc:** BE03, BE04, BE05, BE06, BE08

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Read queries; /readers/{id}/history, /overdue-items.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE09.1 | Dựng projection lịch sử mượn/trả/gia hạn/ledger có cursor | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE09.2 | Tách tìm sách công khai và tìm độc giả chỉ cho nhân viên có quyền | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE09.3 | Tính quá hạn từ OPEN và dueAt, thêm asOf và index phù hợp | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE09.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không lưu trạng thái quá hạn làm chân lý.
- không leak reader.
- join không nhân tiền.
- filter sai trả lỗi rõ.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
