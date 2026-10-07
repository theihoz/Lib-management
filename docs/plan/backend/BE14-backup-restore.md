# BE14 — Sao lưu và phục hồi cô lập

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F23
**Phụ thuộc:** BE00, BE01; schema nghiệp vụ hoàn chỉnh

## Nguồn và ranh giới

DOCX thiết kế là chuẩn tên/thuộc tính; UML là chuẩn luồng. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

BackupManifest, Job; /backup-jobs, /restore-jobs.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| BE14.1 | Dựng backup bằng pg_dump, checksum và manifest lưu private | Model/migration hoặc nền màn hình cùng mô tả hợp đồng |
| BE14.2 | Tạo restore request tham chiếu backup và target cô lập được allowlist; phê duyệt theo quyền vận hành, trạng thái duyệt trong RestoreJobPayload server ghi; worker không nhận job PENDING | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE14.3 | Worker restore vào target mới, kiểm tra migrations/invariants và ghi kết quả diễn tập | Service/API hoặc màn hình tích hợp, ví dụ dữ liệu và xử lý lỗi |
| BE14.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Job QUEUED nhưng approvalStatus=PENDING không được lease/chạy; thiếu restore.approve không đổi trạng thái duyệt.
- Hai lần duyệt/replay không tạo restore song song; worker kiểm lại approval/target/checksum trước adapter.
- Checksum sai chặn restore.
- không nhận SQL/path tùy ý.
- thất bại không đổi DB đang dùng.
- không tự promote target vào production.

## Kiểm thử dự kiến

- Unit test service và guard; integration test trên PostgreSQL thật cho query/constraint/transaction.
- Kiểm thử quyền, input sai, not-found, retry và cạnh tranh với các lệnh ghi.
- Adapter ngoài được mock ở unit test, kiểm thử contract riêng ở integration.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.
