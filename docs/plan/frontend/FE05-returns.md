# FE05 — Quầy trả

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F08
**Phụ thuộc:** FE01, BE07

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/staff/returns.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE05.1 | Quét copy và hiển thị LoanItem/dueAt | Bố cục/component, state và hợp đồng màn hình |
| FE05.2 | Form GOOD/DAMAGE/LOST, phí dự kiến và đề xuất hỏng/mất có lý do | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE05.3 | Nhận biên nhận trả, hiển thị chờ duyệt và liên kết thu tiền riêng | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE05.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không chặn trả do nợ/thẻ.
- phí dự kiến tách phí đã ghi.
- retry không tạo biên nhận mới.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Quầy trả và tình trạng sách

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Quét copy trước; hiển thị loan/dueAt; ba lựa chọn Tốt/Hỏng/Mất có label/icon. Phí dự kiến, khoản đã ghi và khoản chờ quản lý tách vùng; Thu tiền là bước riêng sau trả.

### Motion theo hành động

Row vừa nhận trả fade180ms, receipt check xuất hiện một lần; đổi condition màu120ms; không shake khi phát hiện phí.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Tạo flow từng item và condition; nối return server; receipt/pending assessment; liên kết thu tiền sau kết quả.

- FE05.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE05.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE05.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Thẻ hết hạn/nợ không disable trả; không tự ghi phí từ preview; retry không replay kết quả như giao dịch mới.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
