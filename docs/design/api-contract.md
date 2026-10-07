# Hợp đồng API nghiệp vụ

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Artifact và trạng thái

[openapi.json](openapi.json) là hợp đồng thiết kế OpenAPI3.1, không phải export của API runtime. `/health/live` và `/health/ready` là phần hiện có; các đường dẫn `/api/v1` là planned. Giữ OpenAPI3.1 cho toolchain FastAPI/client hiện hành; không nâng3.2 chỉ vì có phiên bản mới.

Tên JSON request nghiệp vụ camelCase theo bảng API DOCX; thuộc tính entity response theo snake_case từ từ điển nguồn. Không dùng hai cách viết cùng một trường trong một payload. Cấu hình serializer/alias khi triển khai; frontend sinh kiểu từ schema, không tự đoán.

UUID/path bắt buộc đúng định dạng; datetime response UTC RFC3339; VND chuỗi số nguyên, kiểm tra >0/<=dư trong service; query cursor default20/max100. Mọi enum/constraint phức tạp giữ nguồn x-db-constraint trong entity schema và kiểm lại khi viết model.

## Lỗi và đồng thời

ErrorResponse gồm code/message/details/request_id. 401 token;403permission/account;404resource theo scope;409duplicate/version/idempotency;410artifact hết hạn sau khi kiểm scope;422validation/eligibility;429rate;503provider/DB unavailable. Không trả stacktrace. Scope actor+operation+Idempotency-Key; hash canonical payload, commit response và dữ liệu cùng transaction. Cùng key khác payload409; request đang chạy409+Retry-After. expectedVersion khi tài nguyên có version/token đọc được; danh mục không có version dùng khóa/conditional state. Không tự thêm cột version vào schema nguồn cho PATCH và lệnh nhạy cảm; phiên bản stale không ghi một phần.

## Quyền và tác động

Mỗi operation nghiệp vụ có x-permission (trừ /auth/me dùng x-account-guard), x-functions và x-status=planned trong OpenAPI; kiểm tra [ma trận quyền](permission-matrix.md). GET catalog anonymous; reader/me scoped, không lấy readerId từ query để bypass. response tài chính/auth/PII không là schema public. Quyền tải export được kiểm lại ngay trước signedURL; URL ngắn hạn vẫn có cửa sổ truy cập đến expiry, không hứa thu hồi tức thời signedURL đã phát.

POST tạo tài nguyên trả201+Location; job202+Location. Mượn/thu/nhập/post/return/approval phải idempotent; pending button ở UI không thay thế server. returnedAt/actor/approvedBy được server ghi. Job payload không nhận URL/SQL/path tùy ý.

## Cách dùng và thay đổi

Contract dùng schema theo tài nguyên, có request DTO riêng cho command; không expose writable full entity. Entity response gồm cột nguồn nhưng server phải lọc/redact theo scope, không trả whole Account/JobPayload cho portal. Media/ReportJob response chỉ metadata hợp lệ, không encrypted_object_key hoặc credentials. `/me` routes là scope alias server, không thay ownership.

CI tương lai validate OpenAPI và drift generatedclient; contract hiện tại được rà cấu trúc/reference, chưa có business runtime. Các policy rules dynamic và chuyển trạng thái phải bổ sung validation service, không chỉ JSONSchema.

Tham khảo: [OpenAPI](https://spec.openapis.org/oas/latest.html). Endpoint đầy đủ, request/response và permission nằm trong artifact máy đọc được bên cạnh.


N05: approval tiếp nhận chưa đồng bộ enum APPROVED với danh mục gốc; operation liên quan có x-open-question và chưa được triển khai. PublicEdition bổ sung authors/categories/cover/availability là read projection từ join, không đổi cột BookEdition.

## Hợp đồng kiểm tra quyền dùng khi triển khai

`x-permission` luôn là một mã permission có trong ma trận; đây là metadata thiết kế, chưa tự bảo vệ runtime. Dependency xác thực/authorization phải được nối vào router/service khi triển khai. `/auth/me` chỉ yêu cầu Bearer hợp lệ và `x-account-guard=ACTIVE`, không đặt x-permission vì đây không phải permission gán Role.

- Mặc định yêu cầu `x-permission` và Account ACTIVE. `x-data-scope` diễn tả scope bổ sung; `/me/reservations` cần `reservation.read`, tra Reader từ Account, không yêu cầu quyền tạo đặt trước.
- Nếu có `x-authorization`, dùng OR giữa `rules`, AND giữa `allPermissions` trong mỗi rule, cộng điều kiện scope của rule; metadata này thay điều kiện mặc định `x-permission`. `/jobs/{id}` có nhánh vận hành và nhánh own report/export/provision; nhánh own cần permission hiện tại theo loại job. Không parse biểu thức quyền từ chuỗi văn bản. `jobTypes` là tên loại logic, BE00 phải ánh xạ allowlist sang Job.job_type.
- `x-conditional-permissions` là quyền bổ sung khi payload khớp điều kiện. Trả DAMAGE/LOST cần cả `return.create` và `assessment.propose`; kiểm trước mọi ghi DB. GOOD chỉ cần `return.create`. Nợ/thẻ hết hạn/PENDING không chặn trả, nhưng không bỏ qua kiểm tra quyền.
- `/export-jobs/{id}/download` kiểm scope trước khi trả410 cho artifact hết hạn; job chưa xong409, ngoài scope404. SignedURL có TTL không vượt hạn artifact.

Các extension phải được kiểm tra bằng ca authorization ở BE00/BE01/BE10; OpenAPI không thực thi chúng. Runtime `/health/live` trả `ok`, readiness200 trả `ready`, readiness503 trả `not_ready`; schema phân biệt từng phản hồi. Các route nghiệp vụ vẫn planned.

Ownership của report/export lấy từ `ReportJob.requested_by` qua `ReportJob.job_id`; Job gốc không có cột requester. Provision dùng `ProvisionJobPayload` nội bộ trong `Job.payload`, với `requesterAccountId` do server lấy từ Account đã xác thực. Đây là schema JSON bổ sung, không đổi cột Job và không thêm trường writable vào ProvisionRequest. Metadata thiếu/sai phải fail closed ở nhánh own; không suy diễn quyền từ Reader hoặc email. Mỗi loại job logic được ánh xạ allowlist tại BE00/BE01/BE10.

## Projection phiên và điều kiện thực thi restore

`GET /auth/me` trả `AuthContext` gồm `account: AccountView` và `permissions`, tính từ quan hệ role/permission hiện tại trong DB. Không thêm trường Account; frontend dùng projection cho menu FE01 và xử lý403/khóa tài khoản ở các request sau. Backend không tin permissions do client gửi hoặc cache UI.

Restore tạo `RestoreJobPayload` nội bộ với approvalStatus=PENDING và dữ liệu duyệt NULL. Job giữ trạng thái nguồn QUEUED; trạng thái duyệt nằm riêng trong payload. Dispatcher/worker loại PENDING khỏi nhóm được thực thi. Lệnh duyệt khóa Job, kiểm restore.approve, trạng thái và lý do; ghi approvedBy/approvedAt từ phiên rồi chuyển APPROVED. Retry cùng key trả kết quả đã lưu; lệnh khác sau duyệt trả409. Trước pg_restore, worker kiểm lại approval, manifest/checksum và target allowlist; metadata thiếu/sai bị từ chối. `RestoreJobAccepted` thể hiện trạng thái duyệt; `JobView.approval_status` chỉ chiếu trường này cho restore. Đây là hợp đồng JSON bổ sung, không thêm cột hoặc enum Job.
