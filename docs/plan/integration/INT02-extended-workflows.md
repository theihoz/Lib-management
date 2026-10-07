# INT02 — Luồng mở rộng xuyên hệ thống

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phụ thuộc:** BE08–BE14 và FE06–FE11

## Mục tiêu

Nghiệm thu xuyên module dựa trên [quyết định](../decisions.md) và [truy vết](../traceability.md), không chỉ xác nhận từng phần chạy riêng.

## Task theo PR

| ID | Công việc |
| --- | --- |
| INT02.1 | Giữ chỗ FIFO→READY→email/portal→pickup/hết hạn, gia hạn và pending-fee approval |
| INT02.2 | Thu/phân bổ/miễn/đảo→history/report/CSV, đổi policy không đổi lịch sử |
| INT02.3 | Upload ảnh, receipt/post/disposal, worker retry/dead-letter và backup/restore cô lập |
| INT02.4 | Ghi kịch bản, fixture, kết quả và giới hạn xác minh; cập nhật mục lục |

## Nghiệm thu

- Không sai ledger/count do join.
- stale email không kéo dài READY.
- thu hồi quyền chặn download.
- restore fail giữ DB hiện tại.

## Kiểm thử và bàn giao

- Playwright cho UI/API thật; pytest/PostgreSQL cho giao dịch; fault injection worker/provider và scope.
- Không dùng secret production hoặc restore vào DB đang dùng. Fixture phải có hướng dẫn reset an toàn.
- Task riêng không chạy test trong bước soạn kế hoạch; kiểm thử được thực hiện khi triển khai tương ứng.
