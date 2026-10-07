# Báo cáo rà soát và đồng bộ — 07/10/2026

## Kết quả và phạm vi

Nguồn tên/thuộc tính là DOCX do chủ dự án cung cấp. Quyết định trực tiếp chốt stack, F01–F24 và C01–C09. Giữ 38 bảng/288 trường nguồn; 4 bảng thiết kế bổ sung được tách rõ. Repo đang có scaffold/health/infra, chưa có CRUD/migration/Keycloak/frontend nghiệp vụ. Không tuyên bố đã chạy nghiệm thu.

| Mục | Sửa/bổ sung | Lý do |
| --- | --- | --- |
| Scope và technology | FastAPI/Python3.13/PG17; React TS Vite; Keycloak PKCE; F01–F24 | Bỏ mâu thuẫn stack/scope chưa duyệt trong nguồn cũ |
| DOCX | 65 đoạn nội dung; sửa 426 kiểu đoạn/ngắt trang sai; phụ lục A, 3 hình | Các dòng thuộc tính/đoạn trống bị đặt Heading1 + page break, render 572 trang; bản cuối 148 trang |
| DB | Từ điển 38/288; FK/NULL/type/index/migration; thêm 4 bảng riêng | Không đoán field từ số bảng; duyệt phí và consent cần dữ liệu |
| Tên và enum | FineCharge.assessed_amount; command DAMAGE → condition DAMAGED; LOST → return_kind LOST/condition NULL | Giữ đúng enum nguồn, không giả định đã nhận cuốn mất |
| Duyệt phí | PENDING → ASSESSED/CLOSED_NO_CHARGE; manager decision | Phí thủ công không ghi trực tiếp trước duyệt; chặn lưu thông đúng C03 |
| Identity/quyền | Matrix scope; provisioning; PKCE/JWKS/lock/reconcile | Không JIT/admin tự cấp; own-scope và quyền DB có thể kiểm chứng |
| API | OpenAPI3.1.0: 75 planned operations + 2 health; request DTO và safe read views | Contract client/backend cùng nguồn; version chỉ khi schema có |
| Events/jobs | v1 envelope/dedupe/lease/retry/consent/expiry | Không giữ transaction khi gọi mạng, không hứa email exactly-once |
| Security | Threat model theo trust boundary và acceptance cases | BOLA, permission, upload, private CSV, backup/restore cần kiểm soát cụ thể |
| QA/UI | 24 tiêu chí chức năng + concurrency cases; 12 wireframes desktop/mobile | Acceptance đều Not run; wireframe không giả là frontend runtime |
| UML | Sửa vùng hiện hành, thêm 14 khung; giữ ARCHIVE và một canvas | ERD chi tiết khớp DB; luồng phí/stack đồng bộ; mỗi khung có giải thích |
| Google Docs | Sửa 17 đoạn nghiệp vụ/stack/scope; mục19 và mục lục; H13.8/H14.4/H16.41 đúng mục; 70 bảng và 71 hình gốc giữ, thêm3 | Giữ ý và cấu trúc báo cáo; không gom hình mới cuối tài liệu |
| Chỉ mục/manifest | Cập nhật hash và provenance; ghi disposition UI cũ | Không coi file bị bỏ hoặc nguồn lịch sử là thiết kế hiện hành |

Tệp text trung gian do lần đồng bộ này tạo được đổi sang supplemental-specification.md; không xóa nội dung người dùng. Không khôi phục UI đã bị bỏ ở phiên trước; wireframe/motion mới thay vai trò tham khảo đó.

## Chứng cứ đã kiểm tra

- DOCX ZIP/XML đọc được; đủ tên 38 bảng/288 dòng thuộc tính; các media gốc được giữ. Render toàn tài liệu thành 148 PNG/PDF, xem contact sheets mọi trang và hình bổ sung. Đây là kiểm tra bố cục tổng thể, không là kiểm thử phần mềm.
- OpenAPI: JSON đọc được, 77 operationId duy nhất, mọi local $ref giải được; health responses đối chiếu main.py đúng ok/ready/not_ready. Đây là kiểm tra cấu trúc/reference; chưa chạy validator OpenAPI chuyên dụng hoặc contract tests runtime.
- UML: đúng 1 diagram, 3.020 cells, ID duy nhất, parent/source/target hợp lệ. 94 khung = 80 gốc + 14 bổ sung.
- Drive cùng file ID 1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn, modifiedTime 2026-10-07T08:12:43.043Z. Tải lại bytes, SHA256 **b28dd0080f3fb9c08eb97c1f5b142b3b6594efbf93f4ebe28c97003deffcbe01** khớp repo. Không cần tạo file UML khác.
- Google Docs đọc lại qua trusted-read: revision **AHj4eMTN_YIyEFChu2PHIHn1a1LgsABTnIJ8mgL58UsF05GSSuEbPH1BfKEYr7sMeVZLhLL5utRgtBInId3hFrZqn8_sIHtzOLLYycAiSZf-**, tab t.0, 74 inline objects. Có section19 và ba hình mới ở mục tương ứng. [Snapshot text](live-report-snapshot.md) lưu nội dung/index, không lưu nguyên layout/hình.
- Export DOCX native được connector tạo nhưng tải link về máy trả HTTP403; **library-software-design.docx không phải export của báo cáo live**. Nó là bản nguồn đã sửa và có phụ lục tương ứng. Bản Google Docs nguồn 1aM0… và kế hoạch cũ vẫn là lịch sử, chưa được sửa live trong lần này.
- Draw.io UI yêu cầu OAuth khi xem Drive trong phiên browser mới; chưa xác nhận render toàn canvas trong UI. Đồng bộ cloud đã được xác minh bằng bytes/hash. Wireframe chưa được screenshot trong browser; policy chặn file://. Không suy ra accessibility/visual runtime đã đạt.
- Chỉnh nội dung repo qua Dev Container đang mở; bộ render tài liệu dùng runtime bundled trên host. Chưa commit/push trong lần này.

## Điểm cần chủ dự án xác nhận

1. **N03:** Reader.email và Category.name có bắt buộc duy nhất không? Chưa thêm UQ ngoài nguồn; email IdP khác email liên hệ Reader.
2. **N04:** Giới hạn upload ảnh, retention audit/artifact, hosting/storage và ngân sách; chưa gán số như quy định đã duyệt.
3. **N05:** Người giao BM01 lưu riêng thế nào? AcquisitionReceipt nguồn DRAFT/POSTED/CANCELLED; chọn duyệt+post cùng transaction hoặc bổ sung APPROVED. UML/API/wireframe đánh dấu điểm mở này.
4. **N06:** In thẻ/báo cáo, Excel/PDF và chỉ số nâng cao; F01–F24, CSV Quản lý, portal/email và staff provisioning đã chốt.
5. **N07/vận hành:** Workload/môi trường đo hiệu năng, RPO/RTO, lịch và retention backup, provider email; các mục tiêu và retry defaults chưa là kết quả đo.

N01 không cần bảng giá mất/hỏng tự động trong phiên bản hiện hành; thủ công có đề xuất/duyệt đã chốt. N02 stack/auth đã chốt. Tự đăng ký tắt. Lịch nhắc08:00, token5min/skew30s, lease/retry trong docs là mặc định đề xuất, cần review khi triển khai.

## Cách tiếp tục

Đóng N05 trước migration tiếp nhận. Triển khai BE00/identity/schema rồi lưu thông/tài chính; dùng OpenAPI và acceptance để review từng PR. Các thay đổi tương lai phải cập nhật DB/permission/API/UML/plan cùng nhau theo [chỉ mục thiết kế](README.md).
