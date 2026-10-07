# BE03 — Danh mục và bản sao

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F01–F05, F18
**Phụ thuộc:** BE00, BE01; BE02 cho kiểm tra năm

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Publisher, Author, Category, BookEdition, BookAuthor, BookCategory, Location, BookCopy; /book-editions, /authors, /publishers, /categories.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE03.1 | Dựng model/migration và ràng buộc barcode/ISBN theo DOCX | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE03.2 | Triển khai CRUD tham chiếu, thể loại phân cấp, thêm bản sao nguyên tử | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE03.3 | Thêm catalog công khai, cursor và truy vấn batch tránh N+1 | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE03.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Chặn cây chu trình.
- barcode trùng rollback cả lô.
- hai tác giả trùng tên vẫn có ID riêng.
- catalog không PII.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
