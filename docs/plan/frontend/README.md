# Kế hoạch frontend — Redesign và motion

**Ngày:** 2026-10-07 · **Trạng thái:** Đặc tả, chưa có mã frontend.

## Đọc trước

1. [Định hướng thiết kế](DESIGN-DIRECTION.md): phong cách, màu, chữ, layout và component.
2. [Motion](MOTION.md): timing, trigger, focus và reduced motion.
3. Chọn module bên dưới; áp dụng task chức năng và D1/D2/D3 cho redesign.

## Wireframe

[Board 12 màn hình desktop/mobile](wireframes.html) và [ánh xạ](WIREFRAMES.md). Đây là thiết kế tĩnh, không phải app.

## Mục lục

| Module | Kế hoạch |
| --- | --- |
| FE00 | [FE00 — Nền tảng frontend và thiết kế](FE00-foundation-design.md) |
| FE01 | [FE01 — Đăng nhập và điều hướng](FE01-auth-navigation.md) |
| FE02 | [FE02 — Danh mục, tìm sách và ảnh bìa](FE02-catalog.md) |
| FE03 | [FE03 — Hồ sơ độc giả và cấp thẻ](FE03-readers-cards.md) |
| FE04 | [FE04 — Quầy mượn](FE04-checkout.md) |
| FE05 | [FE05 — Quầy trả](FE05-returns.md) |
| FE06 | [FE06 — Giữ chỗ và gia hạn](FE06-reservations-renewals.md) |
| FE07 | [FE07 — Duyệt phí, thu và miễn/đảo](FE07-finance.md) |
| FE08 | [FE08 — Portal độc giả](FE08-reader-portal.md) |
| FE09 | [FE09 — Báo cáo và quy định](FE09-reports-policy.md) |
| FE10 | [FE10 — Tài khoản, nhập và thanh lý](FE10-administration-inventory.md) |
| FE11 | [FE11 — Màn hình vận hành](FE11-operations.md) |

## Thứ tự

- Nền FE00 và auth/navigation FE01 trước; FE02–FE05 là luồng tích hợp đầu tiên.
- Review app shell + catalog + checkout tĩnh trước; thống nhất tokens rồi mở rộng.
- Motion primitives dùng lại; mỗi màn hình chỉ ghi trigger riêng. Không animation mọi component.
- Giữ các dependency backend đã ghi; mock theo OpenAPI chỉ phục vụ phát triển sớm.
- Toàn bộ phạm vi và C01–C09 ở [quyết định](../decisions.md), [truy vết](../traceability.md). Đặc tả frontend mới tinh chỉnh thẩm mỹ, không thay đổi nghiệp vụ.

## Bàn giao

- Mỗi PR nêu task FE và D-task, màn hình, trạng thái và motion đã áp dụng.
- Khi triển khai: ghi hình desktop/mobile, focus/keyboard và reduced-motion; kiểm thử theo kế hoạch hiện có.
- Nhiệm vụ hiện tại chỉ sửa Markdown trong frontend; không tạo app, dependency hoặc chạy test.
