# Thiết kế tài khoản và xác thực Keycloak

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Thành phần và trách nhiệm

Keycloak quản lý mật khẩu, đăng nhập, email verification, refresh/logout và khóa danh tính. Ứng dụng quản lý Account/Role/Permission và mapping Reader. Account có issuer+subject UNIQUE; reader_id nullable cho nhân viên. Không nhận identity qua readerId/email do client gửi.

Realm riêng Lib-management; public client lib-management-web dùng Authorization Code+PKCE S256, standard flow; tắt implicit/password grant và self-registration. Redirect URI/origin allowlist chính xác cho local/staging/prod, không wildcard production. API audience lib-management-api cấu hình qua audience mapper. Service provisioner có client riêng, quyền quản trị Keycloak tối thiểu và secret chỉ ở server.

## Luồng đăng nhập và phiên

1. Browser redirect đến issuer cố định với state/nonce và PKCE; callback đổi code bằng adapter.
2. Token giữ trong memory; reload dùng adapter kiểm tra phiên, không localStorage.
3. API kiểm tra chữ ký theo JWKS, algorithm allowlist, issuer/audience/exp/nbf. Refresh JWKS một lần khi kid mới, lỗi issuer không thử issuer khác. Clock skew mặc định đề xuất30s, access token5phút; ghi thành cấu hình chờ môi trường triển khai.
4. API lookup Account ACTIVE theo issuer+subject và quyền DB; không auto-create JIT.
5. Logout gọi provider và xóa memory; account khóa trong ứng dụng có hiệu lực ngay tại request kế tiếp. Token bị đánh cắp có thể còn hợp lệ đến exp nếu Account vẫn ACTIVE; dùng quy trình revoke/disable phù hợp, không tuyên bố logout lập tức vô hiệu mọi bearer.

## Cấp tài khoản độc giả và lỗi liên hệ thống

Nhân viên có account.provision_reader chỉ chọn Reader đã có và email liên hệ xác nhận; không được gán role staff/admin. Tạo Keycloak identity qua job bền vững, required actions verify email/update password; không trả mật khẩu tạm trong API/log. Khi provisioning thành công, ghi issuer/subject/reader_id; uniqueness chặn liên kết trùng. Lỗi Keycloak không commit Account ACTIVE giả; Job lưu trạng thái và retry/dedupe theo reader+operation. Tài khoản ngoài DB không được dùng API; orphan bên provider được reconcile có audit, không tự xóa khi chưa xác định chủ sở hữu.

Khóa ứng dụng cập nhật Account trong transaction trước; disable Keycloak qua job sau commit. Khóa provider thất bại không mở lại Account. Xóa nhân viên/độc giả có lịch sử bằng đổi trạng thái, không xóa FK.

## Cấu hình và nghiệm thu

Keycloak DB/credentials độc lập, không dùng credential app DB; local start-dev chỉ phát triển, production tối ưu TLS/proxy/hostname và image pin. Không ghi secret vào .env.example. Kiểm thử issuer/audience/kid rotation/expiry, user ngoài allowlist, self-assert admin, refresh failure và provision retry; backend hiện chưa tích hợp các luồng này.

