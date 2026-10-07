# Hợp đồng API nghiệp vụ

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Artifact và trạng thái

[openapi.json](openapi.json) là hợp đồng thiết kế OpenAPI3.1, không phải export của API runtime. `/health/live` và `/health/ready` là phần hiện có; các đường dẫn `/api/v1` là planned. Giữ OpenAPI3.1 cho toolchain FastAPI/client hiện hành; không nâng3.2 chỉ vì có phiên bản mới.

Tên JSON request nghiệp vụ camelCase theo bảng API DOCX; thuộc tính entity response theo snake_case từ từ điển nguồn. Không dùng hai cách viết cùng một trường trong một payload. Cấu hình serializer/alias khi triển khai; frontend sinh kiểu từ schema, không tự đoán.

UUID/path bắt buộc đúng định dạng; datetime response UTC RFC3339; VND chuỗi số nguyên, kiểm tra >0/<=dư trong service; query cursor default20/max100. Mọi enum/constraint phức tạp giữ nguồn x-db-constraint trong entity schema và kiểm lại khi viết model.

## Lỗi và đồng thời

ErrorResponse gồm code/message/details/request_id. 401 token;403permission/account;404resource theo scope;409duplicate/version/idempotency;422validation/eligibility;429rate;503provider/DB unavailable. Không trả stacktrace. Scope actor+operation+Idempotency-Key; hash canonical payload, commit response và dữ liệu cùng transaction. Cùng key khác payload409; request đang chạy409+Retry-After. expectedVersion khi tài nguyên có version/token đọc được; danh mục không có version dùng khóa/conditional state. Không tự thêm cột version vào schema nguồn cho PATCH và lệnh nhạy cảm; phiên bản stale không ghi một phần.

## Quyền và tác động

Mỗi operation có x-permission, x-functions và x-status=planned trong OpenAPI; kiểm tra [ma trận quyền](permission-matrix.md). GET catalog anonymous; reader/me scoped, không lấy readerId từ query để bypass. response tài chính/auth/PII không là schema public. Quyền tải export được kiểm lại ngay trước signedURL; URL ngắn hạn vẫn có cửa sổ truy cập đến expiry, không hứa thu hồi tức thời signedURL đã phát.

POST tạo tài nguyên trả201+Location; job202+Location. Mượn/thu/nhập/post/return/approval phải idempotent; pending button ở UI không thay thế server. returnedAt/actor/approvedBy được server ghi. Job payload không nhận URL/SQL/path tùy ý.

## Cách dùng và thay đổi

Contract dùng schema theo tài nguyên, có request DTO riêng cho command; không expose writable full entity. Entity response gồm cột nguồn nhưng server phải lọc/redact theo scope, không trả whole Account/JobPayload cho portal. Media/ReportJob response chỉ metadata hợp lệ, không encrypted_object_key hoặc credentials. `/me` routes là scope alias server, không thay ownership.

CI tương lai validate OpenAPI và drift generatedclient; contract hiện tại được rà cấu trúc/reference, chưa có business runtime. Các policy rules dynamic và chuyển trạng thái phải bổ sung validation service, không chỉ JSONSchema.

Tham khảo: [OpenAPI](https://spec.openapis.org/oas/latest.html). Endpoint đầy đủ, request/response và permission nằm trong artifact máy đọc được bên cạnh.


N05: approval tiếp nhận chưa đồng bộ enum APPROVED với danh mục gốc; operation liên quan có x-open-question và chưa được triển khai. PublicEdition bổ sung authors/categories/cover/availability là read projection từ join, không đổi cột BookEdition.
