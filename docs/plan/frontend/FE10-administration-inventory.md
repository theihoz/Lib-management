# FE10 — Tài khoản, nhập và thanh lý

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F21, F22
**Phụ thuộc:** FE01, BE01, BE12

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/admin/accounts, /staff/acquisitions, /manager/disposals.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE10.1 | Quản trị Account/Role/Permission và xác nhận thay đổi quyền | Bố cục/component, state và hợp đồng màn hình |
| FE10.2 | Form receipt nhiều mục, workflow gửi duyệt/post và kết quả tạo copies | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE10.3 | Thanh lý có reason/guard, trạng thái và lịch sử audit | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE10.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không sửa receipt đã post.
- lộ quyền theo permission.
- lỗi barcode không tạo tồn một phần.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Quản trị và tồn kho

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Account/role dùng list và permission detail; receipt như chứng từ với items/barcode, trạng thái duyệt/post; disposal có tóm tắt tác động. Nhóm quyền và kho rõ ràng.

### Motion theo hành động

Panel240ms, row barcode mới180ms; state post đổi chip sau commit; không animation số tồn dự kiến thành tồn thật.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Account role management; receipt draft/approval/post; disposal guard/reason và audit view.

- FE10.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE10.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE10.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Phiếu posted readonly; giữ form khi barcode conflict; sửa quyền có review và không tự mở admin menu trước server success.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
