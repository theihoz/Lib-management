# FE03 — Hồ sơ độc giả và cấp thẻ

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F06, F12
**Phụ thuộc:** FE01, BE04

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/staff/readers, chi tiết độc giả và cấp thẻ.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE03.1 | Dựng tìm/list/detail độc giả theo permission | Bố cục/component, state và hợp đồng màn hình |
| FE03.2 | Form tạo hồ sơ/cấp thẻ, preview hạn và điều kiện từ API | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE03.3 | Luồng nhân viên cấp/liên kết Account; thông báo trùng hồ sơ và expiry | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE03.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không tự tính eligibility thay backend.
- dữ liệu nhập không mất khi lỗi.
- thao tác bằng bàn phím.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Hồ sơ độc giả

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

List bên trái, chi tiết/thẻ bên phải trên desktop; mobile theo trang detail. Thẻ có mã, thời hạn và tình trạng bằng text; action Cấp thẻ/Liên kết tài khoản tách rõ.

### Motion theo hành động

Reader strip cập nhật màu120ms; preview hạn thay nội dung không shake; drawer240ms với focus return. Không count-up tuổi/hạn thẻ.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Triển khai list/detail và form; nối preview server/eligibility; thêm feedback cấp thẻ sau commit.

- FE03.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE03.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE03.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Lý do chặn đọc được; Account mapping không suy từ email; focus không bị reset bởi preview/refetch.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
