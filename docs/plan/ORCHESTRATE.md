> Warning: could not detect ECC install; defaulting to legacy form. If you use the plugin install, edit the prefixes manually.

# Plan-Orchestrate Result

**Plan**: `docs/plan/PLAN.md`
**Lang**: `typescript` (given, theo stack đề xuất; chưa có app code)
**ECC mode**: legacy
**Steps**: 20
**Scope**: all

Các lệnh bên dưới được tạo để sử dụng khi triển khai; chưa chạy. Slash command cần môi trường ECC có orchestrate. Mỗi bước chỉ bắt đầu sau khi Acceptance của phụ thuộc đạt.

## Steps overview

| # | Title | Tags | Chain |
|---|---|---|---|
| 1 | Chốt yêu cầu và chính sách | design | `planner,architect` |
| 2 | Thiết kế UX theo vai trò | design | `planner,architect` |
| 3 | Đóng ADR và hợp đồng API | design | `planner,architect` |
| 4 | Tạo nền dự án và môi trường local | impl | `tdd-guide,typescript-reviewer` |
| 5 | Thiết lập CI và staging sớm | build | `build-error-resolver` |
| 6 | Tạo schema và migration nền | db | `database-reviewer,typescript-reviewer` |
| 7 | Triển khai đăng nhập và quyền | impl, security | `tdd-guide,typescript-reviewer,security-reviewer` |
| 8 | Triển khai danh mục và bản sao | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 9 | Triển khai độc giả và điều kiện | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 10 | Triển khai cho mượn chống tranh chấp | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 11 | Triển khai sổ phí và thu tiền | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 12 | Triển khai trả sách và ghi phí | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 13 | Triển khai gia hạn và FIFO giữ chỗ | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 14 | Triển khai worker và thông báo | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 15 | Triển khai báo cáo export và policy | impl, db | `tdd-guide,database-reviewer,typescript-reviewer` |
| 16 | Hoàn thiện cổng độc giả | impl, security | `tdd-guide,typescript-reviewer,security-reviewer` |
| 17 | Kiểm chứng nghiệp vụ hiệu năng và UX | test | `tdd-guide,e2e-runner` |
| 18 | Hoàn thiện phát hành và phục hồi | build | `build-error-resolver` |
| 19 | Bàn giao hướng dẫn và cập nhật UML | docs | `doc-updater` |
| 20 | Rà soát điều kiện đưa vào sử dụng | review | `typescript-reviewer,code-reviewer` |

---

## Step 1 — Chốt yêu cầu và chính sách

**Intent**: Lập decision log C01–C09 và baseline QĐ01–QĐ08 cùng chủ nghiệp vụ. Gắn mỗi quyết định vào UC, dữ liệu và ví dụ biên.
**Tags**: design
**Chain rationale**: planner làm rõ quyết định; architect kiểm tra kiến trúc và đóng chuỗi.

```bash
/orchestrate custom "planner,architect" "[Plan: docs/plan/PLAN.md#step-1] Chốt baseline quản lý thư viện QĐ01–QĐ08 và C01–C09; ghi người duyệt, ngày hiệu lực và ví dụ biên. Acceptance: đủ 9 mục quyết định; mỗi quy tắc được duyệt truy vết UC và dữ liệu. Không tự coi đề xuất là chính sách đã duyệt."
```

---

## Step 2 — Thiết kế UX theo vai trò

**Intent**: Dựng prototype quầy mượn, trả, thu phí, tra cứu và cổng độc giả. Kế thừa token hiện có và thiết kế đủ trạng thái lỗi.
**Tags**: design
**Chain rationale**: planner làm rõ quyết định; architect kiểm tra kiến trúc và đóng chuỗi.

```bash
/orchestrate custom "planner,architect" "[Plan: docs/plan/PLAN.md#step-2] Thiết kế prototype React cho thủ thư và độc giả: quét thẻ, mượn, trả, thu phí, tìm và đặt trước. Acceptance: đủ loading/empty/error/success; mô tả focus máy quét và màn hình 360/768/1280px; trả sách độc lập thu tiền."
```

---

## Step 3 — Đóng ADR và hợp đồng API

**Intent**: Đánh giá TypeScript, mô hình phiên, module và giao dịch; tạo OpenAPI, ma trận quyền và sơ đồ triển khai bổ sung nếu thay đổi.
**Tags**: design
**Chain rationale**: planner làm rõ quyết định; architect kiểm tra kiến trúc và đóng chuỗi.

```bash
/orchestrate custom "planner,architect" "[Plan: docs/plan/PLAN.md#step-3] Chốt ADR React Vite, NestJS TypeScript và PostgreSQL cho thư viện; định nghĩa module, OIDC, REST và thứ tự khóa. Acceptance: ADR nêu đổi từ đề xuất ASP.NET; OpenAPI có lỗi 403/409/422 và idempotency; sơ đồ triển khai khớp module."
```

---

## Step 4 — Tạo nền dự án và môi trường local

**Intent**: Tạo pnpm workspace, web/API/worker, Compose PostgreSQL, env mẫu và health check. Seed chỉ dùng dữ liệu giả.
**Tags**: impl
**Chain rationale**: tdd-guide tạo kiểm chứng trước triển khai; reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-4] Tạo workspace TypeScript strict gồm web React Vite, API NestJS và worker, Compose PostgreSQL và env mẫu không chứa secret. Acceptance: cài frozen lockfile thành công; health/readiness hoạt động; README hướng dẫn máy mới chạy được."
```

---

## Step 5 — Thiết lập CI và staging sớm

**Intent**: Đặt cổng PR và triển khai skeleton lên staging. Sau từng bước thêm test vào workflow tương ứng.
**Tags**: build
**Chain rationale**: build-error-resolver kiểm tra cấu hình build và CI; TypeScript không có build resolver riêng trong catalogue.

```bash
/orchestrate custom "build-error-resolver" "[Plan: docs/plan/PLAN.md#step-5] Thiết lập GitHub Actions cho lint, typecheck, tests và build web/API/worker; đẩy image GHCR và triển khai staging. Acceptance: PR lỗi bị chặn merge; actions pin full SHA; staging health trả đúng digest và không log deploy hook."
```

---

## Step 6 — Tạo schema và migration nền

**Intent**: Tạo các entity catalogue, thẻ, mượn, giữ chỗ, ledger, policy, audit và outbox. Migration SQL được review trước dùng.
**Tags**: db
**Chain rationale**: database-reviewer kiểm tra schema và migration; typescript-reviewer đóng chuỗi kiểm tra mã.

```bash
/orchestrate custom "database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-6] Tạo schema PostgreSQL cho catalogue, reader/card, loan/item, reservation, ledger, policy và outbox qua Drizzle. Acceptance: migration DB rỗng đạt; unique barcode và partial unique OPEN copy tồn tại; transaction repository dùng cùng connection."
```

---

## Step 7 — Triển khai đăng nhập và quyền

**Intent**: Tích hợp OIDC, ma trận quyền và phạm vi reader. Tạo tài khoản demo qua provider cho staging.
**Tags**: impl, security
**Chain rationale**: tdd-guide triển khai với kiểm chứng; typescript-reviewer kiểm tra mã; security-reviewer đóng chuỗi kiểm tra quyền và dữ liệu cá nhân.

```bash
/orchestrate custom "tdd-guide,typescript-reviewer,security-reviewer" "[Plan: docs/plan/PLAN.md#step-7] Triển khai OIDC theo ADR phiên và quyền thủ thư/quản lý/độc giả; mọi API kiểm tra phạm vi đối tượng. Acceptance: token sai issuer/audience bị từ chối; reader A không đọc B; audit không chứa token hoặc dữ liệu cá nhân thừa."
```

---

## Step 8 — Triển khai danh mục và bản sao

**Intent**: Xây đầu sách, tác giả, NXB, thể loại, bản sao, bìa và tra cứu. Ngừng dùng thay xóa dữ liệu có lịch sử.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-8] Triển khai đầu sách, bản sao mã vạch, tác giả, NXB, thể loại A/B/C, bìa R2 và tìm kiếm phân trang. Acceptance: chặn chu trình; mã vạch duy nhất và không sửa ON_LOAN bằng CRUD; version cũ trả 409. Giữ lịch sử khi ngừng khai thác."
```

---

## Step 9 — Triển khai độc giả và điều kiện

**Intent**: Cấp thẻ theo quy tắc đã duyệt; eligibility trả toàn bộ mã lý do theo thao tác. Phí tính từ ledger, quá hạn từ dueAt.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-9] Triển khai độc giả và thẻ với biên tuổi, hiệu lực 6 tháng lịch và eligibility theo quy tắc đã duyệt. Acceptance: test cuối tháng/biên tuổi đạt; lý do thẻ/nợ/quá hạn đầy đủ; nhận trả không bị chặn bởi eligibility."
```

---

## Step 10 — Triển khai cho mượn chống tranh chấp

**Intent**: Xây quầy mượn và transaction all or nothing, policy snapshot, khóa và idempotency. Thu tiền và giữ chỗ chưa hoàn thiện phải fail closed theo điều kiện hiện có.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-10] Triển khai quầy mượn quét thẻ và mã vạch; khóa edition/reader/copy theo ID, kiểm tra lại và lưu policy snapshot. Acceptance: hai quầy cùng copy chỉ một thành công; retry key không tạo phiếu mới; một mục lỗi rollback toàn phiếu."
```

---

## Step 11 — Triển khai sổ phí và thu tiền

**Intent**: Xây Charge, Payment, Allocation, Waiver, Reversal với số nguyên VND. Biểu phí là cấu hình đã duyệt trước khi tính mất/hỏng.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-11] Triển khai ledger VND gồm charge, payment, allocation, waiver và reversal; thu tiền độc lập trả sách. Acceptance: thu một phần rồi đảo giữ số dư đúng; retry không thu hai lần; miễn phí kiểm tra quyền và audit. Không xóa lịch sử tài chính."
```

---

## Step 12 — Triển khai trả sách và ghi phí

**Intent**: Đóng LoanItem, cập nhật copy và ghi phí trong cùng transaction. Đặt adapter phân bổ giữ chỗ để nối bước tiếp theo.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-12] Triển khai trả tốt/hỏng/mất theo chính sách duyệt; đóng LoanItem, đổi copy và ghi charge trong một transaction. Acceptance: retry chỉ một ReturnEvent; thẻ hết hạn hoặc nợ vẫn trả được; phí dùng dueAt hiện tại và policy snapshot."
```

---

## Step 13 — Triển khai gia hạn và FIFO giữ chỗ

**Intent**: Nối return và mọi đường copy trở lại khả dụng với allocator; renew toàn bộ mục OPEN hoặc không mục nào. Expiry worker sử dụng cùng service.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-13] Triển khai renew all or nothing và hold FIFO createdAt+id theo edition; nối mọi đường copy khả dụng vào allocator. Acceptance: renew đồng thời không vượt giới hạn; READY không gán đôi copy; expiry/return cạnh tranh vẫn đúng FIFO và readyAt."
```

---

## Step 14 — Triển khai worker và thông báo

**Intent**: Xử lý lease outbox, nhắc hạn, expiry và retry hữu hạn. Ghi metric, attempt và dead-letter để thao tác xử lý lại có audit.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-14] Triển khai worker outbox với lease, dedupe, backoff và số lần thử tối đa; nhắc quá hạn và xử lý giữ chỗ hết hạn. Acceptance: không gửi trước commit; crash không mất job; hết lượt retry có cảnh báo và xử lý lại có audit."
```

---

## Step 15 — Triển khai báo cáo export và policy

**Intent**: Tạo report job snapshot, CSV theo quyền, cấu hình PolicyVersion bất biến; acquisition/retire F22 chỉ theo phạm vi mở rộng duyệt.
**Tags**: impl, db
**Chain rationale**: tdd-guide triển khai với kiểm chứng; database-reviewer kiểm tra giao dịch và invariant; typescript-reviewer đóng chuỗi.

```bash
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-15] Triển khai report job, CSV và PolicyVersion; acquisition/retire theo phạm vi được duyệt. Acceptance: tổng phí/thu khớp ledger cùng snapshot; export riêng tư kiểm tra quyền; policy mới không sửa khoản cũ. Chặn công thức CSV."
```

---

## Step 16 — Hoàn thiện cổng độc giả

**Intent**: Nối tìm sách, lịch sử, sách đang mượn, đặt/hủy và gia hạn theo quyền đã duyệt. Responsive và trạng thái offline đúng giới hạn.
**Tags**: impl, security
**Chain rationale**: tdd-guide triển khai với kiểm chứng; typescript-reviewer kiểm tra mã; security-reviewer đóng chuỗi kiểm tra quyền và dữ liệu cá nhân.

```bash
/orchestrate custom "tdd-guide,typescript-reviewer,security-reviewer" "[Plan: docs/plan/PLAN.md#step-16] Hoàn thiện cổng độc giả responsive gồm tìm sách, lịch sử, sách đang mượn và đặt/hủy theo C06 duyệt. Acceptance: chỉ dữ liệu reader hiện tại; luồng chính dùng được 360px và bàn phím; offline không ghi mượn/trả/tiền và logout xóa cache riêng."
```

---

## Step 17 — Kiểm chứng nghiệp vụ hiệu năng và UX

**Intent**: Chạy test cạnh tranh, E2E, accessibility và buổi sử dụng thử; đo NFR trên dữ liệu mô phỏng có quy mô công bố.
**Tags**: test
**Chain rationale**: tdd-guide tổ chức bằng chứng kiểm thử; e2e-runner đóng chuỗi kiểm chứng luồng.

```bash
/orchestrate custom "tdd-guide,e2e-runner" "[Plan: docs/plan/PLAN.md#step-17] Kiểm chứng hệ thống thư viện bằng PostgreSQL thật, E2E và thử UX với 5 người; đo p95 trên dataset công bố. Acceptance: invariant cạnh tranh và retry đạt; báo cáo tải có số mẫu/cấu hình; ít nhất 4/5 người hoàn thành mượn/trả sau hướng dẫn."
```

---

## Step 18 — Hoàn thiện phát hành và phục hồi

**Intent**: Đưa cùng digest từ staging sang production sau signoff. Diễn tập migration, rollback và restore sang DB mới.
**Tags**: build
**Chain rationale**: build-error-resolver kiểm tra cấu hình build và CI; TypeScript không có build resolver riêng trong catalogue.

```bash
/orchestrate custom "build-error-resolver" "[Plan: docs/plan/PLAN.md#step-18] Hoàn thiện release production theo digest đã qua staging, migration một chủ sở hữu và backup/rollback. Acceptance: release có signoff và digest khớp; diễn tập restore DB mới đo RPO/RTO; migration lỗi chặn deploy API và worker."
```

---

## Step 19 — Bàn giao hướng dẫn và cập nhật UML

**Intent**: Viết README, runbook quầy, xử lý lỗi, job thất bại và release; cập nhật mọi sơ đồ thay đổi theo phần mềm.
**Tags**: docs
**Chain rationale**: doc-updater đối chiếu tài liệu và cập nhật truy vết.

```bash
/orchestrate custom "doc-updater" "[Plan: docs/plan/PLAN.md#step-19] Bàn giao README local, hướng dẫn thủ thư, runbook deploy/rollback/restore và cập nhật UML khớp phần mềm. Acceptance: mỗi F ánh xạ UC/API/màn hình/test; đủ hướng dẫn máy mới; các mở rộng và chính sách chưa duyệt ghi trạng thái riêng."
```

---

## Step 20 — Rà soát điều kiện đưa vào sử dụng

**Intent**: Đối chiếu toàn bộ yêu cầu, quyền và release evidence. Chỉ mở sử dụng thật sau nghiệm thu của người phụ trách.
**Tags**: review
**Chain rationale**: typescript-reviewer rà soát mã; code-reviewer đối chiếu điều kiện phát hành.

```bash
/orchestrate custom "typescript-reviewer,code-reviewer" "[Plan: docs/plan/PLAN.md#step-20] Rà soát release thư viện từ yêu cầu đến code, quyền, test và vận hành; tổng hợp bằng chứng trước sử dụng thật. Acceptance: không còn lỗi nghiêm trọng chưa xử lý; mọi yêu cầu có trạng thái; có biên bản go/no-go với người chịu trách nhiệm và tồn đọng."
```

## Batch execution

Thực hiện theo thứ tự và giữ các cổng nghiệm thu đã nêu trong kế hoạch.

```bash
/orchestrate custom "planner,architect" "[Plan: docs/plan/PLAN.md#step-1] Chốt baseline quản lý thư viện QĐ01–QĐ08 và C01–C09; ghi người duyệt, ngày hiệu lực và ví dụ biên. Acceptance: đủ 9 mục quyết định; mỗi quy tắc được duyệt truy vết UC và dữ liệu. Không tự coi đề xuất là chính sách đã duyệt."
/orchestrate custom "planner,architect" "[Plan: docs/plan/PLAN.md#step-2] Thiết kế prototype React cho thủ thư và độc giả: quét thẻ, mượn, trả, thu phí, tìm và đặt trước. Acceptance: đủ loading/empty/error/success; mô tả focus máy quét và màn hình 360/768/1280px; trả sách độc lập thu tiền."
/orchestrate custom "planner,architect" "[Plan: docs/plan/PLAN.md#step-3] Chốt ADR React Vite, NestJS TypeScript và PostgreSQL cho thư viện; định nghĩa module, OIDC, REST và thứ tự khóa. Acceptance: ADR nêu đổi từ đề xuất ASP.NET; OpenAPI có lỗi 403/409/422 và idempotency; sơ đồ triển khai khớp module."
/orchestrate custom "tdd-guide,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-4] Tạo workspace TypeScript strict gồm web React Vite, API NestJS và worker, Compose PostgreSQL và env mẫu không chứa secret. Acceptance: cài frozen lockfile thành công; health/readiness hoạt động; README hướng dẫn máy mới chạy được."
/orchestrate custom "build-error-resolver" "[Plan: docs/plan/PLAN.md#step-5] Thiết lập GitHub Actions cho lint, typecheck, tests và build web/API/worker; đẩy image GHCR và triển khai staging. Acceptance: PR lỗi bị chặn merge; actions pin full SHA; staging health trả đúng digest và không log deploy hook."
/orchestrate custom "database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-6] Tạo schema PostgreSQL cho catalogue, reader/card, loan/item, reservation, ledger, policy và outbox qua Drizzle. Acceptance: migration DB rỗng đạt; unique barcode và partial unique OPEN copy tồn tại; transaction repository dùng cùng connection."
/orchestrate custom "tdd-guide,typescript-reviewer,security-reviewer" "[Plan: docs/plan/PLAN.md#step-7] Triển khai OIDC theo ADR phiên và quyền thủ thư/quản lý/độc giả; mọi API kiểm tra phạm vi đối tượng. Acceptance: token sai issuer/audience bị từ chối; reader A không đọc B; audit không chứa token hoặc dữ liệu cá nhân thừa."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-8] Triển khai đầu sách, bản sao mã vạch, tác giả, NXB, thể loại A/B/C, bìa R2 và tìm kiếm phân trang. Acceptance: chặn chu trình; mã vạch duy nhất và không sửa ON_LOAN bằng CRUD; version cũ trả 409. Giữ lịch sử khi ngừng khai thác."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-9] Triển khai độc giả và thẻ với biên tuổi, hiệu lực 6 tháng lịch và eligibility theo quy tắc đã duyệt. Acceptance: test cuối tháng/biên tuổi đạt; lý do thẻ/nợ/quá hạn đầy đủ; nhận trả không bị chặn bởi eligibility."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-10] Triển khai quầy mượn quét thẻ và mã vạch; khóa edition/reader/copy theo ID, kiểm tra lại và lưu policy snapshot. Acceptance: hai quầy cùng copy chỉ một thành công; retry key không tạo phiếu mới; một mục lỗi rollback toàn phiếu."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-11] Triển khai ledger VND gồm charge, payment, allocation, waiver và reversal; thu tiền độc lập trả sách. Acceptance: thu một phần rồi đảo giữ số dư đúng; retry không thu hai lần; miễn phí kiểm tra quyền và audit. Không xóa lịch sử tài chính."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-12] Triển khai trả tốt/hỏng/mất theo chính sách duyệt; đóng LoanItem, đổi copy và ghi charge trong một transaction. Acceptance: retry chỉ một ReturnEvent; thẻ hết hạn hoặc nợ vẫn trả được; phí dùng dueAt hiện tại và policy snapshot."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-13] Triển khai renew all or nothing và hold FIFO createdAt+id theo edition; nối mọi đường copy khả dụng vào allocator. Acceptance: renew đồng thời không vượt giới hạn; READY không gán đôi copy; expiry/return cạnh tranh vẫn đúng FIFO và readyAt."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-14] Triển khai worker outbox với lease, dedupe, backoff và số lần thử tối đa; nhắc quá hạn và xử lý giữ chỗ hết hạn. Acceptance: không gửi trước commit; crash không mất job; hết lượt retry có cảnh báo và xử lý lại có audit."
/orchestrate custom "tdd-guide,database-reviewer,typescript-reviewer" "[Plan: docs/plan/PLAN.md#step-15] Triển khai report job, CSV và PolicyVersion; acquisition/retire theo phạm vi được duyệt. Acceptance: tổng phí/thu khớp ledger cùng snapshot; export riêng tư kiểm tra quyền; policy mới không sửa khoản cũ. Chặn công thức CSV."
/orchestrate custom "tdd-guide,typescript-reviewer,security-reviewer" "[Plan: docs/plan/PLAN.md#step-16] Hoàn thiện cổng độc giả responsive gồm tìm sách, lịch sử, sách đang mượn và đặt/hủy theo C06 duyệt. Acceptance: chỉ dữ liệu reader hiện tại; luồng chính dùng được 360px và bàn phím; offline không ghi mượn/trả/tiền và logout xóa cache riêng."
/orchestrate custom "tdd-guide,e2e-runner" "[Plan: docs/plan/PLAN.md#step-17] Kiểm chứng hệ thống thư viện bằng PostgreSQL thật, E2E và thử UX với 5 người; đo p95 trên dataset công bố. Acceptance: invariant cạnh tranh và retry đạt; báo cáo tải có số mẫu/cấu hình; ít nhất 4/5 người hoàn thành mượn/trả sau hướng dẫn."
/orchestrate custom "build-error-resolver" "[Plan: docs/plan/PLAN.md#step-18] Hoàn thiện release production theo digest đã qua staging, migration một chủ sở hữu và backup/rollback. Acceptance: release có signoff và digest khớp; diễn tập restore DB mới đo RPO/RTO; migration lỗi chặn deploy API và worker."
/orchestrate custom "doc-updater" "[Plan: docs/plan/PLAN.md#step-19] Bàn giao README local, hướng dẫn thủ thư, runbook deploy/rollback/restore và cập nhật UML khớp phần mềm. Acceptance: mỗi F ánh xạ UC/API/màn hình/test; đủ hướng dẫn máy mới; các mở rộng và chính sách chưa duyệt ghi trạng thái riêng."
/orchestrate custom "typescript-reviewer,code-reviewer" "[Plan: docs/plan/PLAN.md#step-20] Rà soát release thư viện từ yêu cầu đến code, quyền, test và vận hành; tổng hợp bằng chứng trước sử dụng thật. Acceptance: không còn lỗi nghiêm trọng chưa xử lý; mọi yêu cầu có trạng thái; có biên bản go/no-go với người chịu trách nhiệm và tồn đọng."
```
