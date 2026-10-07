# FE02 — Danh mục, tìm sách và ảnh bìa

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F01–F05, F15, F18
**Phụ thuộc:** FE00, FE01, BE03, BE11

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/catalog, /staff/catalog; chi tiết edition/copies/reference data.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE02.1 | Dựng catalog responsive tìm kiếm/filter/cursor và chi tiết ấn bản | Bố cục/component, state và hợp đồng màn hình |
| FE02.2 | Dựng form tác giả/NXB/thể loại/edition cùng bảng copies và barcode | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE02.3 | Dựng upload/thay ảnh bìa, xử lý conflict giữ form và tải lại dữ liệu | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE02.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Dữ liệu thật qua client.
- tên trùng không tự gộp.
- lỗi cây/barcode hiển thị sát trường.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Catalog và hình ảnh sách

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Portal dùng grid cover2:3 với nhãn thể loại gọn, title/author rõ; nhân viên dùng bảng edition và panel copies, toolbar tìm/filter ổn định. Chi tiết sách có cover và thông tin thực, không ảnh trang trí.

### Motion theo hành động

Cover hover nâng3px trên thiết bị hover; grid xuất hiện stagger tối đa6 mục; filter crossfade120ms không replay khi poll. Drawer chi tiết240ms.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Làm catalog public/detail trước; quản trị list/form/copies sau; upload và trạng thái ảnh đi cùng adapter BE11.

- FE02.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE02.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE02.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Cover có kích thước dự trữ; fallback có title/author; không giả stock thành ảnh thật; tìm kiếm không mất focus và request cũ không ghi đè.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
