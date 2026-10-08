# BE04 — Độc giả và thẻ

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F06, F12
**Phụ thuộc:** BE01, BE02; BE05/BE06/BE08 cho eligibility đầy đủ

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Reader, ReaderCard; /readers, /readers/{id}/cards, /readers/{id}/eligibility.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE04.1 | Tạo hồ sơ và cấp thẻ với tuổi 12–55, hạn 6 tháng lịch | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE04.2 | Liên kết Account với Reader và bảo vệ truy cập theo chủ sở hữu | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE04.3 | Xây eligibility reasons từ thẻ, dư nợ, khoản chờ duyệt, quá hạn và policy; dùng port để nối các module | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE04.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Biên tuổi/expiry đúng.
- cộng tháng xử lý ngày cuối tháng.
- preview không thay kiểm tra trong giao dịch.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
