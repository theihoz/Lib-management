# Hoàn thiện lõi thư viện 10 tuần — đặc tả triển khai

**Ngày:** 03/11/2026 · **Trạng thái:** Draft, chờ duyệt thiết kế · **Mốc gốc:** `main@84441fb`

## Yêu cầu và căn cứ

Người dùng yêu cầu giám sát thread `01a1a043-34b0-7a33-abbe-b028a8dc251d`, viết spec cho khoảng thiếu và triển khai **toàn bộ lõi 10 tuần**, gồm gia hạn, phí, báo cáo và CSV. Thread đã kết thúc với kết luận: backend M0 có 9 bảng identity/platform; web mới FE00.1; 74/77 operation trong OpenAPI còn planned (bao gồm phase 2); chưa nghiệm thu luồng UI → API → PostgreSQL.

Nguồn chuẩn: [quyết định](../../plan/decisions.md), [data dictionary](../../design/data-dictionary.md), [OpenAPI](../../design/openapi.json), [quyền](../../design/permission-matrix.md), [C01–C09](../../plan/decisions.md#c01c09), [spec frontend M0](../../specs/M0-frontend-foundation.md), [thiết kế phí](../../design/charge-assessment.md). Spec này bổ sung chi tiết thực thi; không dùng số operations làm tỷ lệ hoàn thành.

## Phạm vi và lựa chọn thực hiện

Lõi gồm **F01–F09, F11–F14, F16, F18–F20**. F14 thuộc lõi vì catalog, cấp thẻ, mượn, gia hạn và phí cần PolicyVersion đã duyệt. Hoàn thành BE02 và FE09.3 trong lõi, không dùng seed/SQL thủ công làm giải pháp thay UI policy.

Phase 2 giữ nguyên F10, F15, F17, F21–F24. F09 được tách khỏi giữ chỗ F10; truy vấn khoản mượn cho nhân viên thuộc F09, không kéo portal history F17 vào lõi. Adapter artifact private cho F20 thuộc lõi dù upload bìa F15 hoãn. Release lõi không phụ thuộc nghiệm thu phase 2 trong INT02.

Cách thực hiện được đề xuất: giữ modular monolith FastAPI/PostgreSQL và React/Vite hiện có; chia thành các lát cắt có UI/API/DB thật, hợp nhất khi mỗi lát đạt nghiệm thu. Một lần triển khai toàn bộ trước khi tích hợp tạo rủi ro quá lớn; thay stack hoặc viết hệ thống song song không phù hợp các quyết định hiện hành. Người thực hiện chọn thứ tự dưới đây; đây không phải xác nhận đã hoàn thành module.

## 1. Nền tảng và hợp đồng xuyên hệ thống

- Sửa DB unavailable thành HTTP 503 `SERVICE_UNAVAILABLE`; không lộ SQL, tham số, thông tin kết nối trong response. Lỗi lập trình/constraint không tự chuyển thành 503.
- Worker tự heartbeat ngoài transaction handler mỗi `min(20, lease_seconds / 3)` giây. Heartbeat và finish chỉ hợp lệ khi owner, attempt và lease còn hiệu lực; mất lease không được ghi kết quả của lượt cũ. Handler ngoại vi vẫn phải idempotent và kiểm quyền trước tác động không đảo được.
- Hoàn tất frontend M0 PR2–5 theo spec có sẵn: generated TypeScript + openapi-fetch, TanStack Query, auth Keycloak PKCE, phiên trong bộ nhớ, route/menu theo permission, shell/tokens/component, focus/reduced motion, test browser. Không yêu cầu người dùng dán JWT vào giao diện.
- Request command camelCase, entity response snake_case; tiền VND là chuỗi nguyên không làm tròn qua JavaScript Number; thời gian response UTC, nghiệp vụ ngày theo Asia/Ho_Chi_Minh.
- Một UoW cho mọi command liên module; repository không commit. Actor/time lấy từ server. Permission kiểm ở request và command; UI chỉ hỗ trợ hiển thị.
- Command có Idempotency-Key như contract; lưu kết quả cùng transaction, replay giữ status/body/Location; cùng key khác payload 409. UI giữ key khi retry, đổi khi payload thay đổi.
- Thiết kế OpenAPI và runtime cập nhật cùng PR; generated client và manifest hash cập nhật sau khi contract đổi. Chỉ đánh `implemented` khi route thực sự chạy và đã kiểm chứng.

## 2. F14 — policy có phiên bản và lịch hiệu lực

### Dữ liệu và lịch

Dùng đúng 10 cột `PolicyVersion` trong data dictionary. Không thêm cột `version`; `expectedVersion` đối chiếu `version_no`. UUID do server tạo; `version_no` cấp tăng bằng sequence PostgreSQL, UQ và >0. `rules_schema_version=1` có schema typed, extra fields bị từ chối.

- DRAFT: chưa approved_by/approved_at; cho phép các bản nháp trùng lịch vì chưa áp dụng.
- Approval: khóa advisory toàn lịch policy, khóa draft; kiểm expectedVersion và trạng thái DRAFT. Lấy approved_by/approved_at từ principal/server; không duyệt hồi tố.
- Khoảng hiệu lực dùng `[effective_from, effective_to)`; NULL effective_to là vô hạn. Một constraint exclusion trên `tstzrange` cho policy đã duyệt chặn chồng hiệu lực cả khi cạnh tranh. Migration chỉ dùng GiST trên range, không cần extension `btree_gist`.
- Khi duyệt phiên bản mới bắt đầu T, chỉ được kết thúc phiên bản đã duyệt liền trước tại T nếu phiên bản trước đang có hiệu lực và chưa có kế tiếp. T phải lớn hơn thời điểm hiện tại và thời điểm bắt đầu của bản trước; bản đầu tiên cũng phải có effectiveFrom ở tương lai khi duyệt. Giữ nguyên effectiveFrom đã gửi, không âm thầm đổi thành thời điểm server; bản chưa đến hiệu lực được UI ghi rõ. Draft đã lỡ thời điểm phải được tạo lại với lịch mới. Không cắt lùi lịch sử, không chèn giữa các khoảng đã lên lịch; yêu cầu đó trả 409.
- Policy đã duyệt không sửa `rules`, version_no, approved_by/at, effective_from. Đóng effective_to tại thời điểm thay thế là chuyển lịch có kiểm soát trong cùng transaction, có audit; không phải chỉnh sửa tự do ACTIVE.
- Trạng thái SUPERSEDED phản ánh policy hết hiệu lực; việc chọn policy không dựa riêng vào status. Query chọn bản đã duyệt chứa thời điểm giao dịch; các khoảng lịch cũ vẫn được giữ để truy vết.
- Không có policy hiệu lực: command phụ thuộc policy trả 422 `POLICY_NOT_EFFECTIVE` trước mọi ghi nghiệp vụ. Read-only catalog vẫn trả dữ liệu.

### Rules v1

Các giá trị bootstrap lấy từ tài liệu, không coi chúng là số mới do người thực hiện tự đặt:

| Trường JSON rules | Giá trị ban đầu | Nguồn / ý nghĩa |
| --- | --- | --- |
| minReaderAge / maxReaderAge | 12 / 55 | BE04; tính tuổi theo ngày cấp thẻ |
| cardValidityMonths | 6 | Tháng lịch, clamp ngày cuối tháng |
| maxBooksPerLoan | 4 | C02; không có activeLoanLimit/activeHoldLimit |
| initialLoanDays | 4 | C04 |
| maxRenewals / renewalDays | 1 / 4 | C04; cộng từ hạn cũ |
| overdueFinePerDay | "1000" | C08; VND nguyên |
| allowedOutstandingBalance | "0" | C01 |
| publicationYearWindow | 8 | C09, gồm hai biên |
| readyHoldDays | 3 | C07; giữ để snapshot tương thích phase 2 |
| damageLostAssessment | "MANUAL_APPROVAL" | C03; không có bảng giá tự động |

Trong lõi, rules v1 cố định các quyết định C01–C09; UI cho xem diff, clone draft và lên lịch nhưng không âm thầm cho thay quy tắc đã chốt. Mở cấu hình giá trị khác là thay đổi quyết định nghiệp vụ, cần spec/approval riêng. Không cho người dùng gửi tùy ý JSON vào DB.

### API và UI

Triển khai các operation đã có: `GET/POST /api/v1/policy-versions`, `POST /api/v1/policy-versions/{id}/approval`. Bổ sung `GET /policy-versions/{id}` (đích Location) trong contract, không thêm PATCH/DELETE cho policy ACTIVE. List dùng cursor ổn định theo version_no, limit mặc định20/max100; quyền đọc `policy.write` như contract hiện tại, tạo `policy.write`, duyệt `policy.approve`.

UI `/manager/policies`: danh sách trạng thái, quy tắc đã duyệt, timezone lịch hiệu lực, tạo draft từ bootstrap/bản đã duyệt, diff, xác nhận duyệt, xử lý 409 không mất dữ liệu nhập, lỗi 401/403/422/503 theo client chung. Không hiện nút sửa/xóa ACTIVE. Bootstrap chạy qua cùng service/rules/audit, CLI không bypass validation; ứng dụng không tự seed hoặc approve khi khởi động.

Snapshot là DTO immutable gồm policy_version_id, rules_schema_version, rules và giá trị quyết định tại thời điểm giao dịch. Mỗi thẻ, LoanItem, RenewalItem/FineCharge tham chiếu/snapshot đúng các trường nguồn. Chính sách mới không thay due_at, phí hoặc thẻ lịch sử. BE03/04/05/06/08 gọi service policy dùng chung Session, không HTTP nội bộ.

## 3. Danh mục, độc giả và thẻ

- BE03/FE02: Publisher, Author, Category, BookEdition, BookAuthor, BookCategory, Location, BookCopy theo từ điển; CRUD đúng contract, tìm kiếm công khai projection an toàn. Bổ sung `GET/POST /api/v1/locations` (catalog.read/catalog.write), DTO Location theo từ điển và create DTO chỉ code/name hợp lệ (code1–32, name1–120, trim và không rỗng; status ACTIVE do server đặt), có Idempotency-Key/Location khi tạo; UI chọn hoặc tạo vị trí, không bắt nhập UUID. Bổ sung các GET list reference data còn thiếu trong cùng contract trước khi làm form. Năm xuất bản theo C09/policy hiệu lực. Barcode UQ; F02 lõi có tạo lô/list bản sao theo contract. Không thêm sửa barcode/location tùy ý hoặc thanh lý copy; chuyển trạng thái chỉ qua nghiệp vụ mượn/trả, thanh lý F22 tiếp tục hoãn. Bìa hiển thị placeholder; không triển khai upload F15.
- BE04/FE03: Reader, ReaderCard; hồ sơ, cấp thẻ tuổi 12–55, hạn 6 tháng lịch, chống trùng card number; linked Account.reader_id theo F16 qua CLI vận hành, không triển khai API quản trị F21. `/accounts/reader-provisioning` hiện gắn cả F16/F21 trong contract: trong lõi tiếp tục hoãn API này cùng F21. Bổ sung CLI `link-reader-account --issuer --subject --reader-id --actor-id` dùng service chung: actor có account.provision_reader, Reader tồn tại/ACTIVE, Account ACTIVE có đúng role READER, không staff/admin, uniqueness một Account/Reader; audit cùng transaction. Tạo user tại Keycloak bằng công cụ vận hành riêng, không password grant public hoặc self-registration. CLI hiện tại chưa có reader linking: đây là phần phải triển khai, không phải năng lực đã có.
- Eligibility do server tổng hợp trạng thái Reader/thẻ, nợ, OPEN quá hạn, ChargeAssessment PENDING và policy. Kết quả preview không thay kiểm tra dưới khóa của checkout/renew. Không lưu debt/overdue/count làm nguồn chân lý.
- UI có tìm sách, chi tiết/bản sao, tìm/tạo độc giả, cấp thẻ, lý do đủ/không đủ điều kiện. Permission/PII theo ma trận hiện hành.

## 4. Phí, checkout, trả và gia hạn

### D01 cần duyệt cùng spec này

Đề xuất cụ thể để đóng D01 trước migration: `ChargeAssessment.kind varchar(16)` CHECK DAMAGE/LOST; `status varchar(24)` CHECK PENDING/ASSESSED/CLOSED_NO_CHARGE; `version integer NOT NULL DEFAULT 1` CHECK >0; `created_at timestamptz NOT NULL DEFAULT now()`. Giữ đủ 15 cột nguồn, nullable của trường quyết định theo trạng thái; không thêm cột nguồn giả. Chỉ ghi D01 đã đóng khi người dùng duyệt spec này.

### Tài chính F11 và nhận trả F08

FineCharge/Payment/PaymentAllocation/Waiver và các reversal đúng từ điển; numeric(14,0), ledger append-only. Tính dư từ charge trừ allocation/waiver còn hiệu lực; reversal là dòng mới có liên kết và lý do. Không xóa/UPDATE sửa lịch sử tài chính; thu/miễn không vượt dư; tổng đảo payment/allocation/waiver không vượt phần còn chưa đảo của chứng từ gốc, không bị giới hạn bằng dư nợ hiện tại. Đảo payment ghi AllocationReversal cần thiết cùng transaction để giữ net allocation <= net payment; cùng Reader ở mọi liên kết. Chống cạnh tranh bằng khóa Reader rồi ledger theo thứ tự ổn định.

GOOD đóng LoanItem, tạo ReturnEvent và chuyển copy AVAILABLE trong một transaction; DAMAGE→REPAIR, LOST→LOST và tạo assessment PENDING. Không tự tạo phí hỏng/mất. Manager quyết định ASSESSED hoặc CLOSED_NO_CHARGE, kiểm expectedVersion; duyệt đồng thời chỉ tạo tối đa một FineCharge. Return vẫn nhận khi có nợ/thẻ hết hạn/PENDING. Phí trễ lấy snapshot: `max(0, returnLocalDate - dueLocalDate) * 1000` mỗi cuốn. Trả và thanh toán là hai transaction độc lập.

### Checkout F07

Tối đa4 cuốn/phiếu; không trùng barcode trong payload. Khóa theo thứ tự BookEdition → Reader → BookCopy → Loan/LoanItem, ổn định theo id; kiểm eligibility và trạng thái copy lại dưới khóa. Một partial unique index bảo đảm mỗi copy tối đa một LoanItem OPEN. Lỗi một cuốn rollback toàn phiếu, idempotency/audit/outbox cùng commit. DueAt và snapshot lấy server/policy, không nhận hạn do frontend tính.

### Gia hạn F09 và tra cứu nhân viên

Tối đa1 lần, thêm4 ngày từ hạn cũ, thẻ còn hiệu lực và eligibility được kiểm lại. Lệnh gia hạn áp dụng toàn bộ mục OPEN của phiếu hoặc không mục nào; bỏ qua mục đã trả trong phiếu trả một phần, không từ chối cả phiếu chỉ vì có mục đã trả. Không còn mục OPEN, có mục OPEN quá hạn/không đủ điều kiện, hoặc vượt giới hạn thì từ chối nguyên tử; retry cùng key replay. Dữ liệu snapshot ban đầu không bị sửa. Dùng RenewalEvent/RenewalItem đúng nguồn.

Bổ sung read endpoint staff `GET /api/v1/loans` với query barcode/cardNumber/readerId và lọc OPEN, cursor/limit như chuẩn, permission `loan.renew` hoặc `return.create` theo authorization OR trong contract. Tra cứu scoped cho nhân viên phục vụ F08/F09; không mở portal history F17. Truy vấn trả đủ loan/item/version token để dùng command hiện có, không bắt nhân viên biết UUID.

UI FE04/05/06/07: quét/chọn copy, xác nhận checkout/return/renew, biên nhận từ server, lý do bị chặn, đề xuất/duyệt phí, thu từng phần/miễn/đảo theo permission. Retry giữ idempotency key. 409 giữ dữ liệu và refetch; không hiển thị thành công trước commit.

## 5. Quá hạn, báo cáo và CSV

- F19: truy vấn OPEN và due_at < now(), không có cron lưu cột overdue làm nguồn thật; UI bảng, filter và links tới tác vụ có quyền.
- F13: báo cáo lending/overdue theo hợp đồng, khoảng thời gian `[from,to)`, timezone thư viện và định nghĩa chỉ số trong response/document. Số lượt mượn đếm LoanItem phát sinh; trả đếm ReturnEvent với return_kind=RETURNED (không đếm khai báo LOST/VOIDED là sách nhận lại); độc giả duy nhất dùng distinct reader_id; quá hạn là OPEN tại thời điểm truy vấn. Không đưa holds/notifications phase 2 vào số liệu lõi.
- Bổ sung `GET /api/v1/report-jobs/{id}/result`, permission report.read và ownership như xem job. Trước thành công409, ngoài scope404, hết hạn410. DTO `ReportResult`: `report_id`, `report_type`, `as_of`, `period: {from,to,timezone}`, `metrics` (các khóa `loan_items_issued`, `returns_received`, `distinct_borrowers`, `open_overdue_items`, số nguyên >=0), `rows` phân trang cursor20/max100. Lending rows: edition_id/title/issued_count/returned_count; overdue rows: loan_item_id/loan_no/reader_code/full_name/barcode/due_at/late_days. Không trả object key hoặc PII ngoài quyền nhân viên. Kết quả rỗng trả metrics0 và rows[]. Result JSON private được ghi cùng checksum/artifact metadata; pagination trên kết quả đã vật hóa, không chạy lại query live khi lật trang.
- `reportType` lõi chỉ `LENDING_SUMMARY` và `OVERDUE`; filters typed `{from,to}` timezone-aware, from<to, không nhận SQL/field/order tùy ý. Snapshot dữ liệu tại lúc worker bắt đầu trong transaction REPEATABLE READ; server ghi ReportJob.as_of từ thời điểm snapshot đó, UI phân biệt thời điểm yêu cầu và thời điểm dữ liệu. Client `asOf` không được hỗ trợ trong lõi và trả422 nếu gửi, không âm thầm bỏ qua. Filter kỳ quá khứ vẫn hoạt động trên sự kiện append-only. ReportJob.as_of trước khi chạy là mốc yêu cầu tạm, response có job status để phân biệt; chỉ SUCCEEDED là kết quả cuối. CSV dùng cùng truy vấn/định nghĩa và snapshot transaction của chính export job; hai job khác nhau không được hứa cùng snapshot.
- F20: ReportJob tham chiếu Job, requested_by từ principal. Export chạy worker, snapshot tham số, CSV UTF-8, quote đúng CSV và chống formula injection cho text bắt đầu `= + - @` hoặc control trước các ký tự đó. Không cast số tiền lớn qua float.
- Artifact private qua port storage chung; adapter filesystem cho local/test với root cấu hình và UUID/object key server sinh; adapter object storage tương ứng môi trường triển khai, không tự chọn hosting production. Không public folder, không nhận path/URL từ payload.
- Download kiểm lại permission `export.download` và ownership trước trạng thái/expiry: ngoài scope404, chưa xong409, hết hạn410. Giữ response JSON `DownloadLink` đã có của `/export-jobs/{id}/download`; adapter local trả URL cùng origin tới endpoint mới `GET /api/v1/export-jobs/{id}/content`, kiểm lại Bearer/quyền/ownership/expiry rồi stream text/csv, Content-Disposition attachment, Cache-Control no-store. Client tải content bằng apiClient có Bearer rồi tạo ObjectURL tạm, revoke sau tải; không gắn token query. Nếu dùng signedURL thì TTL không vượt artifact expiry, kiểm quyền lại ngay trước phát URL.
- Dùng retention cấu hình có mô tả, không biến mục tiêu đề xuất 24h thành quyết định production. ReportJob/Job không lộ object key, SQL, credentials.
- FE09 phần report/CSV có loading/empty/error, polling đúng job status, tải sau SUCCEEDED, thông báo revoked/expired. Chart nếu có luôn có bảng tương đương.

## 6. Phân kỳ triển khai và nghiệm thu

| Mốc | Đầu ra chạy thật | Cổng hoàn thành |
| --- | --- | --- |
| C0 | Hai lỗi M0; auth/client/router/shell frontend; contract/client drift | Unit/integration, browser login và lỗi phiên |
| C1 | F14 policy API/schema/UI; scope và D01 được đồng bộ sau duyệt | PG concurrency, idempotency, lịch `[from,to)`, browser tạo→duyệt |
| C2 | Catalog + độc giả/thẻ + eligibility + nền tài chính | UI tạo/tìm, validation biên tuổi/năm/tháng; permission |
| C3 | Checkout → return GOOD/DAMAGE/LOST, assessment/ledger | INT01 UI/API/DB thật; hai quầy/retry/rollback/phí |
| C4 | Renew, overdue và luồng phí đầy đủ | Test lặp, stale/version, nợ/PENDING/thẻ hết hạn |
| C5 | Reports/CSV/private storage/worker và frontend | Browser job→download; scope/expiry/csv injection |
| C6 | Release lõi, docs/onboarding/manifest, container web/reverse proxy | CI toàn bộ và smoke hệ thống thật; không phụ thuộc phase2 |

Mỗi mốc có schema/contract/implementation/test riêng, không đánh cả lõi Done khi chỉ một mốc đạt. Trạng thái spec/acceptance phân biệt code có trong branch, đã merge và đã nghiệm thu. Dùng feature branch, giữ thay đổi cá nhân, không force push.

## 7. Kiểm thử bắt buộc

1. Unit và integration PostgreSQL disposable, migration empty→head→base→head, alembic check; không truncate DB dev đang dùng.
2. Policy: timezone-aware; thời điểm biên; no policy; draft sai schema; 401/403; stale approval; cạnh tranh lịch; không hồi tố; snapshot không đổi sau policy mới.
3. Circulation/finance: hai quầy cùng copy, atomic rollback, duplicate retry, 5 cuốn, thẻ hết hạn, nợ/PENDING chặn mượn/gia hạn nhưng nhận trả; nửa đêm địa phương; cuối tháng; payment/waiver/reversal cạnh tranh.
4. Worker: job dài hơn lease, heartbeat tự chạy, mất lease/attempt cũ không ghi đè, retry/dead, không để thread sau handler kết thúc.
5. Frontend: Vitest/Testing Library; generated-client drift; 401 refresh tối đa1; 403 không thành công giả; không lưu token/PII vào storage; focus/keyboard/reduced-motion/390px; production không chứa mock.
6. Playwright dùng Keycloak + API + PostgreSQL thật cho login → policy → catalog → reader/card → checkout → return → assessment/payment → renew/overdue → report/CSV. Test mock chỉ bổ sung, không thay bằng chứng này.
7. Lint, format, mypy, TypeScript, wheel/web/container build; CI job `ci-result` kiểm toàn bộ cần thiết. Ghi rõ giới hạn nếu môi trường không chạy được dịch vụ ngoài.

## 8. Điều kiện mở còn lại

- Spec này đề xuất đưa F14 đầy đủ vào lõi và đóng D01 bằng kiểu cụ thể ở mục4; cần duyệt trước migration nghiệp vụ.
- Hosting, retention/ngân sách production, tài khoản SMTP/R2 và extension N03–N07 thuộc phase2/vận hành; không tự mua hay cấu hình bên ngoài.
- Mã hiện tại đã có một số test M0 nhưng không phải bằng chứng hoàn thành luồng nghiệp vụ. Báo cáo nghiệm thu sẽ cập nhật từng mốc với lệnh, commit và kết quả thật.
