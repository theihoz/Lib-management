# BE08 — Giữ chỗ và gia hạn

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F09, F10
**Phụ thuộc:** BE06, BE07; worker BE00

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Reservation, RenewalEvent, RenewalItem; /reservations, /loans/{id}/renewals.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE08.1 | Dựng FIFO theo created_at,id; một lượt active theo reader/edition và phân bổ copy READY | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE08.2 | Thêm hủy, expiry 3 ngày từ readyAt, pickup kiểm tra eligibility và tái phân bổ | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE08.3 | Gia hạn toàn bộ mục OPEN đủ điều kiện, tối đa một lần thêm 4 ngày từ hạn cũ | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE08.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- READY hết hạn chặn ngay dù worker chậm.
- FIFO ổn định.
- gia hạn toàn bộ hoặc không mục nào.
- mục đã trả không đổi.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
