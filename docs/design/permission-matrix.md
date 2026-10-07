# Ma trận quyền và phạm vi dữ liệu

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Nguyên tắc

Vai trò là tập permission, không phải thứ bậc kế thừa. Admin hệ thống không tự có quyền thu/miễn/restore. API kiểm tra Account ACTIVE, permission và scope mỗi request; UI chỉ phản ánh quyền. Worker dùng service identity nội bộ với quyền xử lý job, không đăng nhập như độc giả.

| Permission | Độc giả | Thủ thư | Quản lý | Admin hệ thống | Admin vận hành | Scope/điều kiện |
| --- | --- | --- | --- | --- | --- | --- |
| catalog.read | Có, kể cả anonymous | Có | Có | Có | Có | Dữ liệu công khai, không PII |
| catalog.write / media.write | Không | Có | Cấp thêm rõ | Không | Không | F01–05/F15; guard tham chiếu |
| reader.read / reader.write / card.issue | Chỉ own read | Có | Read theo nghiệp vụ | Không | Không | F06/F17/F18; mục đích phục vụ độc giả |
| eligibility.read | Own | Có | Có | Không | Không | Preview không bảo đảm quyền checkout |
| loan.checkout / return.create / loan.renew | Không | Có | Cấp thêm rõ | Không | Không | Return không chặn bởi debt/card/assessment |
| reservation.read / create / cancel | Own | Có khi hỗ trợ | Cấp thêm rõ | Không | Không | readerId từ session khi own |
| reservation.pickup | Không | Có | Cấp thêm rõ | Không | Không | READY đúng người, chưa expiry |
| finance.read | Own dư/lịch sử | Có | Có | Không | Không | Không lộ độc giả khác |
| assessment.propose / payment.collect | Không | Có | Cấp thêm rõ | Không | Không | Reason/idempotency; không tự duyệt phí |
| assessment.decide / charge.waive / ledger.reverse | Không | Không | Có | Không | Không | Reason bắt buộc, audit; không delete ledger |
| report.read / overdue.read | Không | Có giới hạn báo cáo nghiệp vụ | Có | Không | Không | Staff không xuất CSV mặc định |
| export.create / export.download | Không | Không | Có | Không | Không | Kiểm tra lại quyền, TTL |
| policy.write / policy.approve | Không | Không | Có | Không | Không | ACTIVE bất biến |
| account.provision_reader | Không | Có | Cấp thêm rõ | Có | Không | Reader có sẵn; không cấp role staff/admin |
| account.manage / role.manage | Không | Không | Không | Có | Không | Quyền không tự tăng từ JWT/client |
| acquisition.write | Không | Có | Cấp thêm rõ | Không | Không | Draft |
| acquisition.approve / copy.dispose | Không | Không | Có | Không | Không | Guard loan/hold, reason |
| backup.create / restore.request / restore.approve | Không | Không | Không | Không | Có | Target cô lập allowlist; không tự production cutover |
| job.read / job.replay | Không | Notification theo quyền hạn chế | Không mặc định | Không | Có | Allowlist job type, audit replay |
| notification.read / preference.write | Own | Không | Không | Không | Không | Consent do chủ thể chọn |

Các ô “cấp thêm rõ” không là quyền mặc định. Keycloak role claim không trực tiếp quyết định permission DB. Bootstrap quyền theo bảng này là thiết kế; owner vận hành được gán qua quy trình ngoài API công khai.

## Thu hồi và xử lý lỗi

401 khi token không hợp lệ; 403 khi Account bị khóa/thiếu permission. Đối tượng của người khác có thể trả 404 qua truy vấn scoped để tránh tiết lộ tồn tại; endpoint quản trị có quyền truy vấn trả 403 khi không được action. auth_version trong Account dùng cho cache invalidation nhưng không tự thay tính hiệu lực JWT Keycloak. Không cache quyền dài hạn nếu chưa có đường thu hồi đã kiểm chứng.

## Nghiệm thu

Kiểm thử mỗi ô từ chối, đổi readerId và revoked permission trước download/replay; khóa Account với JWT còn hạn; staff không cấp quyền admin. Kiểm thử trường hợp worker không truy cập PII dư thừa.


GET job riêng của report/provision được cho phép theo permission loại tác vụ và requestedBy ownership; job.read toàn hệ thống/replay vẫn dành quyền vận hành. Không dùng ownership để cấp quyền restore.
