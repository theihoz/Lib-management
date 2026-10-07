# BE13 — Thông báo portal và email

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F24
**Phụ thuộc:** BE00, BE07, BE08, BE09

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

OutboxEvent, Job; portal notification/delivery metadata bổ sung; /notifications.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE13.1 | Định nghĩa notification và delivery metadata, consent theo kênh, dedupe event/channel | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE13.2 | Dựng READY event và email tổng hợp quá hạn 08:00 Asia/Ho_Chi_Minh mỗi độc giả/ngày | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE13.3 | SMTP adapter, lease/backoff/dead-letter, stale-event check và replay có quyền | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE13.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Provider lỗi không rollback nghiệp vụ.
- không kéo dài READY.
- không hứa exactly-once.
- portal chỉ dữ liệu của mình.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
