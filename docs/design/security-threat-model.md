# Mô hình nguy cơ bảo mật

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Tài sản và vùng tin cậy

Tài sản: PII độc giả, phiên/tài khoản, quyền, ledger, lịch sử, artifact báo cáo, backup. Browser không đáng tin; API là boundary kiểm permission; Keycloak/R2/SMTP là external adapters; PostgreSQL/worker là nội bộ. DB không mở Internet; credential và backup không đến browser.

| Nguy cơ | Luồng | Biện pháp thiết kế | Cách kiểm chứng dự kiến |
| --- | --- | --- | --- |
| Token giả/sai audience | Browser→API | issuer/audience/algorithm/JWKS cố định | JWT sai chữ ký/kid/exp không vào service |
| Đổi readerId để xem người khác | Portal→Reader/History/Hold | Scoped query theo Account.reader_id | AccountA truy cập B bị chặn cả API |
| Tự claim admin/cấp quyền | JWT/role endpoint | Permission DB, không JIT, account.provision_reader giới hạn | Staff không grant admin; admin hệ thống không tự có finance |
| Hai quầy mượn/thu trùng | API→DB | Locks/UQ/idempotency/hash payload | Requests cạnh tranh; invariant và ledger |
| CSV formula/PII leak | Export→browser | Escape =,+,-,@, artifact private, recheck permission | Formula input, revoked permission, expired410 |
| Upload giả ảnh/path injection | Browser→R2 | Server sinh key; size/MIME/magic bytes/hash, intent TTL | SVG/script/file đuôi giả, key/path tùy ý bị chặn |
| Replay event/email | Outbox→worker→SMTP | Dedupe, lease, stale check, consent | Crash/timeouts không tạo DB trùng; không kéo hạn READY |
| SSRF qua webhook/restore URL | Job/request→external | Không nhận URL/path/SQL tùy ý; adapter/target allowlist | Payload URLlocalhost/metadata bị từ chối |
| Lộ secret/log PII | API/worker/logs | Redact token/email/rawCSV/signedURL, least privilege | Inspect logs/fixtures không secrets |
| Restore phá dữ liệu đang dùng | Operations→DB | Approval, checksum, isolated allowlist, không auto promote | Failedrestore không thay target production |
| XSS/CORS/CSRF | Browser/session | Render text safe, không HTML raw; CSP khi deploy; origin allowlist; CSRF nếu dùng cookie | Stored malicious title, wrongorigin, session tests |
| Lạm dụng search/export | Public API/Job | Shared limiter, bounded pagination/jobs, rate429 | Multi-instance không mỗi processcounter |

## Giới hạn và điểm cần chốt

Audit12 tháng, artifact24h, idempotency7 ngày, backupRPO24h/RTO4h là mục tiêu/retention đề xuất trong DOCX, chưa là nghĩa vụ pháp lý hoặc kết quả đo. Chốt với thư viện trước production. TLS/hostname/CSP/runtime secrets phụ thuộc hosting chưa chọn. Không tuyên bố tuân thủ toàn bộ ASVS hoặc đã có security assessment.

## Quy trình

Mỗi thay đổi API/schema/quyền bổ sung threat/ca nghiệm thu liên quan; incident/replay/restore có audit. Account vận hành giới hạn riêng; thay credential có checklist rotation và smoke check tại staging. Security checks là kế hoạch, không chứng minh code health đã bảo vệ nghiệp vụ.

Tham khảo: [OWASP Threat Modeling](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html).
