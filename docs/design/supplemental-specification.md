# 19. Đặc tả bổ sung và đồng bộ thiết kế — 07/10/2026

## 19.1. Nguồn chuẩn và phạm vi

Tên thực thể và 288 thuộc tính của 38 bảng gốc giữ theo DOCX chủ dự án cung cấp. Quyết định trực tiếp của chủ dự án có ưu tiên đối với stack và C01–C09. F01–F24 đều thuộc phạm vi; bốn bảng bổ sung bên dưới phục vụ duyệt phí và thông báo. Đây là thiết kế, chưa có migration, CRUD, Keycloak hoặc frontend nghiệp vụ hoàn chỉnh. API hiện có scaffold và hai health endpoints. Nhãn * hoặc OPEN trong hình nguồn cũ chỉ có giá trị lịch sử; dùng canvas UML đã đồng bộ khi triển khai.

Stack: Python 3.13, FastAPI, PostgreSQL 17; React/TypeScript/Vite, React Router, TanStack Query, React Hook Form/Zod; Keycloak OIDC Authorization Code + PKCE S256. Hosting và nơi triển khai còn cần quyết định. CI/CD hiện có hợp đồng build/publish image; publish không đồng nghĩa deploy.

## 19.2. Danh mục bổ sung và quy ước dữ liệu

Giữ 38 bảng gốc; đề xuất thêm ChargeAssessment, Notification, NotificationDelivery và NotificationPreference. Tên bảng vật lý snake_case số ít: charge_assessment, notification, notification_delivery, notification_preference. Không tạo thêm Report và ExportJob đồng nghĩa với ReportJob. Không lưu balance hoặc overdue như nguồn chân lý.

ChargeAssessment: id UUID PK; reader_id FK Reader NOT NULL; return_event_id FK ReturnEvent NOT NULL; kind DAMAGE/LOST; proposed_amount numeric(14,0) >=0; reason và proposed_by bắt buộc; status PENDING/ASSESSED/CLOSED_NO_CHARGE; approved_amount, decided_by, decided_at, decision_reason, fine_charge_id có thể NULL khi PENDING; version integer >0 mặc định 1; created_at; UNIQUE(return_event_id,kind), UNIQUE(fine_charge_id). ASSESSED yêu cầu approved_amount>0, người/thời điểm/lý do quyết định và FineCharge tương ứng; CLOSED_NO_CHARGE yêu cầu approved_amount=0, thông tin quyết định và không có FineCharge.

Notification: id PK; event_id FK OutboxEvent có thể NULL; reader_id FK Reader; kind READY/OVERDUE; reservation_id FK Reservation có thể NULL; summary; read_at có thể NULL; dedupe_key UNIQUE; created_at.

NotificationDelivery: id PK; notification_id FK Notification; channel EMAIL; status QUEUED/SENDING/DELIVERED/FAILED/SKIPPED; job_id FK Job; provider_message_id, delivered_at, last_error_code có thể NULL; UNIQUE(notification_id,channel).

NotificationPreference: reader_id PK/FK Reader; email_consent mặc định false; changed_by FK Account; updated_at. Có địa chỉ email không đồng nghĩa đã đồng ý nhận nhắc.

UUID bất biến; timestamp UTC/timestamptz, nghiệp vụ Asia/Ho_Chi_Minh; VND numeric(14,0), truyền API bằng chuỗi số nguyên. Partial UNIQUE LoanItem(copy_id) WHERE closed_at IS NULL; ReturnEvent.loan_item_id UNIQUE. Reservation có UNIQUE có điều kiện cho reader/edition đang QUEUED hoặc READY và copy_id cho Reservation READY; BookCopy tương ứng phải HELD. FK không cascade xóa lịch sử. Category không có chu trình; BookCopy barcode duy nhất; ISBN chuẩn hóa duy nhất khi có.

## 19.3. Quyền và xác thực

Vai trò là tập permission, không kế thừa quyền mặc nhiên. Khách chỉ đọc catalog công khai; độc giả có own-scope cho lịch sử, dư nợ, đặt/hủy giữ chỗ và thông báo. Thủ thư xử lý danh mục, thẻ, lưu thông, đề xuất phí và thu; Quản lý quyết định phí, miễn/đảo ledger, quy định, báo cáo và CSV. Admin hệ thống quản trị Account/Role; quyền backup/restore dành cho permission vận hành được gán rõ, không suy ra từ tên role.

Keycloak xác thực; Account/AccountRole/RolePermission của ứng dụng phân quyền. API kiểm issuer, audience, chữ ký, expiry rồi lookup Account bằng issuer+subject, kiểm Account đang hoạt động, permission và scope. Token phía trình duyệt chỉ lưu trong bộ nhớ. Tắt tự đăng ký và JIT; nhân viên cấp/liên kết tài khoản độc giả có sẵn. Không nhận actor/approvedBy/role đặc quyền từ client. Khóa Account chặn ngay ở API; tác vụ khóa provider có retry/reconciliation và không thay thế kiểm tra ứng dụng.

Mã quyền chính: catalog.read/write, reader.read/write, card.issue, eligibility.read, loan.checkout/renew, return.create, reservation.read/create/cancel/pickup, finance.read, assessment.propose/decide, payment.collect, charge.waive, ledger.reverse, report.read, export.create/download, policy.write/approve, account.provision_reader/manage, role.manage, acquisition.write/approve, copy.dispose, backup.create, restore.request/approve, job.read/replay, notification.read, preference.write. Job/report/provision chỉ xem khi có quyền loại job và ownership phù hợp. Report/export lấy owner từ ReportJob.requested_by qua job_id; provision dùng Job.payload.requesterAccountId do server ghi theo ProvisionJobPayload. Job không có cột requested_by. auth_version vô hiệu cache quyền ứng dụng, không tự vô hiệu JWT Keycloak.

## 19.4. Duyệt phí hỏng/mất và nhận trả

Thủ thư nhận trả GOOD/DAMAGE hoặc ghi mất LOST. GOOD ghi ReturnEvent(return_kind=RETURNED, condition=GOOD); DAMAGE ghi RETURNED/DAMAGED; LOST ghi return_kind=LOST và condition=NULL vì chưa nhận lại cuốn. Command condition và enum lưu trữ có ánh xạ rõ, không đổi enum gốc.

Trong một transaction, khóa theo thứ tự BookEdition → Reader → BookCopy → Loan/LoanItem → Reservation → Charge/Payment; nhóm không dùng được bỏ qua, không đảo thứ tự. Đóng LoanItem, tạo ReturnEvent, cập nhật copy: tốt AVAILABLE hoặc HELD theo FIFO, hỏng REPAIR, mất LOST. Phí trễ tạo theo snapshot C08; DAMAGE/LOST tạo ChargeAssessment PENDING có đề xuất số tiền và lý do. Trả không bị chặn bởi nợ, thẻ hết hạn hoặc PENDING.

PENDING → ASSESSED khi Quản lý quyết định amount>0: tạo đúng một FineCharge và liên kết. PENDING → CLOSED_NO_CHARGE khi amount=0: ghi lý do, không tạo khoản phí bằng 0. Hai trạng thái cuối không được duyệt lại; sửa tiền sau đó qua miễn/đảo ledger có audit. PENDING chặn checkout, renew và reservation-create; proposed_amount chưa là dư nợ. Checkout/renew/hold và tạo/duyệt assessment cùng khóa Reader để loại bỏ race.

Retry cùng Idempotency-Key và payload trả biên nhận cũ; key khác payload hoặc expectedVersion cũ trả 409. Tìm lại sách mất không mở lại mục mượn hoặc tự đảo phí.

## 19.5. Hợp đồng API

Hợp đồng máy đọc được nằm tại docs/design/openapi.json: OpenAPI 3.1.0, 75 operation nghiệp vụ planned và hai health endpoints hiện có. Request command dùng camelCase; entity response giữ snake_case của DOCX, DTO tổng hợp được đặt tên riêng. Không expose writable full Account/Job/BackupManifest hoặc khóa object private.

Nhóm endpoint /api/v1: book-editions/authors/publishers/categories/copies/media; readers/cards/eligibility; loans/returns/renewals/reservations; charge-assessments và decisions; payments/waivers/ledger-reversals; reports/export-jobs; policies; accounts/roles; acquisitions; backup-manifests/restores/jobs; auth/me; me/loans/reservations/fine-charges/notifications/notification-preference. API đang thiết kế chưa được coi là endpoint runtime đã tồn tại.

POST tạo tài nguyên 201 + Location; job 202 + Location. UUID đúng định dạng, cursor mặc định 20/tối đa 100; tiền chuỗi số nguyên. returnedAt/processedBy/approvedBy do server ghi. Lỗi có code/message/details/request_id: 401 token, 403 permission/Account, 404 đối tượng ngoài scope, 409 cạnh tranh/idempotency, 422 validation/eligibility, 429 rate limit, 503 dependency. Chưa có cột version trong nguồn thì không tự dùng expectedVersion như một cột DB mới; dùng trạng thái có điều kiện/khóa transaction hoặc đặc tả extension riêng.

CSV chỉ Quản lý; bộ lọc/scope/asOf được snapshot. Download kiểm lại quyền trước phát URL ngắn hạn; signed URL đã phát có cửa sổ hiệu lực đến expiry. Job không nhận SQL/path/URL tùy ý.

## 19.6. Sự kiện và tác vụ nền

OutboxEvent ghi cùng transaction nghiệp vụ. Payload envelope v1: schemaVersion, eventId, eventType, occurredAt, requestId, aggregateType, aggregateId, data; eventId=OutboxEvent.id. Không tùy ý thêm cột nguồn để lưu envelope.

Các sự kiện: reservation.ready.v1, reservation.expired.v1, loan.item.returned.v1, charge.assessment.decided.v1, reader.overdue.daily.v1, report.requested.v1, account.reader.provision.requested.v1, backup.requested.v1 và restore.requested.v1.

Dispatcher tạo Job và đánh dấu processed_at trong cùng transaction, UNIQUE dedupe_key. Riêng restore: Job QUEUED với RestoreJobPayload.approvalStatus=PENDING không được claim/lease. restore.approve có reason ghi approvedBy/approvedAt từ server dưới khóa Job và chuyển payload APPROVED; worker kiểm lại approval, checksum và target allowlist trước pg_restore. Metadata thiếu/sai bị từ chối; không thêm enum hoặc cột Job mới. Worker lấy lease bằng SKIP LOCKED, commit trước khi gọi provider, retry hữu hạn; không hứa exactly-once email. READY giữ hạn 3 ngày từ readyAt, retry không gia hạn; trước gửi kiểm trạng thái/expiry. Nhắc quá hạn tổng hợp một độc giả/ngày/kênh theo consent. Lịch 08:00 và thông số lease/retry là mặc định đề xuất trong kế hoạch, chưa là chỉ tiêu đã được người dùng duyệt.

## 19.7. Bảo mật và vận hành

Ranh giới tin cậy gồm browser/API, API/Keycloak, API/DB, worker/provider và private artifact. Chặn BOLA qua scoped query; chặn nâng quyền qua permission DB; chống SQL injection bằng bind parameter; không render HTML chưa lọc; không log token/PII đầy đủ; upload kiểm MIME/nội dung, giới hạn cần chốt. Không cho client điều khiển target restore, bucket hoặc URL provider.

Production DB role ứng dụng không được DDL/drop; migration chạy riêng. Backup mã hóa, lưu checksum và restore drill vào môi trường cô lập; không tự cutover production. Retention, upload size, hosting, RPO/RTO và ngân sách vẫn cần xác nhận; chưa tuyên bố đạt chứng nhận hay NFR.

## 19.8. Giao diện và nghiệm thu

Board wireframe docs/plan/frontend/wireframes.html có 12 màn hình desktop/mobile: catalog, quầy mượn, trả, duyệt/thu phí, portal, độc giả/thẻ, giữ chỗ/gia hạn, báo cáo/CSV, quy định, tài khoản/quyền, nhập/thanh lý và vận hành. Bố cục theo hướng thư viện giấy ấm; scanner/bảng ưu tiên desktop, tác vụ chính ưu tiên mobile. Đây là minh họa, chưa là frontend chạy thật.

Mỗi module cần loading/empty/error/pending/success/conflict; lỗi cạnh trường và tóm tắt có chữ, keyboard/focus rõ; motion có mục đích phản hồi và hỗ trợ reduced-motion. Không dùng animation để trì hoãn phản hồi lưu.

Ma trận nghiệm thu tại docs/quality/acceptance-matrix.md truy vết F01–F24; mọi test nghiệp vụ hiện Not run. Ưu tiên tranh chấp một copy, duyệt phí trùng, retry sau commit, READY hết hạn, own-scope/BOLA, khóa tài khoản với token còn hạn, signed download quyền bị thu hồi, consent và crash worker. Kiểm tra tài liệu không thay cho test runtime.

## 19.9. Thay đổi và điểm còn mở

Đã sửa scope cũ F21–F24 chưa duyệt; stack .NET/NestJS chưa chốt; JIT; phí hỏng/mất ghi trực tiếp; manifest binary cũ; liên kết UI cũ. Bổ sung DB/permission/API/identity/assessment/events/threat model/acceptance/wireframes và 14 khung UML trong cùng canvas.

N01/N02 đã có quyết định; N06 chỉ còn in/Excel/PDF/chỉ số nâng cao. N03 uniqueness Reader.email/Category.name, N04 retention/upload/hosting và N05 người giao/APPROVED cần xác nhận. N07 cần môi trường và dữ liệu đo; chưa khẳng định đạt hiệu năng. Bản DOCX gốc và nguồn tham khảo lịch sử được lưu để truy vết; không xóa schema hay hình nguồn.


## 19.10. Kết quả rà soát kiến trúc và đồng bộ

GET /api/v1/auth/me trả AuthContext gồm AccountView và tập permissions hiện tại từ AccountRole/RolePermission; Bearer JWT và Account ACTIVE là bắt buộc, không đòi permission nghiệp vụ riêng chỉ để bootstrap UI. UI không thay thế kiểm quyền API; quyền bị thu hồi phải được kiểm lại mỗi lệnh. Request validation trả cùng ErrorResponse với request_id; mã 503 dành lỗi phụ thuộc/readiness theo hợp đồng runtime.

Lớp/ERD dùng tên trường nguồn: Reader.full_name, Loan.issued_by, policy_version_id; bảng vật lý số ít; Account dùng UNIQUE(issuer,subject). Không có BookEdition.active_cover_id, Account.oidc_sub hoặc Job.requested_by trong danh mục. Một LoanItem có 0..1 ReturnEvent; 0..1 Reservation fulfilled; một Job có 0..1 ReportJob. UQ của PolicyVersion là version_no; chống chồng hiệu lực là bất biến khác.

FK chỉ chứng minh đối tượng tồn tại. Unit of Work phải kiểm thẻ/phiếu cùng độc giả, giữ chỗ đúng ấn bản/bản sao/độc giả, assessment khớp return và charge, payment allocation cùng chủ thể, READY notification đúng độc giả. CHECK trạng thái assessment cần IS NULL/IS NOT NULL rõ ràng, không để NULL làm biểu thức CHECK vượt qua.

UML editable đã sửa trực tiếp tại library-uml.drawio, vẫn một canvas/94 khung/3.020 cells. DOCX đã thay 73 hình nguồn bằng ảnh tái xuất từ cell hiện hành và giữ ba hình ChargeAssessment cùng logic. Routing cạnh xấp xỉ do bộ xuất ngoài ứng dụng Draw.io; các snapshot live phải được kiểm chứng riêng. N05 trạng thái APPROVED/người giao phiếu nhập vẫn cần xác nhận; không tự thêm vào enum DRAFT/POSTED/CANCELLED.
