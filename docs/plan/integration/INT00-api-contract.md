# INT00 — Hợp đồng API

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phụ thuộc:** BE00; FE00 dùng contract để phát triển mock

## Mục tiêu

Nghiệm thu xuyên module dựa trên [quyết định](../decisions.md) và [truy vết](../traceability.md), không chỉ xác nhận từng phần chạy riêng.

## Task theo PR

| ID | Công việc |
| --- | --- |
| INT00.1 | Chốt /api/v1, schema/lỗi/quyền và ví dụ OpenAPI |
| INT00.2 | Sinh client TypeScript và mock từ schema; thêm kiểm tra drift trong CI |
| INT00.3 | Chốt pagination cursor20/max100, 202 job+Location, Idempotency-Key và mapping lỗi |
| INT00.4 | Ghi kịch bản, fixture, kết quả và giới hạn xác minh; cập nhật mục lục |

## Nghiệm thu

- OpenAPI/client cùng commit.
- response tiền chuỗi VND, thời gian UTC.
- 401/403/404/409/422 rõ.
- frontend không tự dựng eligibility.

## Kiểm thử và bàn giao

- Playwright cho UI/API thật; pytest/PostgreSQL cho giao dịch; fault injection worker/provider và scope.
- Không dùng secret production hoặc restore vào DB đang dùng. Fixture phải có hướng dẫn reset an toàn.
- Task riêng không chạy test trong bước soạn kế hoạch; kiểm thử được thực hiện khi triển khai tương ứng.
