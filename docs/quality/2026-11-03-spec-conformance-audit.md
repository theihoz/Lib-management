# Audit đối chiếu spec lõi 10 tuần (03/11/2026)

Nguồn: [spec lõi](../superpowers/specs/2026-11-03-core-library-design.md), [spec frontend M0](../specs/M0-frontend-foundation.md), [ma trận quyền](../design/permission-matrix.md). Phương pháp: đọc mã, chạy pytest (73 pass, 58 skip — các test cần PostgreSQL bị bỏ qua trong môi trường audit), không chạy được toolchain Node.

**Trạng thái = bằng chứng đã có, không phải tuyên bố hoàn thành.**

| Mục spec | Kết quả | Bằng chứng / hành động |
| --- | --- | --- |
| §1 DB unavailable → 503 `SERVICE_UNAVAILABLE` | Đạt (code + test đơn vị) | `core/errors.py`, `tests/test_database_errors.py` |
| §1 Worker heartbeat ngoài transaction | Đạt (code) | `worker/runner.py`; test cần PG |
| §1 Idempotency, UoW, snapshot policy | Có code; chưa chạy PG | `tests/integration` bị skip ở audit |
| §1 Contract và runtime cùng PR | **Lệch → đã sửa** | Thêm 10 operation vào `openapi.json` (locations, copies/lookup, readers/lookup, loans, report result, export content, policy get); mount router báo cáo vốn chưa được include |
| Backend khởi động được | **Lỗi → đã sửa** | 7 chỗ `, response_model=` lạc dòng gây SyntaxError |
| §2 Policy: GET theo id (Location target) | **Thiếu → đã thêm** | `GET /policy-versions/{id}` |
| §2 Policy: exclusion constraint, không hồi tố | Có (migration 0004, router approval) | cần PG để chứng minh cạnh tranh |
| §3 CLI `link-reader-account` | **Thiếu → đã thêm** | `identity/service.py::link_reader_account`, `cli.py`; kiểm quyền, Reader ACTIVE, đúng vai trò READER, một Reader/một Account, audit |
| §3 Tra cứu theo số thẻ/mã vạch, không UUID | **Lệch (UI) → đã sửa** | `Circulation.tsx`, `ReaderPicker.tsx` |
| §4 Checkout/return/renew UI | Viết lại | idempotency key giữ khi retry; 409 giữ dữ liệu |
| §4 Phí: thu, miễn, quyết định phí | Viết lại | `Finance.tsx` |
| §5 F19 quá hạn có độc giả/sách | **Thiếu → đã sửa** | `GET /overdue-items` trả `OverdueRow` (reader, title, lateDays theo Asia/Ho_Chi_Minh) + test PG |
| §5 Report/CSV: job → kết quả → tải | Viết lại | `Reports.tsx`; CSV tải qua client có Bearer + ObjectURL |
| §5 Chống formula injection CSV | Đạt (code) | `reporting/service.py` |
| Frontend: quyền theo ma trận | **Sai → đã sửa** | `reader.write`, `card.issue`, `payment.collect`, `assessment.decide`, `charge.waive`, `overdue.read`, `export.create`, `policy.write`; test `routes.test.ts` |
| Frontend: phạm vi lõi, bỏ phase 2 | **Lệch → đã sửa** | 71 → 36 màn; gỡ DesignBrowser/fixtures/discovery |
| Frontend: silent SSO | **Thiếu → đã thêm** | `check-sso`, `public/silent-check-sso.html` |
| Frontend: `/me` | Nâng cấp | `MePage.tsx` (tài khoản, lối tắt theo quyền, nhóm quyền) |
| Index DB | Đã rà bằng đọc mã, **chưa đo** | xem dưới |
| §7 Playwright E2E với Keycloak+API+PG thật | **Chưa có** | ngoài phạm vi phiên này |
| §7 Lighthouse | **Chưa chạy** | cần bản build production |
| CDN, load balancer | Chỉ cấu hình mẫu | `deploy/`; không triển khai cloud |

## Index (đọc mã, chưa `EXPLAIN`)

- Tra cứu chính đã có chỉ mục: `book_copy.barcode`, `reader_card.card_no`, `reader.reader_code` (UNIQUE), `loan_item.loan_id`, `fine_charge.reader_id`, `loan.reader_id`.
- `loan_item`: UNIQUE một phần `copy_id WHERE closed_at IS NULL` và `(due_at, id) WHERE closed_at IS NULL` phục vụ quá hạn.
- Chưa có chỉ mục cho `ILIKE '%…%'` trên tên độc giả và tiêu đề sách. Với quy mô thư viện là chấp nhận được; `pg_trgm` là extension nên cần quyết định riêng (spec ghi N03–N07 ngoài lõi).
- Việc cần làm khi có PG: `EXPLAIN (ANALYZE, BUFFERS)` cho `GET /overdue-items`, `GET /loans`, tìm sách.

## Chưa xác minh (cần môi trường có Node/PG/Keycloak)

`npm run gen:api`, lint, prettier, typecheck, Vitest, build; `RUN_BUSINESS_DB_TESTS=1 pytest tests/business`; luồng đăng nhập Keycloak thật; Lighthouse. `schema.d.ts` đang được sửa tay cho các operation mới và phải sinh lại.
