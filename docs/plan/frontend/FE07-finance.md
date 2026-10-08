# FE07 — Duyệt phí, thu và miễn/đảo

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F11
**Phụ thuộc:** FE01, BE05

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/staff/finance, /manager/charge-assessments.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE07.1 | Bảng phí gốc/đã thu/miễn/dư và hồ sơ PENDING cần quản lý xử lý | Bố cục/component, state và hợp đồng màn hình |
| FE07.2 | Form thanh toán một phần và phân bổ có biên nhận | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE07.3 | Dialog duyệt/miễn/đảo với reason, permission và dữ liệu trước/sau | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE07.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- VND không float.
- không đổi trực tiếp ledger.
- pending và nợ đã ghi phân biệt.
- conflict giữ form.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Sổ phí và hàng chờ xác nhận

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Hàng đợi phí chờ duyệt tách ledger; cột Gốc/Đã thu/Đã miễn/Dư căn phải và tabular nums. Form phân bổ và preview tổng cạnh nhau; action miễn/đảo trong dialog có reason.

### Motion theo hành động

Đổi allocation cập nhật số trực tiếp; highlight row sau response180ms; dialog240ms. Không đếm tiền từ0 hoặc toast thay biên nhận.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Dựng ledger và assessment; form payment/allocation; review trước approve/waive/reverse; feedback idempotency/conflict.

- FE07.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE07.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE07.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Số tiền không nhảy layout; pending assessment khác debt; permission quyết định action; miễn/đảo không PATCH ledger.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.

## Đồng bộ dữ liệu Docs mới

- FE07.S1: dùng ChargeAssessment DTO đã công bố, không gọi trực tiếp tên bảng hoặc tự thêm trường DB vào client. API tiền dạng chuỗi; hiển thị VND, không dùng float để tính dư nợ.
- FE07.S2: PENDING / ASSESSED / CLOSED_NO_CHARGE có nhãn, icon và giải thích; phân biệt đề xuất với nợ đã ghi. Chỉ Quản lý có action quyết định theo permission.
- FE07.S3: gửi amount/reason/version theo command; 409 giữ dữ liệu nhập và yêu cầu tải bản mới, không tự duyệt lại. Trường người/thời điểm do server ghi, không cho sửa trên form.
- FE07.S4: motion không thay thế phản hồi trạng thái; reduced-motion, focus và loading/empty/error theo DESIGN-DIRECTION.md/MOTION.md. Đây là plan, chưa nghiệm thu UI runtime.
