# INT01 — Luồng thư viện đầu tiên

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phụ thuộc:** BE01–BE07, FE01–FE05

## Mục tiêu

Nghiệm thu xuyên module dựa trên [quyết định](../decisions.md) và [truy vết](../traceability.md), không chỉ xác nhận từng phần chạy riêng.

## Task theo PR

| ID | Công việc |
| --- | --- |
| INT01.1 | Chuẩn bị seed catalog/reader/policy/account trong môi trường local |
| INT01.2 | Chạy đăng nhập→tìm sách→cấp thẻ→mượn→trả bằng UI/API/DB thật |
| INT01.3 | Kiểm tra hai quầy cạnh tranh, retry, nợ/thẻ hết hạn, pending phí và biên nhận |
| INT01.4 | Ghi kịch bản, fixture, kết quả và giới hạn xác minh; cập nhật mục lục |

## Nghiệm thu

- Một copy không có hai OPEN.
- rollback nguyên tử.
- trả vẫn thành công khi nợ.
- không mock nghiệp vụ ở nghiệm thu.

## Kiểm thử và bàn giao

- Playwright cho UI/API thật; pytest/PostgreSQL cho giao dịch; fault injection worker/provider và scope.
- Không dùng secret production hoặc restore vào DB đang dùng. Fixture phải có hướng dẫn reset an toàn.
- Task riêng không chạy test trong bước soạn kế hoạch; kiểm thử được thực hiện khi triển khai tương ứng.
