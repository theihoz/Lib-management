# FE01 — Đăng nhập và điều hướng

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F16, F21
**Phụ thuộc:** FE00, BE01

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/login, /staff, /me và trang 403.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE01.1 | Tích hợp Keycloak public client Authorization Code PKCE, token chỉ trong bộ nhớ | Bố cục/component, state và hợp đồng màn hình |
| FE01.2 | Menu theo AuthContext.permissions từ /auth/me, auth guard và phiên hết hạn | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE01.3 | Liên kết callback/logout, xử lý network error không tạo vòng lặp login | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE01.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- API vẫn quyết định quyền.
- token không localStorage.
- tài khoản bị khóa thoát vùng có quyền.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Điều hướng theo vai trò

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Menu nhóm Quầy, Danh mục, Quản lý, Vận hành theo permission; header nhỏ với người dùng và breadcrumb. Login tập trung vào action đăng nhập và trạng thái lỗi, không hero.

### Motion theo hành động

Marker active180ms; route nhân viên180ms, portal280ms; phiên hết hạn hiện thông báo rõ, không lặp redirect hoặc exit chờ animation.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Xây shell/menu route states trước; thêm auth callback và trạng thái phiên; cuối cùng nối transition không remount shell.

- FE01.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE01.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE01.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Đổi vai trò không flash menu trái quyền; token/auth lỗi không bị che bởi loading; focus heading hoặc thông báo lỗi đúng.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
