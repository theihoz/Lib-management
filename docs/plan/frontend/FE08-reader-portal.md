# FE08 — Portal độc giả

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F10, F17, F18, F24
**Phụ thuộc:** FE01, FE02, BE08, BE09, BE13

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/me/loans, /me/reservations, /me/history, /me/notifications.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE08.1 | Thiết kế mobile-first hiển thị hạn mượn/nhận và dư nợ của mình | Bố cục/component, state và hợp đồng màn hình |
| FE08.2 | Tạo/hủy giữ chỗ, xem lịch sử và lý do chặn | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE08.3 | Thông báo portal, đọc/chưa đọc và lựa chọn consent email | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE08.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không có ô nhập readerId tùy ý.
- loading/empty/error riêng.
- ngày và VND rõ.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Portal độc giả mobile

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Mở vào sách và việc cần làm: hạn mượn, READY, khoản chờ duyệt. Bottom nav Catalog/Của tôi/Thông báo; detail/history dùng list rõ ngày, CTA đặt/hủy riêng. Không banner marketing.

### Motion theo hành động

Route280ms, book hover theo device; badge read120ms; nội dung lịch sử không stagger dài. Bottom nav stable, tôn trọng safe-area.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Dựng navigation responsive; catalog/own-loans/holds; history/debt; notification và consent riêng.

- FE08.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE08.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE08.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Không hiển thị readerId input; sở hữu do backend; nhắc việc không phụ thuộc motion; thông báo click/read không làm item nhảy khỏi focus.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
