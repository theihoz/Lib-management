# INT03 — Container, CI và bàn giao team

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phụ thuộc:** BE00, FE00; hoàn thiện sau INT01/INT02

## Mục tiêu

Nghiệm thu xuyên module dựa trên [quyết định](../decisions.md) và [truy vết](../traceability.md), không chỉ xác nhận từng phần chạy riêng.

## Task theo PR

| ID | Công việc |
| --- | --- |
| INT03.1 | Bổ sung Node/dev services vào Dev Container portable; Keycloak, SMTP local, API/worker và web profiles |
| INT03.2 | Build frontend static multi-stage, SPA fallback, runtime API config; cùng origin /api, không secret frontend |
| INT03.3 | Mở rộng CI lint/typecheck/unit/integration/e2e/build và publish image theo cùng SHA; viết onboarding Windows/macOS |
| INT03.4 | Ghi kịch bản, fixture, kết quả và giới hạn xác minh; cập nhật mục lục |

## Nghiệm thu

- npm ci và uv sync tái lập.
- lockfiles đầy đủ.
- API health hiện có không bị phá.
- release chỉ sau gates, không tự chọn đích production.

## Kiểm thử và bàn giao

- Playwright cho UI/API thật; pytest/PostgreSQL cho giao dịch; fault injection worker/provider và scope.
- Không dùng secret production hoặc restore vào DB đang dùng. Fixture phải có hướng dẫn reset an toàn.
- Task riêng không chạy test trong bước soạn kế hoạch; kiểm thử được thực hiện khi triển khai tương ứng.
