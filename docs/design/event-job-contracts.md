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
| account.reader.provision.requested.v1 | Identity | readerId,jobId | Provider provision: readerId+operation |
| backup.requested.v1 / restore.requested.v1 | Operations | jobId,manifestId nullable,targetAlias | allowlist target; retry không ghi đè target đang dùng |

Không ghi recipient email/secret/rawCSV vào event logs; worker lấy dữ liệu nhận tối thiểu khi gửi. Phiên bản payload và tên event được xác định trong eventType/payload, không thêm cột source tùy ý.

## Lease, retry và xử lý trùng

Worker SELECT FOR UPDATE SKIP LOCKED lấy job đủ hạn, ghi lease_owner/lease_until rồi commit nhanh; không giữ DB transaction khi gọi provider. Mặc định đề xuất lease60s, heartbeat20s cho job dài; attempts5, exponential1/2/4/8s + jitter, giới hạn 60s; FAILED terminal có audit và replay có quyền. Export/restore chạy riêng allowlist, không dùng timeout/retry SMTP như chính sách chung cho mọi loại job. Config phải được chốt theo workload khi triển khai.

processed_at nghĩa là đã dispatch vào Job, không phải email delivered. Đánh dấu event processed cùng transaction tạo Job UQ dedupe_key. Consumer có thể chạy lặp sau crash; thay đổi DB có UQ và idempotency; provider email timeout có thể đã gửi, dùng provider idempotency nếu có, không hứa exactly-once.

## READY và consent

Trước email READY kiểm tra reservation còn READY và chưa expiry; event cũ thành SKIPPED, không gia hạn readyExpiresAt. Portal vẫn cho thấy trạng thái thật. Email nhắc08:00 tổng hợp mục OPEN quá hạn từ dueAt; đề xuất schedule là cấu hình, một độc giả/ngày dù restart. email_consent=false là mặc định; thay consent không xóa audit lịch sử. Job terminal không auto replay khi thiếu consent.

## Nghiệm thu

Crash trước/sau provider call; lease expired; hai workers; payload v1/v2; timeout; stale READY; mất consent; job replay cùng dedupe; deadline pickup không phụ thuộc cron. Không giữ transaction dài cho external call.

