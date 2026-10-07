# BE12 — Nhập sách và thanh lý

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F22
**Phụ thuộc:** BE01, BE03, BE06, BE08

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

AcquisitionReceipt, AcquisitionReceiptItem, BookCopy; /acquisition-receipts, lệnh disposal.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE12.1 | Dựng phiếu nhập draft và duyệt bởi Quản lý | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE12.2 | Post receipt và tạo copies nguyên tử; kiểm tra barcode trước commit | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE12.3 | Dựng thanh lý với permission, reason và guard loan/hold; lưu audit | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE12.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Phiếu đã post không sửa trực tiếp.
- lỗi một barcode rollback.
- copy đang mượn/READY không thanh lý.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
