# FE04 — Quầy mượn

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F07, F12
**Phụ thuộc:** FE01, FE02, FE03, BE06

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/staff/checkout.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE04.1 | Quét thẻ với focus và thanh điều kiện độc giả luôn hiển thị | Bố cục/component, state và hợp đồng màn hình |
| FE04.2 | Quét barcode, tối đa4 copies không trùng, preview và xác nhận | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE04.3 | Gửi Idempotency-Key, biên nhận, xử lý COPY_UNAVAILABLE và giữ danh sách để sửa | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE04.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Enter không gửi hai lần.
- pending vô hiệu nút submit.
- conflict không mất dữ liệu nhập.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Quầy mượn và thanh hành trình

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Desktop: scanner và danh sách sách ở cột chính; tóm tắt độc giả/điều kiện/hạn và CTA ở cột340px. Thanh Xác định→Chọn sách→Xác nhận→Biên nhận nằm đầu vùng quầy; mobile theo một cột.

### Motion theo hành động

Scan thành công thêm row180ms và viền nhấn một lần; bước hoàn tất đổi marker180ms; receipt fade180ms. Không stagger danh sách hoặc chờ animation trước scan tiếp.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Dựng layout/keyboard scan; nối lookup và eligibility; confirmation/idempotency; receipt và conflict feedback.

- FE04.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE04.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE04.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Tối đa4 không đổi; COPY_UNAVAILABLE giữ danh sách; scanner luôn sẵn sàng; Enter không submit trùng; status announce một lần.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
