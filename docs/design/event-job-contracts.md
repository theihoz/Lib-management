# Hợp đồng sự kiện và tác vụ nền

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Envelope và phiên bản

OutboxEvent giữ đúng các cột nguồn; payload JSON có schemaVersion=1, eventId, eventType, occurredAt, requestId, aggregateType, aggregateId và data. eventId bằng OutboxEvent.id. Thêm trường tương thích giữ version; đổi nghĩa hoặc bỏ field phải có v2 và consumer tương thích trước producer. Envelope là hợp đồng bổ sung, không khẳng định đã có JSON Schema/migration runtime.

| Event v1 | Producer | data tối thiểu | Consumer và dedupe |
| --- | --- | --- | --- |
| reservation.ready.v1 | Transaction phân bổ | reservationId,readerId,editionId,readyAt,readyExpiresAt | Portal eventId; email eventId+EMAIL |
| reservation.expired.v1 | Expiry worker/transaction | reservationId,editionId | Reallocate; không gửi READY cũ |
| loan.item.returned.v1 | Return | loanItemId,copyId,editionId,condition | Allocate hold; dedupe loanItemId+return |
| charge.assessment.decided.v1 | Finance | assessmentId,readerId,status,chargeId nullable | Projection/audit; không tự email ngoài phạm vi |
| reader.overdue.daily.v1 | Scheduler08:00 | readerId,localDate,asOf | Một portal/email summary readerId+localDate+channel |
| report.requested.v1 | Reporting | reportJobId,requestedBy,filterSnapshot,asOf | Export jobId; auth recheck download |
| account.reader.provision.requested.v1 | Identity | readerId,jobId,requesterAccountId (server) | Provider provision: readerId+operation |
| backup.requested.v1 / restore.requested.v1 | Operations | jobId,manifestId nullable,targetAlias | allowlist target; retry không ghi đè target đang dùng |

Không ghi recipient email/secret/rawCSV vào event logs; worker lấy dữ liệu nhận tối thiểu khi gửi. Phiên bản payload và tên event được xác định trong eventType/payload, không thêm cột source tùy ý.

## Lease, retry và xử lý trùng

Worker SELECT FOR UPDATE SKIP LOCKED lấy job đủ hạn, ghi lease_owner/lease_until rồi commit nhanh; không giữ DB transaction khi gọi provider. Mặc định đề xuất lease60s, heartbeat20s cho job dài; attempts5, exponential1/2/4/8s + jitter, giới hạn 60s; FAILED terminal có audit và replay có quyền. Export/restore chạy riêng allowlist, không dùng timeout/retry SMTP như chính sách chung cho mọi loại job. Config phải được chốt theo workload khi triển khai.

processed_at nghĩa là đã dispatch vào Job, không phải email delivered. Đánh dấu event processed cùng transaction tạo Job UQ dedupe_key. Consumer có thể chạy lặp sau crash; thay đổi DB có UQ và idempotency; provider email timeout có thể đã gửi, dùng provider idempotency nếu có, không hứa exactly-once.

## READY và consent

Trước email READY kiểm tra reservation còn READY và chưa expiry; event cũ thành SKIPPED, không gia hạn readyExpiresAt. Portal vẫn cho thấy trạng thái thật. Email nhắc08:00 tổng hợp mục OPEN quá hạn từ dueAt; đề xuất schedule là cấu hình, một độc giả/ngày dù restart. email_consent=false là mặc định; thay consent không xóa audit lịch sử. Job terminal không auto replay khi thiếu consent.

## Nghiệm thu

Crash trước/sau provider call; lease expired; hai workers; payload v1/v2; timeout; stale READY; mất consent; job replay cùng dedupe; deadline pickup không phụ thuộc cron. Không giữ transaction dài cho external call.

## Ownership khi đọc trạng thái job

Report/export truy vấn ownership từ `ReportJob.requested_by` qua `job_id`; không đọc cột requester không tồn tại trên Job. Cấp tài khoản dùng schema JSON nội bộ `ProvisionJobPayload` trong [OpenAPI](openapi.json): `schemaVersion=1`, `readerId`, `requesterAccountId`. Producer lấy requesterAccountId từ Account đã xác thực, ghi cùng transaction tạo job/outbox; envelope event provision gồm jobId và requesterAccountId để truy vết. Worker không ghi đè requester khi retry/replay. Schema này là bổ sung cho payload, chưa là cột mới hay triển khai runtime.

Đọc job own cần permission hiện tại tương ứng (report.read/export.create/account.provision_reader), loại job allowlist và ownership đúng. Metadata thiếu hoặc không hợp lệ thì từ chối nhánh own; job.read vận hành kiểm allowlist riêng. Không dùng Job.payload client gửi hoặc readerId/email để cấp quyền. JobView không trả payload nội bộ.

## Điều kiện duyệt restore trước lease

Restore request tạo Job(status=QUEUED), `RestoreJobPayload.approvalStatus=PENDING` và approvedBy/approvedAt/approvalReason NULL; chưa cho chạy restore. Dispatcher/worker loại restore PENDING trước claim/lease; QUEUED riêng không chứng minh đã được duyệt. Payload/schema/metadata sai bị từ chối. Transaction approval khóa Job, kiểm restore.approve và lý do rồi ghi APPROVED và dữ liệu người duyệt từ server; chỉ sau đó mới dispatch. JobId và projection approval_status cho biết tiến độ.

Worker kiểm lại approval, target allowlist, manifest và checksum trước pg_restore; replay không bỏ qua điều kiện duyệt. Loại job khác giữ điều kiện thực thi riêng. Không thêm enum WAITING_APPROVAL vào Job gốc hoặc cho client sửa payload approval. BE00/BE14 kiểm chứng không có lệnh restore bên ngoài khi PENDING.
