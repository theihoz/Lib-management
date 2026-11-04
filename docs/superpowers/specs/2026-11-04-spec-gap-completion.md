# Hoàn thiện phần còn thiếu so với spec nhóm — đặc tả triển khai

**Ngày:** 04/11/2026 · **Trạng thái:** Approved — chủ dự án duyệt D1–D4 theo đề xuất ngày 04/11/2026; D5–D6 dùng đề xuất mặc định đến khi có quyết định khác · **Mốc gốc:** `main@395952d` (PR #50)

## Yêu cầu và căn cứ

Chủ dự án yêu cầu lập spec và kế hoạch cho **mọi phần còn thiếu** sau khi đối chiếu code với spec nhóm. Nguồn: [bảng yêu cầu](https://docs.google.com/document/d/1UZsEh4NGKM_OBGHocXhkOOpvqz3SDKbG/edit) (20 yêu cầu), [Lab 2 DFD v2](https://docs.google.com/document/d/1QBCDsxck3rTL1FHh9mfNos_Nd772UhyOAC4oJuFt4FE/edit) (BM01–BM15, QĐ01–QĐ26), [Lab 3 UML](https://docs.google.com/document/d/11tcWnRM4Wdc23r0-Fq5F7didcXUskmpM8DDybzkzFy4/edit), [Lab 4 Giao diện](https://docs.google.com/document/d/17i5MAqcagM54Xi6sl8rNXyBShp1pic6Tb23eCWRZ19w/edit), [thiết kế phần mềm](https://docs.google.com/document/d/1aM0zXfRCbXduHbcH1MjuiCiB1BGI-0IPUnFsNsiWcc0/edit). Bảng QĐ ↔ code hiện hành: [source-rules](../../specs/source-rules.md).

Spec này thay các phần đã cũ của [spec lõi 03/11](2026-11-03-core-library-design.md): rules v1 cố định và "C01–C09 giữ nguyên" đã được thay bởi [quyết định 04/11](../../plan/decisions.md#quyết-định-04112026--đối-chiếu-lại-spec-nhóm-lab-2-v2-lab-3-lab-4) (rules v2 cấu hình được, ngưỡng nợ 50.000). Phần còn lại của spec 03/11 vẫn áp dụng.

## Hiện trạng đã kiểm chứng (04/11/2026)

- API phục vụ **63/85** operation trong [OpenAPI](../../design/openapi.json); 22 còn thiếu đều thuộc F15, F16, F21, F22 (phiếu nhập), F23, F24. README đang ghi 66/85 (sai).
- 82/85 operation trong OpenAPI vẫn ghi `x-status: planned` dù 60 trong số đó đã chạy, nên `test_openapi_drift` chỉ kiểm 3 operation.
- Bảng phase 2 đã có schema (migration 0006): `acquisition_receipt*`, `backup_manifest`, `notification*`. `book_edition` chưa có liên kết ảnh bìa.
- Chưa có Playwright E2E trong repo/CI; kiểm thử trình duyệt mới chạy thủ công trong Dev Container.

## Danh sách việc

Ký hiệu: **G** = khoảng thiếu thuộc lõi 10 tuần (làm trước), **P** = phase 2 theo [quyết định 03/11](../../plan/decisions.md#quyết-định-03112026--phạm-vi-lõi-10-tuần), **Q** = chất lượng/hợp đồng.

| Mã | Spec | Việc | Ưu tiên |
| --- | --- | --- | --- |
| G1 | YC#2, Lab 2 YC2, Lab 3 BookCopy | Đổi trạng thái bản sao Sẵn sàng/Hỏng/Bảo trì/Mất | 1 |
| G2 | YC#6, BM02, Lab 3 ReaderCard | Khóa/mở khóa thẻ; hiển thị Hết hạn | 1 |
| G3 | YC#11, QĐ07, QĐ11 | Tạo phạt thủ công | 1 |
| G4 | YC#17, BM12, QĐ22 | Hồ sơ độc giả: đang mượn, phạt chưa thu, đặt trước, lịch sử | 1 |
| G5 | YC#1, BM13, QĐ23 | Tìm sách theo tác giả và thể loại; ngừng dùng ấn bản | 2 |
| G6 | YC#9 (Ai: Độc giả) | Độc giả tự gia hạn trên portal | 2 |
| G7 | YC#19, BM14 | Bảng điều khiển: quá hạn + sách mượn nhiều | 3 |
| G8 | YC#18 | Tìm kiếm toàn hệ thống Ctrl+K | 3 |
| Q1 | Quy tắc bảo trì OpenAPI | `x-status` đúng thực tế; drift test hai chiều | 1 |
| Q2 | NFR, acceptance matrix | Playwright E2E trong repo và CI với Keycloak/API/PostgreSQL thật | 2 |
| P1 | YC#10, BM04, Lab 2 YC9 | F10 đặt trước đủ quy tắc + UI quầy/portal + job hết hạn | 4 |
| P2 | YC#15, BM10, QĐ18–QĐ19 | F15 ảnh bìa qua R2 | 5 |
| P3 | YC#17 (portal), QĐ22 | F17 lịch sử của tôi trên portal | 4 |
| P4 | YC#16, Lab 3 Account/Role | F16/F21 cấp tài khoản độc giả, quản trị tài khoản/vai trò | 5 |
| P5 | BM01, QĐ03 | F22 phiếu tiếp nhận sách mới và thanh lý | 5 |
| P6 | Lab 3 BackupManifest, Job BACKUP | F23 sao lưu/khôi phục | 6 |
| P7 | Lab 3 OutboxEvent (ReservationReady) | F24 thông báo portal + email | 6 |

## Quyết định (D1–D4 đã duyệt 04/11/2026)

| Mã | Câu hỏi | Đề xuất | Lý do |
| --- | --- | --- | --- |
| D1 | Trạng thái bản sao: Lab 3 dùng AVAILABLE/BORROWED/LOST/DAMAGED/MAINTENANCE; DB đang dùng AVAILABLE/ON_LOAN/HELD/REPAIR/LOST/RETIRED | Giữ tên DB, thêm `MAINTENANCE`; nhãn: REPAIR = "Hỏng", ON_LOAN = "Đã mượn" | Không đổi tên dữ liệu đã có lịch sử; vẫn đủ 4 lựa chọn của YC#2 |
| D2 | Phạt thủ công (YC#11, Ai: Thủ thư) có cần Quản lý duyệt? | Thủ thư đề xuất (`ChargeAssessment` kind `MANUAL`), Quản lý duyệt như C03 | Mọi khoản phí không tự tính đều qua Quản lý; tái dùng luồng duyệt có sẵn |
| D3 | Lab 2: "đang mượn + đang đặt ≤ 4" khi đặt trước | Thêm rule `maxActiveLoansAndHolds` = 4, chỉ áp dụng khi **tạo đặt trước**; mượn vẫn theo QĐ05 mỗi phiếu | Lab 2 chỉ đặt điều kiện này ở YC9; mở rộng sang mượn là đổi C02 |
| D4 | "Xóa sách" (YC#1, YC#3–5) | Ngừng dùng (`INACTIVE`) thay vì xóa cứng; chặn khi còn bản sao đang mượn/giữ | Lab 3: RESTRICT, không xóa lịch sử mượn trả |
| D5 | Dung lượng ảnh bìa tối đa (QĐ18 "do hệ thống quy định") | 2 MB, PNG/JPG/WebP, cấu hình được | Đủ cho ảnh bìa; R2 free tier |
| D6 | Thứ tự phase 2 | P1 + P3 → P2/P4/P5 → P6/P7 | P1/P3 hoàn tất YC#10/YC#17; P6/P7 phụ thuộc hạ tầng chưa chốt (SMTP, nơi lưu backup) |

## Tiến độ

| Mã | Trạng thái | Commit |
| --- | --- | --- |
| Q1 | Xong | `783cc54` |
| G1 | Xong (migration 0009) | `f69546b` |
| G2 | Xong | `0a07d0c` |
| G3 | Xong (migration 0010) | `801f8a8` |
| G4 | Xong | `3af0c7d` |
| G5 | Xong | `a30f53d` |
| G6 + P3 | Xong (portal `/me`: đang mượn, gia hạn, lịch sử, phạt) | `ce17a35` |
| G7 | Xong (`/staff/dashboard`, trang mặc định của nhân viên) | `ccacda3` |
| G8 | Xong (Ctrl+K / ⌘K) | `9447108` |
| Q2 | Xong (Playwright `apps/web/e2e`, job CI `e2e`) | `49ef0aa` |
| P1, P2, P4–P7 | Chưa làm | — |

## Quy ước chung

Giữ nguyên quy ước của spec lõi: một UoW mỗi command, `Idempotency-Key` cho mọi POST/PATCH ghi, `expectedVersion` cho sửa đối tượng có `version`, audit cùng transaction, permission kiểm ở server, tiền là chuỗi VND nguyên, ngày nghiệp vụ theo Asia/Ho_Chi_Minh. Mỗi việc cập nhật trong cùng PR: OpenAPI (đánh `implemented`), `npm run gen:api`, [source-rules](../../specs/source-rules.md), [acceptance matrix](../../quality/acceptance-matrix.md), mock demo nếu UI mới cần dữ liệu.

## G1 — Đổi trạng thái bản sao

- `PATCH /api/v1/copies/{id}` (mới), quyền `catalog.write`. Body `{expectedVersion, status, reason}`; `status ∈ AVAILABLE, REPAIR, MAINTENANCE, LOST`; `reason` bắt buộc khi khác AVAILABLE (≤ 500 ký tự).
- Chuyển trạng thái hợp lệ: AVAILABLE ↔ REPAIR ↔ MAINTENANCE, mọi trạng thái đó → LOST, LOST → AVAILABLE (tìm thấy). Không đổi bằng tay ON_LOAN/HELD (chỉ qua mượn/trả/giữ chỗ) hay RETIRED (chỉ qua thanh lý F22): 409 `COPY_STATUS_LOCKED`.
- Về AVAILABLE gọi `allocate()` cho đặt trước đang chờ của ấn bản, cùng thứ tự khóa BookEdition → BookCopy.
- Migration: CHECK `book_copy.status` thêm `MAINTENANCE` (D1). Audit `catalog.copy.status`.
- UI FE02.05: cột trạng thái tiếng Việt, nút "Đổi trạng thái" mở hộp thoại chọn trạng thái + lý do; ẩn với bản đang mượn/giữ.
- Test: mỗi chuyển hợp lệ/không hợp lệ, version cũ 409, replay idempotency, AVAILABLE kích hoạt READY.

## G2 — Khóa/mở khóa thẻ

- `PATCH /api/v1/reader-cards/{id}` (mới), quyền `card.issue`. Body `{expectedVersion, status: ACTIVE|BLOCKED, reason}`; lý do bắt buộc khi khóa. REVOKED không mở lại (409); thẻ hết hạn không mở khóa được.
- Trạng thái hiển thị (BM02, YC#6): `ACTIVE` và `expires_at > now` = "Hoạt động"; `BLOCKED` = "Tạm khóa"; `ACTIVE` và đã hết hạn = "Hết hạn" (suy ra, không lưu); `REVOKED` = "Đã thu hồi".
- Eligibility đã yêu cầu thẻ ACTIVE còn hạn; thêm lý do riêng `CARD_BLOCKED` để quầy hiển thị đúng.
- UI FE03.02: danh sách thẻ với nhãn trên, nút Khóa/Mở khóa + lý do.
- Test: khóa → checkout 422 `CARD_BLOCKED`; mở khóa → mượn được; REVOKED/hết hạn không mở.

## G3 — Phạt thủ công (theo D2)

- Migration: `charge_assessment.kind` thêm `MANUAL`; `return_event_id` cho phép NULL với CHECK `(kind = 'MANUAL') = (return_event_id IS NULL)`; thêm `loan_item_id` NULL tùy chọn (FK, phải thuộc độc giả).
- `POST /api/v1/charge-assessments` (mới), quyền `assessment.propose`: `{readerId, loanItemId?, proposedAmount, reason}`; số tiền > 0.
- Quyết định giữ nguyên `POST /charge-assessments/{id}/decisions`; khi duyệt tạo `FineCharge.reason = 'MANUAL'`, `manual_reason` = lý do. PENDING chặn mượn như các đề xuất khác.
- UI FE07: "Đề xuất phạt thủ công" trên hồ sơ tài chính độc giả; FE07 Quản lý duyệt như hiện có.
- Test: đề xuất → PENDING_ASSESSMENT; duyệt 0 = không thu; duyệt > 0 tạo khoản MANUAL; thiếu quyền 403.

## G4 — Hồ sơ độc giả đầy đủ

- API: `GET /loans` thêm `readerId` (staff `loan.checkout` hoặc `reader.read`); `FineCharge` view thêm `balance` (từ `charge_balance`, chuỗi VND); `GET /reservations` thêm `readerId` + `status`. Không đổi quyền hiện có.
- UI FE03.02 thêm bốn khối: Đang mượn (phiếu, sách, hạn trả, quá hạn bao nhiêu ngày), Phạt chưa thu (khoản, còn nợ, tổng), Đặt trước đang chờ, Lịch sử mượn trả (`/readers/{id}/history`, phân trang). BM12: hiển thị ngày mượn, hạn trả, ngày trả, tiền phạt.
- Test: API filter đúng độc giả; balance sau thu/miễn/đảo; UI Vitest cho trạng thái rỗng/lỗi.

## G5 — Tìm sách và ngừng dùng ấn bản

- `GET /book-editions?query=` khớp thêm tên tác giả (EXISTS book_author/author) ngoài tiêu đề/ISBN; thêm `categoryId` (gồm thể loại con, CTE đệ quy) và `status` (staff). Giữ tham số hóa và giới hạn độ dài (AT18).
- Ngừng dùng (D4): `PATCH /book-editions/{id}` với `status: INACTIVE` bị chặn 409 khi còn bản sao ON_LOAN/HELD; catalog công khai ẩn ấn bản INACTIVE. Tác giả/NXB đã có quy tắc tương tự; thể loại: không có API xóa (QĐ09).
- UI FE02.01/FE02.03: bộ lọc thể loại (cây A/B/C), từ khóa tìm cả tác giả; nút "Ngừng dùng ấn bản".

## G6 — Độc giả tự gia hạn

- Cấp `loan.renew` cho READER; route gia hạn trả 404 nếu `principal.account.reader_id` khác `loan.reader_id` (scope own, C06). Quy tắc C04/Lab 2 giữ nguyên: chưa quá hạn, không nợ vượt ngưỡng, chưa gia hạn, không có đặt trước của người khác.
- UI FE08: nút "Gia hạn" trên từng phiếu của tôi, hiện lý do từ chối.
- Cập nhật [ma trận quyền](../../design/permission-matrix.md) và `rbac_seed`; test scope chéo độc giả 404.

## G7 — Bảng điều khiển

- `GET /api/v1/dashboard` (mới), quyền `overdue.read`: `{overdueCount, overdueTop: [10 mục gần hạn nhất], topBooks30d: [5 ấn bản], loansToday, returnsToday, copiesInStock}`; truy vấn đồng bộ có giới hạn, dùng lại SQL của báo cáo.
- UI: trang `/staff` (mặc định sau đăng nhập của nhân viên) với Stats + hai bảng; liên kết sang FE09 quá hạn và báo cáo.

## G8 — Ctrl+K

- Component `CommandPalette` trong shell: mở bằng Ctrl+K / ⌘K hoặc nút trên thanh trên; `role="dialog"`, ô tìm `role="combobox"`, danh sách `role="listbox"`, phím ↑/↓/Enter/Esc.
- Ba nhóm kết quả: Điều hướng (màn hình người dùng có quyền, lọc tại client), Sách (`/book-editions?query`, 5 kết quả), Độc giả (`/readers/lookup`, chỉ khi có `reader.read`). Từ khóa trống không gọi API (QĐ23); debounce 250 ms; hiện "Không tìm thấy".
- Test Vitest: phím tắt, lọc theo quyền, không gọi API khi trống.

## Q1 — Hợp đồng đúng thực tế

- Script `scripts/openapi_status.py`: đánh `x-status: implemented` cho operation runtime phục vụ, `planned` cho phần còn lại.
- Drift test hai chiều: mọi operation runtime phải là `implemented` trong thiết kế, và ngược lại. README sửa số đếm theo kết quả.

## Q2 — E2E trong CI

- `apps/web/e2e/` với `@playwright/test` (devDependency khóa trong lockfile): đăng nhập 3 vai trò, mượn → trả, phạt → thu, tạo/duyệt policy, báo cáo BM08 + CSV, QĐ26, Ctrl+K, tự gia hạn.
- CI job `e2e` chạy `scripts/local.sh up` (Docker trên runner), `npx playwright install --with-deps chromium`, lưu trace/screenshot khi lỗi. Thêm vào `ci-result`.
- Dev Container: thêm thư viện hệ thống cho Chromium vào Dockerfile để chạy E2E tại chỗ (thay cách giải nén thủ công).

## P1 — F10 đặt trước

- Quy tắc Lab 2 YC9: chỉ đặt khi ấn bản **không có** bản AVAILABLE (409 `COPY_AVAILABLE`, "vui lòng mượn trực tiếp"); thẻ còn hạn, đủ điều kiện; `loans OPEN + reservations QUEUED/READY < maxActiveLoansAndHolds` (D3); không trùng đặt trước đang hoạt động.
- Hàng đợi FIFO theo `created_at, id`; khi bản sao về AVAILABLE thì giao READY với `ready_expires_at = ready_at + readyHoldDays` (C07). Job `RESERVATION_EXPIRY` trong worker: hết hạn → EXPIRED, phân bổ lượt kế tiếp cùng transaction.
- UI: FE06 quầy (danh sách giữ chỗ, giao sách, hủy), FE08 portal (đặt, hủy, xem vị trí hàng đợi). BM04 hiển thị mã phiếu, ngày đặt, trạng thái, hạn giữ chỗ.
- Test: có bản sẵn → 409; giới hạn 4; FIFO; hết hạn chuyển lượt; gia hạn bị chặn khi có người đặt.

## P2 — F15 ảnh bìa

- Migration: `book_edition.cover_asset_id` FK `media_asset` (PUBLIC). `POST /media-upload-intents` (quyền `media.write`) trả URL ký sẵn hạn ngắn; `POST /media-assets/{id}/finalization` kiểm MIME bằng magic bytes (PNG/JPG/WebP), kích thước ≤ D5, sha256, gắn vào ấn bản (QĐ18).
- Adapter `R2Storage` (S3 API) + `FileStorage` local; cấu hình qua biến môi trường, không commit khóa. URL công khai lưu để hiển thị (QĐ19).
- UI FE02.09: chọn file, xem trước, tiến độ, lỗi định dạng/dung lượng.

## P3 — F17 lịch sử của tôi

- `GET /me/loans` đã có; thêm `status=ALL` và phân trang lịch sử. UI FE08: tab Đang mượn / Lịch sử / Phạt của tôi (`/me/fine-charges`).

## P4 — F16/F21 tài khoản và vai trò

- `POST /accounts/reader-provisioning` (`account.provision_reader`): tạo user Keycloak qua Admin API (adapter, service account riêng), liên kết Account ↔ Reader, gửi email đặt mật khẩu của Keycloak; idempotent theo email.
- `GET/PATCH /accounts`, `PUT /accounts/{id}/roles`, `GET/POST /roles`, `PUT /roles/{id}/permissions`, `GET /permissions` (`account.manage`, `role.manage`). Không cho tự hạ quyền admin cuối cùng; khóa Account có hiệu lực ở request kế tiếp.
- UI FE10: danh sách tài khoản, khóa/mở, gán vai trò, ma trận vai trò–quyền.

## P5 — F22 tiếp nhận và thanh lý

- `POST /acquisition-receipts` (DRAFT, `acquisition.write`): BM01 gồm mã phiếu, ngày tiếp nhận, người giao, NXB/nhà cung cấp, dòng `{editionId, quantity, unitValue}`; tổng số lượng/trị giá do server tính. QĐ03 kiểm năm xuất bản của từng ấn bản.
- `POST /acquisition-receipts/{id}/approval` (`acquisition.approve`), `/posting` sinh bản sao với mã vạch theo số lượng (Lab 2 YC2) trong một transaction. Thanh lý `POST /copies/{id}/disposal` đã chạy; thêm UI.
- UI FE10: lập/duyệt/ghi sổ phiếu; in BM01.

## P6 — F23 sao lưu/khôi phục

- Job `BACKUP` (`backup.create`, và lịch hằng ngày): `pg_dump -Fc` vào storage private, `backup_manifest` với checksum/size/retention. Khôi phục chỉ vào DB đích trong allowlist, hai người (yêu cầu + duyệt), kiểm checksum trước; không thay DB đang phục vụ (quyết định 07/10).
- `POST /jobs/{id}/replay` (`job.replay`) cho job DEAD.
- Chặn bởi quyết định hạ tầng: nơi lưu backup production (D6).

## P7 — F24 thông báo

- Sự kiện outbox `ReservationReady`, `LoanOverdueDigest` (08:00, tối đa một email/độc giả/ngày, chỉ khi consent). Portal: `GET /me/notifications`, `POST /me/notifications/{id}/read`, `PUT /me/notification-preferences`.
- Adapter SMTP; local dùng Mailpit trong `compose.local.yaml`. Không gửi email khi chưa consent.
- Chặn bởi quyết định hạ tầng: nhà cung cấp SMTP production (D6).

## Nghiệm thu chung

- Mỗi việc: pytest nghiệp vụ trên PostgreSQL tạm (`RUN_BUSINESS_DB_TESTS=1`), Vitest cho UI có logic, cập nhật E2E Q2 khi có luồng mới; `ruff`, `mypy`, `npm run lint/typecheck/test/build` sạch; CI `ci-result` xanh.
- Cập nhật cùng PR: OpenAPI `x-status`, source-rules, acceptance matrix, README "Trạng thái hiện tại".
- Không đánh dấu hoàn thành khi chỉ có mock; demo GitHub Pages cập nhật mock sau khi API thật đã có.
