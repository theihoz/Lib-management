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

## Gate đồng bộ theo Docs mới

- INT00.S1: truy vết 39 bảng/303 trường từ data-dictionary.json; đối chiếu schema DB với DTO projection và command, không đòi DTO chứa toàn bộ cột.
- INT00.S2: ChargeAssessment.version required trong response là hợp đồng API hiện hành, không chứng minh DB NOT NULL đã chốt. D01 cần quyết định và backfill trước migration.
- INT00.S3: CI drift dự kiến kiểm tra tên/kiểu/NULL/FK/UQ và mã trạng thái; bộ tài liệu đã đối chiếu không thay thế contract tests/runtime.
- INT00.S4: notification extensions giữ scope F24; hoàn thiện đặc tả chi tiết ở BE13 trước migration, không thêm trường suy đoán vào nguồn 39/303.
