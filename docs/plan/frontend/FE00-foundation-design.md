# FE00 — Nền tảng frontend và thiết kế

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** Toàn hệ thống
**Phụ thuộc:** INT00

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

Khung app, CSS tokens, components và trạng thái.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE00.1 | Bootstrap apps/web React TypeScript Vite, npm lockfile, React Router và client OpenAPI | Bố cục/component, state và hợp đồng màn hình |
| FE00.2 | Tạo tokens tinh chỉnh từ DOCX theo DESIGN-DIRECTION.md; bảng/form/dialog/book tile/receipt và responsive | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE00.3 | Thiết lập TanStack Query, React Hook Form/Zod, Vitest/Testing Library và môi trường mock | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE00.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Desktop/mobile không overflow.
- focus rõ.
- nhãn tiếng Việt.
- cấu hình API không chứa secret.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Shell và bộ thành phần

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Sidebar xanh mực, vùng làm việc nền giấy; serif chỉ cho heading, sans cho control. Có table/form/dialog/book tile/reader strip/receipt dùng lại, không card lồng card.

### Motion theo hành động

Tạo primitives route enter, dialog, row feedback, toast cùng reduced-motion theo MOTION.md. Shell giữ nguyên giữa routes; chỉ content transition.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Token/shell/components có review hình tĩnh; sau đó thêm motion trong PR riêng, tránh trộn thay layout với nghiệp vụ.

- FE00.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE00.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE00.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Form/bảng/text dài không overflow; reduced motion không mất feedback; contrast và focus được đo khi triển khai.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
