# BE10 — Báo cáo và CSV

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F13, F20
**Phụ thuộc:** BE09, BE00; adapter lưu trữ BE11

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

ReportJob, Job, MediaAsset; /report-jobs, /export-jobs, /jobs/{id}.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE10.1 | Định nghĩa từng metric, kỳ báo cáo và read query không nhân bản do join | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE10.2 | Dựng job xuất CSV, artifact private và trạng thái tiến trình | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE10.3 | Kiểm tra quyền Quản lý lúc yêu cầu và tải, xử lý ô formula và artifact hết hạn | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE10.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Job trả 202.
- dữ liệu rỗng hợp lệ.
- quyền bị thu hồi chặn download.
- artifact hết hạn 410.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
