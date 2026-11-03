# Tích hợp frontend từ bộ thiết kế libmanagement-figma

Ngày: 03/11/2026. Nhánh thực hiện: `frontend`.

## Phạm vi đã chọn

Người dùng chọn dựng đủ giao diện theo Figma, nối API hiện có và chuẩn bị client
cho API nghiệp vụ. Nguồn thiết kế là `docs/libmanagement-figma/screens.json`, các
board SVG desktop/mobile và `docs/plan/frontend/DESIGN-DIRECTION.md`.

Bao phủ 71 màn hình thuộc FE01–FE11 bằng các trang React có điều hướng và thành
phần dùng chung; không dùng ảnh SVG toàn màn hình thay giao diện. Giữ React,
TypeScript, Vite, cấu hình runtime và proxy `/api`, `/health` hiện tại.

## Các cách triển khai

1. **Cách người dùng chọn:** giao diện đầy đủ, API client theo OpenAPI; chỉ xác
   nhận tích hợp thật cho các endpoint backend đã có. Có chế độ xem thiết kế ở
   môi trường development để xem dữ liệu minh họa của tất cả màn hình.
2. Bổ sung toàn bộ backend nghiệp vụ cùng lúc: cần mô hình dữ liệu, migration,
   giao dịch và kiểm thử nghiệp vụ; người dùng không chọn phạm vi này.
3. Nhúng board SVG: xem được bản vẽ nhưng không có biểu mẫu, bàn phím và dữ liệu
   động; không đáp ứng yêu cầu gắn frontend vào ứng dụng.

## Thiết kế và hành vi

- Nền giấy #F7F5EF, sidebar #142C35 rộng 232px, primary #174B73, serif Georgia
  cho tiêu đề; token màu và spacing theo tài liệu hiện có.
- App shell có sidebar, breadcrumb, ngày theo Asia/Ho_Chi_Minh, nhóm chức năng;
  mobile dùng drawer và bố cục một cột. Các trang portal có bố cục đọc sách.
- Thành phần chung: button, field, status badge, bảng responsive, toolbar,
  dialog xác nhận, trạng thái loading/empty/error, bìa sách fallback, biên nhận.
- 11 nhóm: xác thực, danh mục, độc giả/thẻ, mượn, trả, giữ chỗ/gia hạn, tài chính,
  portal, báo cáo/quy định, quản trị/kho, vận hành. Route registry tập trung ánh
  xạ trang, quyền và chức năng; các biến thể lỗi/biên nhận có thể xem trong bộ
  duyệt thiết kế.
- Chế độ xem thiết kế chỉ trong development, có nhãn dữ liệu minh họa rõ ràng;
  thao tác mẫu không ghi dữ liệu và không báo thành công như một giao dịch thật.
  Mã/dữ liệu mẫu được tách để không đi vào production build.
- Chế độ thật gọi endpoint tương ứng. Khi endpoint chưa được backend triển
  khai, hiển thị trạng thái không tải được/chưa khả dụng và giữ nội dung đang
  nhập; không thay bằng dữ liệu giả và không giả thành công.

## Kết nối API và phiên đăng nhập

- Sinh kiểu TypeScript từ `docs/design/openapi.json`; client dùng URL runtime,
  Bearer token, request ID, ErrorResponse và AbortSignal.
- Có hàm theo module cho catalog, readers, circulation, finance, portal,
  administration, operations; payload/response theo hợp đồng thiết kế.
- Mutation hỗ trợ Idempotency-Key cho thao tác được hợp đồng yêu cầu; giữ khóa
  khi retry cùng payload, tạo khóa mới khi payload thay đổi.
- Keycloak OIDC Authorization Code + PKCE qua thư viện chính thức; token chỉ
  ở bộ nhớ. `/auth/me` là nguồn account và quyền, không dùng JWT role thay DB.
- Có trang đăng nhập, đang xác minh, hết phiên, thiếu quyền, tài khoản bị khóa,
  lỗi mạng và xác nhận đăng xuất. Guard/UI quyền không thay kiểm tra ở API.
- Nối health/readiness thật qua Vite proxy. Keycloak hiện chưa chạy nên không
  tuyên bố đã kiểm chứng đăng nhập SSO đầy đủ trong môi trường hiện tại.

## Giới hạn và bảo toàn workspace

Không triển khai endpoint nghiệp vụ hoặc thay schema backend. Không thay đổi
các file của người dùng đã có trong workspace. Không merge vào `main`, không
publish website hay push nhánh nếu chưa có yêu cầu.

## Kiểm chứng

Chạy lint, format check, typecheck, unit/component test, production build;
kiểm tra kiểu API không lệch hợp đồng, dữ liệu mẫu không lọt vào production.
Kiểm tra HTTP frontend/config/modules và proxy readiness đến PostgreSQL thật.
Kiểm thử các ranh giới quan trọng: API error, idempotency, permission guard,
điều hướng thiết kế, validation, trạng thái endpoint chưa có. Ghi rõ giới hạn
nếu không có trình duyệt để kiểm tra hình ảnh/keyboard trực tiếp.

## Bổ sung phạm vi được người dùng yêu cầu trong khi triển khai

Sau khi duyệt thiết kế, người dùng yêu cầu bổ sung REST API còn thiếu cho các
màn hình. Phần giới hạn không triển khai backend ở trên được thay bằng: API
nghiệp vụ dùng Python/FastAPI trong `apps/api`, giữ hợp đồng OpenAPI, RBAC,
giao dịch, idempotency và migration. TypeScript trong `apps/web/src/api` chỉ là
client HTTP; không chứa backend hoặc thay quyền do server kiểm tra.

Người dùng cũng yêu cầu tối ưu ảnh/lazy loading, chia chunk, cache API, debounce,
phân trang, skeleton, giảm render dư, nén payload, connection pool, index,
cache tính toán server, CDN, load balancer và Lighthouse. Áp dụng trực tiếp các
tối ưu ứng dụng; CDN/load balancer có cấu hình triển khai riêng, không tự mua
dịch vụ hoặc tuyên bố đã triển khai cloud. Không cache chung dữ liệu phiên,
PII hoặc phản hồi có kiểm tra RBAC. Báo cáo Lighthouse ghi đúng URL, bản build,
thiết bị và môi trường đã chạy.

## Điều chỉnh 03/11/2026: giao diện thật theo spec lõi

Người dùng yêu cầu giao diện thật, không phải bản demo. Phạm vi 71 màn, chế độ xem
thiết kế và dữ liệu minh họa ở trên không còn là hướng triển khai:

- Đăng ký route chỉ gồm lõi 10 tuần (F01–F09, F11–F14, F16, F18–F20); mượn giữ chỗ,
  lịch sử portal, tài khoản/nhập kho/thanh lý và vận hành (nhóm 10, 11) thuộc phase 2.
- Không còn `DesignBrowser`, `fixtures` hay khám phá chức năng qua `/openapi.json`;
  mỗi màn gọi API thật và hiển thị lỗi thật (401/403/404/409/422/503).
- Quyền của route theo [ma trận quyền](permission-matrix.md); API vẫn là nơi quyết định.
- Quầy mượn/trả/gia hạn tra cứu theo số thẻ và mã vạch (`/readers/lookup`,
  `/copies/lookup`, `GET /loans`), không yêu cầu nhập UUID.
- Báo cáo/CSV: tạo job → theo dõi trạng thái → xem kết quả đã vật hóa → tải CSV qua
  client có Bearer. Phiên khôi phục bằng Keycloak `check-sso` + silent SSO.
- Lighthouse, CDN, load balancer: xem `deploy/PERFORMANCE.md`; chưa có số đo Lighthouse
  thật cho đến khi chạy được trên bản build production.
