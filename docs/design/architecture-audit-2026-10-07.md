# Architecture audit — Lib-management

Ngày: 07/10/2026. Phạm vi: FastAPI/PostgreSQL hiện có; thiết kế phân quyền, API, worker, DB và UML hiện hành. Thực hiện trong Dev Container `/workspaces/lib-management`, nhánh `fix/architecture-audit`. Ba subagent phụ trách backend, contract/quyền và UML/DB; agent chính đối chiếu kết quả và sửa tài liệu kiến trúc/kế hoạch. Không áp dụng mô hình 12 lớp agent/LLM vì ứng dụng chưa có thành phần đó.

## Phát hiện theo mức độ

Các mức High dưới đây là rủi ro của thiết kế khi triển khai, không là lỗi khai thác đã xác nhận trong runtime scaffold.

| Mã | Mức | Bằng chứng và cơ chế | Sửa/đối chiếu |
| --- | --- | --- | --- |
| A01 | High | API `/returns` chưa chỉ rõ quyền đề xuất assessment khi DAMAGE/LOST, trái charge-assessment | Bổ sung quyền có điều kiện; kiểm trước mọi ghi; GOOD chỉ yêu cầu quyền trả |
| A02 | High | `/jobs/{id}` dùng biểu thức quyền văn bản; ownership từng nhánh chưa có nguồn dữ liệu chính xác | Quy tắc OR/AND có cấu trúc; report/export lấy ReportJob.requested_by, provision lấy requester server ghi trong payload; không dùng Job.requested_by không tồn tại |
| A03 | High | Restore mô tả chờ duyệt nhưng worker lấy QUEUED chưa có điều kiện loại PENDING | Payload duyệt có kiểu; lọc trước claim/lease, ghi duyệt trong transaction và kiểm lại trước restore; không đổi enum Job gốc |
| A04 | High | ERD tổng quát có thuộc tính không có trong DOCX: active_cover_id, oidc_sub, Job.kind; lớp Reader.name/Loan.createdBy lệch nguồn | Sửa cell tại chỗ về tên/thuộc tính chuẩn; không thêm cột nguồn vì tên trên sơ đồ cũ |
| A05 | Medium | ERD thể hiện N với ReturnEvent.loan_item_id, Reservation.fulfilled_loan_item_id, ReportJob.job_id dù có UQ | Chỉnh cardinality về tối đa một bản ghi liên quan; ghi guard tương ứng trong DB design |
| A06 | Medium | Thuyết minh F08/F11 còn phí trực tiếp, khác luồng PENDING đã duyệt | Sửa thuyết minh luồng trả/assessment, giữ receipt đóng và không chặn trả |
| A07 | Medium | Runtime health thiếu operation ID chuẩn/schema503; model chung ban đầu vẫn cho trạng thái không đúng HTTP response | Model riêng live/ready/unavailable có const, trường status bắt buộc và cấm trường dư; test đối chiếu contract |
| A08 | Medium | `/me/reservations` yêu cầu quyền tạo; `/auth/me` không đủ dữ liệu menu FE01 | Đọc dùng reservation.read; AuthContext là read projection account + permissions DB, không đổi Account |
| A09 | Medium | Contract export thiếu410 trong khi threat model yêu cầu xử lý artifact hết hạn | Bổ sung410 và kiểm scope trước trạng thái hết hạn |
| A10 | Low | DB_PORT cho phép0 hoặc lớn hơn65535 | Validation1–65535, fail khi đọc Settings |
| A11 | Low | Đặc tả hạ tầng còn nói frontend chưa chọn; chưa có tài liệu tập trung ranh giới module/transaction | Sửa trạng thái frontend; bổ sung system-architecture.md và liên kết chỉ mục |

## Chẩn đoán kiến trúc

Kiến trúc đã chọn là modular monolith, SQLAlchemy Session đồng bộ cho nghiệp vụ, API và worker riêng. Vấn đề chính là thiếu ánh xạ/guard giữa tài liệu: DTO chưa đủ cho frontend, mô tả quyền chưa chuyển thành điều kiện rõ ràng, sơ đồ tổng quát giữ tên lịch sử trong khi DB chi tiết dùng nguồn chuẩn. Đã bổ sung [kiến trúc hệ thống](system-architecture.md) để xác định module sở hữu dữ liệu và Unit of Work liên module; không dùng repository tự commit hoặc gọi provider trong transaction.

## Vòng audit thứ hai

Sau sửa ban đầu, rà soát lại độc lập các kết quả: phát hiện schema health còn rộng, nguồn ownership Job.requested_by không tồn tại, AuthContext thiếu permissions và restore thiếu guard duyệt. Những điểm này được sửa tiếp trong cùng đợt. Điều này không thay thế nghiệm thu các module chưa có code.

## Kế hoạch sửa theo thứ tự

1. Khóa hợp đồng quyền/ownership/duyệt restore trước BE01/BE14, có kiểm tra phủ định và cạnh tranh trong các PR triển khai.
2. Dùng tên/field DOCX và cardinality UQ hiện hành khi viết Alembic/model; N05 tiếp nhận phải được xác nhận trước migration.
3. Dùng contract health đã sửa ngay trong scaffold; triển khai router nghiệp vụ theo contract planned, không tự mở endpoint khi thiếu auth/transaction.
4. Cập nhật DB/API/UML/plan/acceptance trong cùng PR; chỉ chuyển planned sang implemented khi có bằng chứng runtime.

## Giới hạn

- UML đã cập nhật đúng file Drive và đọc lại bytes khớp SHA256 repo. Google Docs đã cập nhật và đọc lại nội dung/cấu trúc; bố cục PDF live chưa xác minh vì tải export HTTP403.
- DOCX nguồn đã sửa có kiểm soát và render 149 trang; snapshot Google Docs là text readback, không là native DOCX export.
- Chưa có migration/CRUD/Keycloak/frontend/worker nghiệp vụ để chứng minh phân quyền, giao dịch lưu thông, đồng thời ledger hoặc restore thực tế đã đạt.
- N03/N04/N05/N06/N07 vẫn mở theo [báo cáo đồng bộ](synchronization-report.md); không tự chọn chính sách retention, hosting, uniqueness hay APPROVED mới cho tiếp nhận.
- Chưa commit/push trong đợt audit này.

## Kiểm tra và chứng cứ

- `uv run --locked ruff check .`, `ruff format --check .`, `mypy src`: đạt trong apps/api.
- `uv run --locked pytest -q`: 17 passed, 5 integration skipped theo mặc định.
- `RUN_DB_INTEGRATION=1 uv run --locked pytest -q`: 22 passed, gồm PostgreSQL thực trong container; các ca timeout/blackhole/concurrency/pool exhaustion đạt.
- Runtime OpenAPI health đối chiếu operation ID, HTTP status, required status/const/additionalProperties với thiết kế: đạt.
- OpenAPI thiết kế: 77 operationId duy nhất, 75 planned + 2 health; local references giải được. Đây là kiểm tra cấu trúc/đối chiếu, chưa là validator OAS chuyên dụng hoặc nghiệm thu endpoint planned.
- UML: một canvas, 3.020 cell ID duy nhất, parent/source/target hợp lệ; đối chiếu 38 hộp ERD/288 trường và projection lớp. Chưa render toàn canvas.
- Manifest: hash toàn bộ file khớp; UML synced_verified, cloud hash cuối khớp repo; provenance lịch sử giữ riêng.

Bằng chứng: [backend](../../apps/api/src/lib_management/main.py), [cấu hình](../../apps/api/src/lib_management/config.py), [API](api-contract.md), [quyền](permission-matrix.md), [events/restore](event-job-contracts.md), [UML audit với cell IDs](../diagrams/architecture-audit-notes.md), [manifest](../source-manifest.json).

Vòng hai còn phát hiện state restore cũ có chuyển target/promote và metadata guard `/auth/me` trộn vào permission. Sửa restore chỉ ghi nhận target cô lập; tách guard Account ACTIVE khỏi mã permission. N05 vẫn cần chủ dự án xác nhận trước migration tiếp nhận.

## Đồng bộ cuối sau hai vòng architecture audit

- Drive: đúng file ID `1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn`; modifiedTime `2026-10-07T12:05:49.077Z`; 1.230.546 bytes; SHA256 `c4052199b78fafb106ce580f5bc8e6e7018b1558561cffc228e091dd27f3d068` khớp repo khi tải lại. Một canvas/3.020 cell/94 khung.
- Google Docs: đúng báo cáo `15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8`, tab t.0; đọc lại 82 inline images, 70 bảng, 24 mục chức năng và 82 số hình duy nhất. Thay 26 hình hiện có; thêm 8 hình state/activity F21–F24 đúng mục; sửa danh mục hình/mục lục thủ công và thêm 19.10. Revision cuối lưu trong manifest và snapshot.
- DOCX: 67 bảng/76 hình; thay 73 occurrence sơ đồ từ cell hiện hành, giữ ba hình assessment; nguồn 38 bảng/288 thuộc tính không đổi. Render 149 trang; xem contact sheets toàn tài liệu và chi tiết các trang thay đổi. Routing ảnh xuất ngoài Draw.io là xấp xỉ; chưa kiểm tra toàn canvas bằng GUI Draw.io.
- PDF Google Docs cuối xuất được (17.006.937 bytes), nhưng tải về HTTP403; chỉ xác nhận nội dung/cấu trúc connector, chưa xác nhận bố cục PDF live. DOCX repo là bản nguồn đã sửa, không là export báo cáo live.
- Runtime scaffold: Ruff/format/mypy đạt; mặc định 17 passed/5 skipped, PostgreSQL integration 22 passed. Contract tĩnh 77 operations/649 refs/95 schemas đạt; full OAS metaschema chưa chạy. F01–F24 nghiệp vụ, Keycloak, worker và frontend chưa được nghiệm thu runtime.
- N03–N07 còn mở; lời xác nhận chung không xác định lựa chọn chính sách. Thay đổi đang ở nhánh `fix/architecture-audit`, chưa commit/push.
