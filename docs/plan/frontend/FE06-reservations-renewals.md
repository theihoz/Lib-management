# FE06 — Giữ chỗ và gia hạn

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F09, F10
**Phụ thuộc:** FE01, BE08

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/staff/reservations, màn gia hạn phiếu.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE06.1 | Danh sách QUEUED/READY cùng vị trí/hạn nhận từ server | Bố cục/component, state và hợp đồng màn hình |
| FE06.2 | Luồng hủy, pickup và trạng thái hết hạn; xử lý conflict | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE06.3 | Preview gia hạn toàn bộ OPEN và xác nhận, giữ rõ hạn cũ/mới | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE06.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không cho chỉnh status tùy ý.
- worker chậm không làm UI hứa pickup.
- lý do chặn từng mục rõ.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Hàng đợi giữ chỗ và gia hạn

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Table staff có QUEUED/READY/expiry, vị trí hàng đợi rõ; portal timeline 3 bước Đang chờ→Sẵn sàng→Nhận sách. Gia hạn hiển thị hạn cũ/mới và reasons của mục OPEN.

### Motion theo hành động

READY đổi chip120ms và highlight một lần khi event mới; countdown là text theo hạn server, không pulse liên tục; approval drawer240ms.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Dựng list/timeline; hủy/pickup và expiry; preview renew all-or-nothing; feedback conflict.

- FE06.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE06.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE06.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Không re-sort row đang focus khi polling; đúng hạn chặn pickup ngay; lỗi renewal không làm UI đổi hạn từng phần.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
