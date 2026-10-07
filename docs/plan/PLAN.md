> **Tài liệu lịch sử (06/10/2026).** Giữ để tham khảo phạm vi nghiệp vụ và 20 bước. Backend hiện đã chốt Python/FastAPI/PostgreSQL; đề xuất NestJS/Drizzle/TypeScript cho backend và trạng thái C01–C09 chưa duyệt trong bản này đã cũ. C01–C09 đã được người dùng đồng ý áp dụng. Dùng [hướng dẫn team](../operations/team-development.md), [đặc tả hiện hành](../operations/fastapi-infrastructure-spec.md) và [mục lục nguồn](../README.md) để triển khai. Frontend/auth/hosting vẫn chưa chốt.

# Kế hoạch triển khai phần mềm quản lý thư viện

Ngày 06/10/2026. Stack đề xuất TypeScript. Trạng thái đề xuất để triển khai.

## Mục tiêu và phạm vi

Đề xuất xây dựng ứng dụng web quản lý thư viện bằng TypeScript cho cả giao diện và API, PostgreSQL cho dữ liệu và GitHub Actions cho CI/CD. Quầy thủ thư ưu tiên thao tác bằng máy quét và bàn phím; cổng độc giả ưu tiên điện thoại. Kiến trúc gồm một API chia module và một worker dùng chung cơ sở dữ liệu.

Kế hoạch nối tài liệu thiết kế với công việc triển khai có đầu ra, phụ thuộc và tiêu chí nghiệm thu. Phạm vi chính bao gồm F01–F20. F21–F24 là các mở rộng được đánh dấu riêng; kiểm soát tài khoản và khả năng phục hồi tối thiểu vẫn là điều kiện vận hành an toàn.

Nguồn thiết kế là Google Docs Thiết kế phần mềm Quản lý thư viện UML và kiến trúc 2026 và bộ UML Quản lý thư viện 2026. Bộ sơ đồ có 74 trang, trong đó 24 sơ đồ trạng thái và 24 luồng hoạt động cho từng chức năng; một trang lưu bản gốc. Các định danh F và UC được giữ để truy vết.

Ngày lập kế hoạch 06/10/2026. Đây là đề xuất triển khai; các mục tiêu hiệu năng và thời gian bên dưới cần đo khi có ứng dụng. C01–C09 cần chủ nghiệp vụ hoặc giảng viên quyết định trước khi đóng băng quy tắc tương ứng.

Quyết định kiến trúc ADR01 đề xuất chuyển lựa chọn backend từ ASP.NET Core trong tài liệu trước sang NestJS TypeScript. Mục đích là dùng một ngôn ngữ xuyên suốt cho nhóm mới học. Nếu nhóm đã thành thạo C#, cần đánh giá lại ADR01 trước bước 4; mô hình nghiệp vụ và PostgreSQL vẫn áp dụng.

| Mốc | Đầu ra và điều kiện chuyển mốc |
|---|---|
| M0 | Bước 1–3: yêu cầu, UX và ADR được thống nhất |
| M1 | Bước 4–9: môi trường, CI, tài khoản, danh mục và thẻ chạy trên staging |
| M2 | Bước 10–13: mượn, sổ phí, trả, gia hạn và giữ chỗ nhất quán |
| M3 | Bước 14–17: job, báo cáo, cổng độc giả và kiểm chứng chất lượng |
| M4 | Bước 18–20: phát hành, hướng dẫn và đối chiếu thiết kế |

## Công nghệ và chính sách phiên bản

TypeScript là lựa chọn đề xuất để chia sẻ kỹ năng và kiểu dữ liệu giữa frontend và backend. Kiểu tĩnh không thay kiểm tra dữ liệu lúc chạy hoặc kiểm tra quyền trên máy chủ. SQL là kỹ năng bổ sung bắt buộc cho các giao dịch mượn và sổ phí.

Node.js 24 là nhánh LTS được chọn; trang chính thức ghi 24.21.0 là bản LTS tại thời điểm tra cứu [T1]. PostgreSQL 18 là nhánh được hỗ trợ đến 2030 [T5]. Chốt bản vá tương thích khi tạo dự án; ghi exact version vào manifest, lockfile, cấu hình runtime và Docker digest. Các thư viện frontend/backend chọn stable, kiểm tra peer dependencies cùng nhau; không sử dụng latest làm định danh triển khai.

React SPA phù hợp giao diện quầy và cổng độc giả không đặt trọng tâm SEO. Vite cung cấp công cụ dựng frontend [T2,T3]. NestJS chia controller, service và module, phù hợp ranh giới nghiệp vụ [T4]. Drizzle với node-postgres được đề xuất vì cho phép viết SQL rõ ràng và đặt tất cả thao tác trong cùng transaction [T6].

| Lớp | Lựa chọn đề xuất | Cách giữ dễ vận hành |
|---|---|---|
| Ngôn ngữ | TypeScript strict và SQL | Một bộ quy ước, kiểu API sinh từ OpenAPI |
| Giao diện | React, Vite, React Router | SPA responsive; route theo vai trò |
| Biểu mẫu và dữ liệu | React Hook Form, Zod, TanStack Query | Kiểm tra trường, cache có quy tắc, lỗi rõ ràng |
| Thành phần UI | Radix và component nội bộ | Dùng token sẵn có; kiểm tra keyboard [T7] |
| API và job | NestJS và worker TypeScript | Chung mã nghiệp vụ; entrypoint riêng |
| Dữ liệu | PostgreSQL 18, Drizzle, pg | Migration SQL có review; khóa và constraint |
| Lưu trữ | Cloudflare R2 | Bìa sách và tệp riêng tư tách bucket |
| Công cụ | pnpm workspace, Docker Compose | Một README khởi động; một lockfile |
| Kiểm chứng | Vitest, Supertest, Playwright | Unit, PostgreSQL thật, E2E trình duyệt |
| Triển khai | GitHub Actions, GHCR, Render | Image theo digest; DB managed cùng vùng |

## Kiến trúc ứng dụng và hợp đồng dữ liệu

Frontend gọi /api/v1 qua HTTPS. API gồm Identity, Catalog, Readers, Circulation, Reservations, Finance, Reporting và Policy. Worker thực hiện outbox, hết hạn giữ chỗ, nhắc hạn và xuất báo cáo. API và worker dùng chung domain service; worker không tự tạo bộ quy tắc khác.

Tổ chức dự án đề xuất apps/web, apps/api, apps/worker, packages/contracts, packages/ui và packages/config. OpenAPI sinh client và kiểu DTO. Domain và repository ở backend; frontend không được nhập entity DB hoặc bí mật máy chủ. Tài liệu, migration và workflow được quản lý phiên bản cùng mã nguồn.

Checkout, return, renew, thu tiền và cấp lượt READY là transaction PostgreSQL. Drizzle transaction phải giữ cùng connection; SQL FOR UPDATE và partial unique index dùng cho các invariant quan trọng [T6,T8,T9]. Các lớp repository phải nhận transaction context, không âm thầm truy vấn bằng connection ngoài transaction.

Thứ tự khóa toàn hệ thống: BookEdition theo ID, Reader theo ID, BookCopy theo ID, Loan và LoanItem, Reservation, rồi Charge và Payment. Job cũng tuân thủ. Truy vấn trạng thái phải kiểm tra lại sau khi khóa; đặt lock timeout và retry có giới hạn cho lỗi tạm, giữ cùng idempotency key.

Idempotency key gắn actor, operation và payload hash; lưu kết quả trong transaction nghiệp vụ. Cùng key và khác payload trả 409. Cùng payload trả kết quả trước đó. Outbox được ghi cùng commit; gửi email sau commit với lease, dedupe và số lần thử hữu hạn.

Các endpoint tham chiếu: POST /loans; POST /loans/{id}/returns; POST /loans/{id}/renewals; POST /reservations; POST /payments; POST /report-jobs. Lỗi có code, fieldErrors, reasons và correlationId. 403 cho thiếu quyền, 409 cho tranh chấp, 422 cho dữ liệu hoặc điều kiện không hợp lệ. Thao tác xem trước điều kiện không đặt chỗ.

Mở rộng schema theo expand, backfill, validate rồi contract qua các release riêng. Chỉ một job sở hữu migration bằng DB advisory lock. API và worker phiên bản cũ vẫn phải tương thích trong giai đoạn rolling deploy. Hoàn tác image không tự hoàn tác dữ liệu.

## Quy tắc phải chốt trước khi triển khai

Chủ nghiệp vụ là người quyết định chính sách. Nhóm kỹ thuật ghi phương án, người duyệt, ngày hiệu lực và ví dụ biên trong decision log. Có thể làm danh mục và hạ tầng trong khi chờ, nhưng không phát hành luồng phụ thuộc một quy tắc chưa duyệt.

PolicyVersion bất biến; LoanItem và FineCharge lưu phiên bản hoặc snapshot cần thiết. Tiền dùng số nguyên VND hoặc numeric(14,0), truyền qua API bằng chuỗi thập phân để tránh chuyển đổi sai. dueAt đã lưu là nguồn xác định quá hạn. Múi giờ nghiệp vụ là Asia/Ho_Chi_Minh.

| ID | Nội dung cần quyết định | Phương án dự thảo để đối chiếu |
|---|---|---|
| C01 | Không nợ hay nợ dưới 50.000 | Không nợ theo QĐ08 |
| C02 | Giới hạn một phiếu và tổng đang mượn | 4 cuốn một phiếu; tổng cần quyết định riêng |
| C03 | Biểu phí mất và hỏng | Cần bảng theo loại sách, lý do và thẩm quyền |
| C04 | Gia hạn và điều kiện thẻ | 4 ngày ban đầu; gia hạn 1 lần thêm 4 ngày từ hạn cũ |
| C05 | Định dạng và quyền xuất | Quản lý xuất CSV; Excel/PDF chờ duyệt |
| C06 | Cổng độc giả và tự tạo tài khoản | Độc giả xác thực xem dữ liệu của mình |
| C07 | Mốc tính 3 ngày giữ READY | Từ readyAt, độc lập lúc gửi thông báo |
| C08 | Cách làm tròn ngày phạt | Chênh lệch ngày địa phương; quá hạn cùng ngày có thể phí 0 |
| C09 | Biên năm xuất bản trong 8 năm | currentYear minus 8 đến currentYear, gồm hai biên |

## Giao diện và luồng thao tác

Thủ thư mở trực tiếp Quầy mượn trả; menu còn lại là Sách, Độc giả, Đặt trước và Phí. Quản lý có Báo cáo và Quy định theo quyền riêng. Độc giả thấy Tìm sách, Sách đang mượn, Đặt trước và Lịch sử. Không dùng một dashboard chứa tất cả chức năng làm màn hình bắt đầu.

Quầy mượn: quét thẻ, xem điều kiện, quét từng mã sách, kiểm tra danh sách và xác nhận. Focus trở về ô mã vạch sau mỗi lượt; Enter thêm sách, nút Xác nhận riêng để tránh máy quét vô tình gửi phiếu. Mã trùng trong danh sách hiện thông báo ngay. Hiển thị tên sách, bản sao, hạn dự kiến và lý do từ chối trước khi gửi.

Quầy trả: quét sách, hiện khoản đang mượn, chọn tốt hoặc ghi nhận hỏng/mất, xác nhận trả và in/xem biên nhận. Thẻ hết hạn hoặc nợ không chặn nhận trả. Nếu có phí, cung cấp nút sang màn hình Thu phí; trả sách và thu tiền có kết quả độc lập.

Cổng độc giả: ô tìm kiếm có bộ lọc tên, tác giả, thể loại và khả dụng; chi tiết sách hiển thị số bản khả dụng và hàng đợi. Đặt trước theo đầu sách, hiển thị vị trí hàng đợi và thời hạn READY. Gia hạn hiển thị tất cả lý do không đủ điều kiện; dữ liệu cá nhân chỉ thuộc người đăng nhập.

Sử dụng token giao diện hiện có: Arial hoặc system sans, nội dung 16px, bảng 14px, khoảng cách 4/8/12/16/24/32px. Nút chính xanh đậm; mọi trạng thái có chữ và biểu tượng. Vùng bấm mục tiêu 44px, focus rõ, form có label và lỗi cạnh trường. WCAG 2.2 AA là mục tiêu cần đánh giá, không phải chứng nhận đã đạt [T7,T10].

Mỗi màn hình có loading, empty, error, success và mất kết nối. Tìm kiếm debounce khoảng 300ms; phân trang máy chủ. Không cập nhật lạc quan giao dịch mượn, trả hoặc tiền. Gửi lại sau mất mạng dùng cùng key; chưa xác minh commit thì hiện Đang xác minh giao dịch và chặn tạo key mới.

Responsive mục tiêu 360px, 768px và 1280px: bảng quầy chuyển thẻ hoặc vùng cuộn có nhãn trên điện thoại; hành động chính luôn dễ thấy. PWA được xem xét ở giai đoạn cổng độc giả. Chỉ cache dữ liệu công khai để đọc; xóa cache riêng khi logout. Mượn, trả và thu tiền luôn cần kết nối máy chủ.

## CI CD từ ngày đầu

CI chạy khi mở PR: cài phụ thuộc với frozen lockfile, format, lint, typecheck, unit, integration trên PostgreSQL và migration DB rỗng, build frontend/API/worker. E2E luồng trọng yếu chạy trên môi trường dữ liệu giả cô lập. PR chỉ được merge khi các kiểm tra bắt buộc đạt và có review.

CD sau merge main: dựng image linux/amd64 cho API chứa bản build frontend và cho worker, gắn commit SHA, đẩy GHCR, lấy digest rồi triển khai staging. API phục vụ SPA giúp giảm dịch vụ phải quản lý. Smoke test xác minh digest đang chạy, schema version và luồng mượn trả mẫu trước khi đánh dấu staging thành công.

Release production chọn chính digest đã qua staging. Kiểm tra backup, quyền migration và tương thích API/worker; chạy migration một lần trước khi đổi phiên bản. Deploy API rồi worker, theo dõi health, lỗi và outbox. Render hỗ trợ image và deploy hook có imgURL theo tag hoặc digest [T11,T12]. HTTP 200 từ hook chỉ báo bắt đầu; workflow phải chờ trạng thái deploy và smoke test.

Secrets tách staging và production. Render deploy hook là bí mật, lưu vào Actions secrets và không ghi log. OIDC chỉ dùng với nhà cung cấp hỗ trợ, không mặc định Render nhận OIDC. Pin action bằng full commit SHA, quyền GITHUB_TOKEN tối thiểu, không cấp secret deploy cho PR từ fork [T12,T13,T14].

Cổng phê duyệt production phụ thuộc gói GitHub và loại repository. Required reviewers có giới hạn ở private repo [T15]. Nếu gói không hỗ trợ, người có quyền phát hành thực hiện deploy production sau signoff đã ghi nhận trên release; không coi workflow_dispatch tự nó là phê duyệt.

Rollback ứng dụng dùng digest trước còn lưu trong GHCR và schema tương thích. Worker cũ phải đọc được job đang tồn. Khi migration phá dữ liệu, dừng ghi, đánh giá forward fix hoặc phục hồi DB mới và đối chiếu giao dịch sau backup; không chạy downgrade phá dữ liệu tự động.

| Workflow đề xuất | Trigger | Điều kiện đạt |
|---|---|---|
| ci.yml | PR và main | Lint, typecheck, tests, build, migration đạt |
| staging.yml | main đã qua CI | Digest mới healthy; smoke test đạt |
| release.yml | Release đã được signoff | Backup, migration, API và worker đạt |
| dependency.yml | Hàng tuần | PR nâng phiên bản có CI; không tự merge major |

## Bảo mật chất lượng và nghiệm thu

OIDC Authorization Code với PKCE qua nhà cung cấp được duyệt; API kiểm tra issuer, audience, expiry, chữ ký và quyền phía máy chủ. Nếu dùng cookie phiên cần HttpOnly, Secure, SameSite và CSRF cho thao tác ghi. Nếu dùng bearer token, tránh lưu refresh token vào localStorage. Viết ADR cho mô hình phiên trước triển khai.

Độc giả chỉ đọc và sửa dữ liệu của mình; thủ thư, quản lý và quản trị có ma trận quyền riêng. Mọi truy vấn kiểm tra phạm vi đối tượng. Không nâng quyền theo claim chưa được xác minh; không giả định quản lý có mọi quyền thủ thư. Audit chỉ ghi mã, hành động và người thực hiện, hạn chế email, ngày sinh, token trong log.

Các kịch bản bắt buộc: hai quầy mượn cùng copy; trả gửi lại sau commit; gia hạn hai lần đồng thời; trả đúng lúc giữ chỗ hết hạn; thu một phần rồi đảo khoản; đổi policy nhưng khoản cũ giữ phép tính; vượt phạm vi reader; export sau bị thu hồi quyền. Integration cần PostgreSQL thật để kiểm chứng khóa và partial index.

Coverage mục tiêu 80% nhánh/statement cho domain trọng yếu, kèm toàn bộ invariant và đường lỗi có test; không dùng coverage tổng để thay bằng chứng nghiệp vụ. OWASP ASVS dùng làm checklist kiểm chứng đã chọn theo mô hình hệ thống [T16]. Playwright dùng E2E trình duyệt [T17].

| Chỉ tiêu đề xuất | Cách nghiệm thu |
|---|---|
| Đúng dữ liệu | Một LoanItem OPEN trên mỗi copy; ledger không âm; mọi invariant qua suite |
| Giao dịch | p95 mượn và trả ≤500ms ở tải 50 nhân viên đồng thời |
| Tìm kiếm | p95 ≤1 giây với 100.000 bản sao, 50.000 độc giả, 1 triệu mục lịch sử |
| Thông báo | 99% job gửi trong 2 phút khi provider khỏe; hết lượt có cảnh báo |
| Export | 100.000 dòng CSV trong 2 phút; tránh công thức CSV; tệp có phạm vi quyền |
| Khả dụng | Mục tiêu 99,5% một tháng; xác định lịch bảo trì và cách đo |
| Khôi phục | RPO ≤24 giờ và RTO ≤4 giờ qua diễn tập restore |
| Dễ thao tác | 5 người thử: ≥4 tự hoàn thành mượn/trả mẫu sau hướng dẫn 10 phút |

## Lộ trình triển khai

Mỗi bước có thể tạo một PR hoặc nhóm PR nhỏ. Chỉ chuyển bước khi phụ thuộc và Acceptance đã đạt. F21–F24 cần phạm vi mở rộng được duyệt; bước 7 và 18 vẫn có quyền và phục hồi nền tối thiểu.

<a id="step-1"></a>
## Step 1 Chốt yêu cầu và chính sách

Lập decision log C01–C09 và baseline QĐ01–QĐ08 cùng chủ nghiệp vụ. Gắn mỗi quyết định vào UC, dữ liệu và ví dụ biên.

- Tags: design
- Phụ thuộc: không
- Truy vết: F01–F20
- Acceptance: 9 xung đột có người quyết định và trạng thái
- Acceptance: Quy tắc được duyệt có ngày hiệu lực và ví dụ

<a id="step-2"></a>
## Step 2 Thiết kế UX theo vai trò

Dựng prototype quầy mượn, trả, thu phí, tra cứu và cổng độc giả. Kế thừa token hiện có và thiết kế đủ trạng thái lỗi.

- Tags: design
- Phụ thuộc: 1
- Truy vết: F07,F08,F10,F11,F18,F17
- Acceptance: Prototype có 5 luồng trọng yếu
- Acceptance: Thao tác bàn phím và 3 kích thước màn hình được mô tả

<a id="step-3"></a>
## Step 3 Đóng ADR và hợp đồng API

Đánh giá TypeScript, mô hình phiên, module và giao dịch; tạo OpenAPI, ma trận quyền và sơ đồ triển khai bổ sung nếu thay đổi.

- Tags: design
- Phụ thuộc: 1, 2
- Truy vết: Toàn hệ thống
- Acceptance: ADR01 có lý do đổi backend
- Acceptance: Hợp đồng lỗi, idempotency và khóa được ghi rõ

<a id="step-4"></a>
## Step 4 Tạo nền dự án và môi trường local

Tạo pnpm workspace, web/API/worker, Compose PostgreSQL, env mẫu và health check. Seed chỉ dùng dữ liệu giả.

- Tags: impl
- Phụ thuộc: 3
- Truy vết: Nền kỹ thuật
- Acceptance: Máy mới khởi động theo README
- Acceptance: Web, API và worker chạy; không có secret trong repo

<a id="step-5"></a>
## Step 5 Thiết lập CI và staging sớm

Đặt cổng PR và triển khai skeleton lên staging. Sau từng bước thêm test vào workflow tương ứng.

- Tags: build
- Phụ thuộc: 4
- Truy vết: CI/CD
- Acceptance: PR sai type hoặc build bị chặn
- Acceptance: Staging hiển thị đúng commit/digest

<a id="step-6"></a>
## Step 6 Tạo schema và migration nền

Tạo các entity catalogue, thẻ, mượn, giữ chỗ, ledger, policy, audit và outbox. Migration SQL được review trước dùng.

- Tags: db
- Phụ thuộc: 3, 4, 5
- Truy vết: ERD và toàn bộ F
- Acceptance: DB rỗng migrate thành công
- Acceptance: Unique barcode và LoanItem OPEN được DB cưỡng chế

<a id="step-7"></a>
## Step 7 Triển khai đăng nhập và quyền

Tích hợp OIDC, ma trận quyền và phạm vi reader. Tạo tài khoản demo qua provider cho staging.

- Tags: impl, security
- Phụ thuộc: 6
- Truy vết: F16,F21 mở rộng
- Acceptance: Sai issuer/audience bị từ chối
- Acceptance: Reader A không đọc được dữ liệu B
- Acceptance: API ghi audit không lộ token

<a id="step-8"></a>
## Step 8 Triển khai danh mục và bản sao

Xây đầu sách, tác giả, NXB, thể loại, bản sao, bìa và tra cứu. Ngừng dùng thay xóa dữ liệu có lịch sử.

- Tags: impl, db
- Phụ thuộc: 6, 7
- Truy vết: F01–F05,F15,F18
- Acceptance: Cây thể loại không có chu trình
- Acceptance: Không sửa ON_LOAN thành AVAILABLE bằng CRUD
- Acceptance: Tra cứu phân trang và bìa hoạt động

<a id="step-9"></a>
## Step 9 Triển khai độc giả và điều kiện

Cấp thẻ theo quy tắc đã duyệt; eligibility trả toàn bộ mã lý do theo thao tác. Phí tính từ ledger, quá hạn từ dueAt.

- Tags: impl, db
- Phụ thuộc: 1, 7, 8
- Truy vết: F06,F12
- Acceptance: Biên tuổi và cộng tháng cuối tháng đạt
- Acceptance: Mượn/gia hạn kiểm tra thẻ, nợ, quá hạn
- Acceptance: Trả sách không dùng eligibility chặn

<a id="step-10"></a>
## Step 10 Triển khai cho mượn chống tranh chấp

Xây quầy mượn và transaction all or nothing, policy snapshot, khóa và idempotency. Thu tiền và giữ chỗ chưa hoàn thiện phải fail closed theo điều kiện hiện có.

- Tags: impl, db
- Phụ thuộc: 8, 9
- Truy vết: F07
- Acceptance: Hai yêu cầu cùng copy chỉ một thành công
- Acceptance: Gửi lại key giữ một phiếu
- Acceptance: Một mục lỗi rollback cả phiếu

<a id="step-11"></a>
## Step 11 Triển khai sổ phí và thu tiền

Xây Charge, Payment, Allocation, Waiver, Reversal với số nguyên VND. Biểu phí là cấu hình đã duyệt trước khi tính mất/hỏng.

- Tags: impl, db
- Phụ thuộc: 1, 6, 7, 9
- Truy vết: F11
- Acceptance: Thu một phần và đảo khoản giữ số dư đúng
- Acceptance: Gửi lại không thu hai lần
- Acceptance: Miễn khoản cần quyền và lý do

<a id="step-12"></a>
## Step 12 Triển khai trả sách và ghi phí

Đóng LoanItem, cập nhật copy và ghi phí trong cùng transaction. Đặt adapter phân bổ giữ chỗ để nối bước tiếp theo.

- Tags: impl, db
- Phụ thuộc: 10, 11
- Truy vết: F08,UC22
- Acceptance: ReturnEvent duy nhất mỗi item
- Acceptance: Thẻ hết hạn và nợ vẫn trả được
- Acceptance: Phí dùng dueAt và policy đã lưu

<a id="step-13"></a>
## Step 13 Triển khai gia hạn và FIFO giữ chỗ

Nối return và mọi đường copy trở lại khả dụng với allocator; renew toàn bộ mục OPEN hoặc không mục nào. Expiry worker sử dụng cùng service.

- Tags: impl, db
- Phụ thuộc: 1, 10, 11, 12
- Truy vết: F09,F10
- Acceptance: Renew đồng thời không vượt giới hạn
- Acceptance: READY một copy một reservation
- Acceptance: Hết hạn và trả đồng thời giữ FIFO

<a id="step-14"></a>
## Step 14 Triển khai worker và thông báo

Xử lý lease outbox, nhắc hạn, expiry và retry hữu hạn. Ghi metric, attempt và dead-letter để thao tác xử lý lại có audit.

- Tags: impl, db
- Phụ thuộc: 13
- Truy vết: F19,F24 mở rộng
- Acceptance: Crash sau gửi không mất job
- Acceptance: Không gửi trước commit
- Acceptance: Quá attempt có cảnh báo

<a id="step-15"></a>
## Step 15 Triển khai báo cáo export và policy

Tạo report job snapshot, CSV theo quyền, cấu hình PolicyVersion bất biến; acquisition/retire F22 chỉ theo phạm vi mở rộng duyệt.

- Tags: impl, db
- Phụ thuộc: 11, 13, 14
- Truy vết: F13,F14,F20,F22 mở rộng
- Acceptance: Tổng hợp khớp chi tiết cùng snapshot
- Acceptance: Tệp riêng tư và tải kiểm tra quyền
- Acceptance: Policy mới không sửa khoản cũ

<a id="step-16"></a>
## Step 16 Hoàn thiện cổng độc giả

Nối tìm sách, lịch sử, sách đang mượn, đặt/hủy và gia hạn theo quyền đã duyệt. Responsive và trạng thái offline đúng giới hạn.

- Tags: impl, security
- Phụ thuộc: 2, 7, 13, 14, 15
- Truy vết: F10,F17,F18 và C06
- Acceptance: Dữ liệu chỉ thuộc reader đang đăng nhập
- Acceptance: 360px và keyboard dùng được
- Acceptance: Offline không ghi giao dịch

<a id="step-17"></a>
## Step 17 Kiểm chứng nghiệp vụ hiệu năng và UX

Chạy test cạnh tranh, E2E, accessibility và buổi sử dụng thử; đo NFR trên dữ liệu mô phỏng có quy mô công bố.

- Tags: test
- Phụ thuộc: 16
- Truy vết: F01–F20
- Acceptance: Các invariant và đường lỗi đạt
- Acceptance: Có báo cáo p95 và cấu hình tải
- Acceptance: Ít nhất 4/5 người hoàn thành thao tác mẫu

<a id="step-18"></a>
## Step 18 Hoàn thiện phát hành và phục hồi

Đưa cùng digest từ staging sang production sau signoff. Diễn tập migration, rollback và restore sang DB mới.

- Tags: build
- Phụ thuộc: 5, 14, 17
- Truy vết: CI/CD,F23 mở rộng
- Acceptance: Production dùng digest staging đã đạt
- Acceptance: Restore đo RPO và RTO
- Acceptance: Migration chỉ chạy một lần

<a id="step-19"></a>
## Step 19 Bàn giao hướng dẫn và cập nhật UML

Viết README, runbook quầy, xử lý lỗi, job thất bại và release; cập nhật mọi sơ đồ thay đổi theo phần mềm.

- Tags: docs
- Phụ thuộc: 18
- Truy vết: Toàn hệ thống
- Acceptance: Mỗi F có UC, API, màn hình và bằng chứng
- Acceptance: Hướng dẫn máy mới và vận hành đầy đủ

<a id="step-20"></a>
## Step 20 Rà soát điều kiện đưa vào sử dụng

Đối chiếu toàn bộ yêu cầu, quyền và release evidence. Chỉ mở sử dụng thật sau nghiệm thu của người phụ trách.

- Tags: review
- Phụ thuộc: 19
- Truy vết: F01–F24
- Acceptance: Không còn lỗi nghiêm trọng chưa xử lý
- Acceptance: Có biên bản go hoặc no go và danh sách tồn

## Vận hành ngân sách và rủi ro

Triển khai đề xuất trên Render gồm API phục vụ SPA, worker và PostgreSQL managed cùng vùng; Cloudflare R2 cho bìa và tệp xuất. Local dùng Compose. Staging có DB riêng và dữ liệu giả. Không sao chép nguyên dữ liệu độc giả thật để chạy demo hoặc test.

Production cần DB có backup phù hợp. Render cung cấp PITR cho PostgreSQL trả phí; gói Free không có recovery managed [T18]. Mục tiêu RPO 24 giờ và RTO 4 giờ cần backup độc lập, cảnh báo backup trễ và diễn tập restore. RPO là mục tiêu tổ chức, không suy ra từ số lần backup trên dashboard.

Lập bảng ngân sách trước bước 18: compute API và worker, DB và backup, object storage/egress, domain, email, gói GitHub và OIDC. Người phụ trách lấy báo giá hiện hành theo vùng, dung lượng và mức tải; chưa chốt ngân sách bằng con số khi chưa có quy mô thực tế.

Theo dõi request latency, 5xx, lock wait, deadlock, pool saturation, outbox age, retry count, export time và lần backup gần nhất. Log JSON có correlationId và actor ID tối thiểu; dashboard dành cho vận hành. Cảnh báo tới kênh do chủ hệ thống chọn.

Học và thực hiện theo mốc M0–M4. Gợi ý lập sprint 1–2 tuần và giới hạn một nhóm nghiệp vụ đang làm; đo thời gian ở M1 rồi ước lượng lại. Chưa có số người, kinh nghiệm và lịch nộp nên các mốc không phải cam kết ngày hoàn thành.

Rủi ro lớn nhất là quy tắc chưa duyệt, lỗi đồng thời và phạm vi mở rộng. Chủ nghiệp vụ chốt C01–C09; người phụ trách DB giữ invariant; người phát hành giữ bằng chứng migration và phục hồi. Giới hạn edition mutex có thể gây chờ khi nhiều người thao tác một đầu sách; chỉ thay chiến lược sau đo tải.

| Phạm vi sau giai đoạn đầu | Điều kiện xem xét |
|---|---|
| Native mobile và giao dịch offline | Có yêu cầu phần cứng hoặc mất mạng bắt buộc; thiết kế đồng bộ riêng |
| Microservices Kafka Redis Kubernetes | Số liệu tải hoặc tổ chức chứng minh cần tách |
| AI gợi ý sách và vector search | Tra cứu cơ bản đạt yêu cầu; có dữ liệu và mục tiêu đo rõ |
| Thanh toán trực tuyến và nhiều chi nhánh | Có đặc tả đối soát hoặc mô hình chi nhánh được duyệt |

## Lưu trữ tệp và đối chiếu tài liệu

Bìa công khai ở bucket riêng; kiểm tra MIME thực và kích thước trước khi lưu, không tin phần mở rộng. Tệp export và backup ở vùng riêng tư. Download export kiểm tra quyền và phạm vi rồi cấp URL ngắn hạn, dự kiến 5 phút; URL đã cấp là bearer link dùng được đến khi hết hạn [T19]. Nếu yêu cầu thu hồi tức thời, phục vụ qua API kiểm quyền mỗi lần thay vì signed URL trực tiếp.

Bản thiết kế trước vẫn là nguồn UC, trạng thái và luồng. Sau mỗi thay đổi code, cập nhật bảng truy vết F → UC → endpoint → màn hình → migration → testcase; ghi phiên bản UML vào release. Mọi thay đổi policy cần decision log trước khi sửa sơ đồ và đặc tả.

Repository dự án là https://github.com/theihoz/Lib-management.git. Đã clone và kiểm tra ngày 06/10/2026: chưa có commit, branch hoặc mã nguồn remote; checkout local có main chưa được tạo commit. Vì vậy TypeScript là ngôn ngữ được chọn trong kế hoạch, không phải ngôn ngữ phát hiện từ source đang có.

Đặt tài liệu vào docs/plan; khi bắt đầu triển khai, tạo commit khởi tạo rồi dùng nhánh ngắn feat, fix hoặc docs và PR vào main. Gắn PR với bước kế hoạch và tiêu chí nghiệm thu. Sau khi có CI, cấu hình required checks và review theo quyền/gói tài khoản. GitHub Actions nằm ở .github/workflows; tách quyền secrets staging và production.

File docs/plan/PLAN.md là kế hoạch có anchor step 1–20. Các lệnh điều phối agent cũ đã được loại bỏ; áp dụng quy trình dành cho team trong docs/operations/team-development.md.

Những việc cần chủ dự án cung cấp trước phát hành: quyết định C01–C09, số thành viên và mức kinh nghiệm, thời hạn, ngân sách hosting, provider OIDC, kênh email, quyền GitHub và dữ liệu khởi tạo được phép dùng.

## Nguồn tham khảo

Tài liệu kỹ thuật chính thức được tra cứu ngày 06/10/2026. Lựa chọn công nghệ và các chỉ tiêu là đề xuất của kế hoạch; nguồn không chứng minh ứng dụng đã đạt chúng.

- S1 [Google Docs thiết kế](https://docs.google.com/document/d/1aM0zXfRCbXduHbcH1MjuiCiB1BGI-0IPUnFsNsiWcc0/edit)
- S2 [Bộ UML editable](https://drive.google.com/file/d/1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn/view)
- T1 [Node.js LTS](https://nodejs.org/en/about/previous-releases)
- T2 [React lựa chọn công cụ app](https://react.dev/learn/creating-a-react-app)
- T3 [Vite yêu cầu runtime](https://vite.dev/guide/)
- T4 [NestJS modules và TypeScript](https://docs.nestjs.com/)
- T5 [PostgreSQL versioning](https://www.postgresql.org/support/versioning/)
- T6 [Drizzle transactions](https://orm.drizzle.team/docs/transactions)
- T7 [Radix accessibility](https://www.radix-ui.com/primitives/docs/overview/accessibility)
- T8 [PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- T9 [PostgreSQL partial index](https://www.postgresql.org/docs/current/indexes-partial.html)
- T10 [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- T11 [Render image deploy](https://render.com/docs/deploying-an-image)
- T12 [Render deploy hook](https://render.com/docs/deploy-hooks)
- T13 [GitHub Actions security](https://docs.github.com/en/actions/reference/security/secure-use)
- T14 [GitHub OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect)
- T15 [GitHub environments và giới hạn gói](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- T16 [OWASP ASVS](https://owasp.org/projects/asvs)
- T17 [Playwright](https://playwright.dev/docs/intro)
- T18 [Render PostgreSQL recovery](https://render.com/docs/postgresql-backups)
- T19 [Cloudflare R2 presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)