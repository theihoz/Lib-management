# Ma trận quyền và phạm vi dữ liệu

**Ngày đồng bộ:** 2026-11-03 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Nguyên tắc

Áp dụng [quyết định 03/11/2026 — phân quyền theo tên vai trò](../plan/decisions.md#quyết-định-03112026--phân-quyền-theo-tên-vai-trò), thay bản tách nhiệm vụ trước đó. Vai trò nhân viên tích lũy theo tên: Thủ thư làm nghiệp vụ quầy; Quản lý có mọi quyền của Thủ thư cộng duyệt phí, miễn/đảo, báo cáo, CSV, quy định, duyệt nhập/thanh lý; Admin hệ thống có toàn bộ 39 permission. Admin vận hành lo sao lưu/khôi phục, tác vụ nền và xem báo cáo, không chạm quầy hay hồ sơ độc giả. Độc giả chỉ thấy dữ liệu của mình. API kiểm tra Account ACTIVE, permission và scope mỗi request; UI chỉ phản ánh quyền và ẩn màn `/staff`, `/manager` với tài khoản chỉ có quyền độc giả. Worker dùng service identity nội bộ với quyền xử lý job, không đăng nhập như độc giả.

| Permission | Độc giả | Thủ thư | Quản lý | Admin hệ thống | Admin vận hành | Scope/điều kiện |
| --- | --- | --- | --- | --- | --- | --- |
| catalog.read | Có, kể cả anonymous | Có | Có | Có | Có | Dữ liệu công khai, không PII |
| catalog.write / media.write | Không | Có | Có | Có | Không | F01–05/F15; guard tham chiếu |
| reader.read / reader.write / card.issue | Chỉ own read | Có | Có | Có | Không | F06/F17/F18; mục đích phục vụ độc giả |
| eligibility.read | Own | Có | Có | Có | Không | Preview không bảo đảm quyền checkout |
| loan.checkout / return.create / loan.renew | Không | Có | Có | Có | Không | Return không chặn bởi debt/card/assessment |
| reservation.read / create / cancel | Own | Có | Có | Có | Không | readerId từ session khi own |
| reservation.pickup | Không | Có | Có | Có | Không | READY đúng người, chưa expiry |
| finance.read | Own dư/lịch sử | Có | Có | Có | Không | Không lộ độc giả khác |
| assessment.propose / payment.collect | Không | Có | Có | Có | Không | Reason/idempotency |
| assessment.decide / charge.waive / ledger.reverse | Không | Không | Có | Có | Không | Reason bắt buộc, audit; không delete ledger |
| report.read | Không | Có | Có | Có | Có | Báo cáo tổng hợp |
| overdue.read | Không | Có | Có | Có | Không | Danh sách có PII độc giả |
| export.create / export.download | Không | Không | Có | Có | Có | Kiểm tra lại quyền, TTL |
| policy.write / policy.approve | Không | Không | Có | Có | Không | ACTIVE bất biến |
| account.provision_reader | Không | Có | Có | Có | Không | Reader có sẵn; không cấp role staff/admin |
| account.manage / role.manage | Không | Không | Không | Có | Không | Quyền không tự tăng từ JWT/client |
| acquisition.write | Không | Có | Có | Có | Không | Draft |
| acquisition.approve / copy.dispose | Không | Không | Có | Có | Không | Guard loan/hold, reason |
| backup.create / restore.request / restore.approve | Không | Không | Không | Có | Có | Target cô lập allowlist; không tự production cutover |
| job.read | Không | Không | Có | Có | Có | Allowlist job type |
| job.replay | Không | Không | Không | Có | Có | Allowlist job type, audit replay |
| notification.read / preference.write | Own | Không | Không | Own | Không | Consent do chủ thể chọn |

Nguồn mã: `ROLES` trong `apps/api/src/lib_management/identity/rbac_seed.py`; bản demo sao chép sang `apps/web/src/mock/personas.ts`. `seed-rbac` chỉ thêm grant, không gỡ grant đã có.

Keycloak role claim không trực tiếp quyết định permission DB. Bootstrap quyền theo bảng này là thiết kế; owner vận hành được gán qua quy trình ngoài API công khai.

## Thu hồi và xử lý lỗi

401 khi token không hợp lệ; 403 khi Account bị khóa/thiếu permission. Đối tượng của người khác có thể trả 404 qua truy vấn scoped để tránh tiết lộ tồn tại; endpoint quản trị có quyền truy vấn trả 403 khi không được action. auth_version trong Account dùng cho cache invalidation nhưng không tự thay tính hiệu lực JWT Keycloak. Không cache quyền dài hạn nếu chưa có đường thu hồi đã kiểm chứng.

## Nghiệm thu

Kiểm thử mỗi ô từ chối, đổi readerId và revoked permission trước download/replay; khóa Account với JWT còn hạn; staff không cấp quyền admin. Kiểm thử trường hợp worker không truy cập PII dư thừa.


GET job riêng của report/provision được cho phép theo permission loại tác vụ và requestedBy ownership; job.read toàn hệ thống/replay vẫn dành quyền vận hành. Không dùng ownership để cấp quyền restore.

## Đối chiếu với extension OpenAPI

`x-account-guard=ACTIVE` trên `/auth/me` là điều kiện Account hiện tại, không thêm vào RolePermission và không có x-permission. `x-permission` chứa mã đơn; `x-authorization` xác định nhánh quyền thay thế và ownership cho job. Một nhánh own cần đồng thời permission hiện tại, đúng loại job allowlist và ownershipSource của loại job bằng Account.id; quyền vận hành vẫn kiểm allowlist. Export job dùng `export.create`, report job dùng `report.read`, provision job dùng `account.provision_reader`. Không cấp quyền xem backup/restore/replay chỉ vì đã tạo job.

`/me/reservations` dùng `reservation.read`; đọc không đòi `reservation.create`. Trả DAMAGE/LOST yêu cầu bổ sung `assessment.propose`, kiểm cùng `return.create` trước transaction để tránh lưu ReturnEvent rồi thất bại khi tạo assessment. “Return không chặn” nói về điều kiện thẻ/nợ/PENDING, không cho người thiếu quyền nhận trả. GOOD không cần `assessment.propose`.

Nguồn ownership: report/export dùng `ReportJob.requested_by` và FK `job_id`; provision dùng `Job.payload.requesterAccountId` theo schema nội bộ `ProvisionJobPayload`. Job không có cột `requested_by`. Server ghi metadata sau xác thực trong cùng transaction tạo job; client không được chọn requester. Metadata thiếu/sai không đủ điều kiện nhánh own.
