# Thiết kế cơ sở dữ liệu PostgreSQL

**Ngày đồng bộ:** 2026-10-07 · **Trạng thái:** Đặc tả thiết kế, chưa phải triển khai/nghiệm thu.

Nguồn: DOCX chính, Google Docs live và các quyết định đã duyệt trong [decisions](../plan/decisions.md). Khi nguồn cũ mâu thuẫn, quyết định trực tiếp của người dùng được áp dụng; thuộc tính gốc giữ theo DOCX.

## Quy ước vật lý và ranh giới

UUID bất biến; bảng vật lý snake_case số ít; PK ghép giữ nguyên. Các cột giữ đúng snake_case DOCX. FK mặc định RESTRICT; không cascade xóa lịch sử. Tiền numeric(14,0), API chuỗi số nguyên; timestamptz lưu UTC, nghiệp vụ Asia/Ho_Chi_Minh; date cho ngày sinh. ID UUID sinh phía server, created_at DEFAULT now() khi nguồn quy định. Không thêm default cho cột nguồn chưa quy định.

## Danh mục và từ điển 38 bảng

### 1. Publisher → `publisher`

Truy vết: F05. Quy tắc: Không xóa khi còn ấn bản tham chiếu.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| name | varchar(200) | Không | CHECK không rỗng | Tên nhà xuất bản |
| address | text | Có | — | Địa chỉ liên hệ |
| status | varchar(16) | Không | ACTIVE/INACTIVE | Trạng thái danh mục |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 2. Author → `author`

Truy vết: F04. Quy tắc: Tên không phải định danh duy nhất.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| name | varchar(200) | Không | CHECK không rỗng | Tên tác giả |
| biography | text | Có | — | Giới thiệu |
| status | varchar(16) | Không | ACTIVE/INACTIVE | Trạng thái |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 3. Category → `category`

Truy vết: F03. Quy tắc: Cấm chu trình; giữ các thể loại gốc theo QĐ04.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| code | varchar(32) | Không | UQ | Mã thể loại |
| name | varchar(120) | Không | — | Tên thể loại |
| parent_id | uuid | Có | FK Category.id | Thể loại cha |
| is_root | boolean | Không | DEFAULT false | Cờ gốc được bảo vệ |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 4. BookEdition → `book_edition`

Truy vết: F01,F18. Quy tắc: ISBN chuẩn hóa, unique khi có; năm theo C09; version dùng optimistic concurrency.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| isbn | varchar(13) | Có | UQ | ISBN chuẩn hóa |
| title | varchar(300) | Không | CHECK không rỗng | Nhan đề |
| publication_year | smallint | Không | — | Năm xuất bản |
| publisher_id | uuid | Có | FK Publisher.id | Nhà xuất bản |
| language | varchar(32) | Có | — | Ngôn ngữ |
| description | text | Có | — | Mô tả nội dung |
| status | varchar(16) | Không | ACTIVE/INACTIVE | Trạng thái |
| version | integer | Không | DEFAULT 1; >0 | Phiên bản cập nhật |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 5. BookAuthor → `book_author`

Truy vết: F01,F04. Quy tắc: Quan hệ N:N, không có id riêng.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| edition_id | uuid | Không | PK ghép; FK BookEdition.id | Ấn bản |
| author_id | uuid | Không | PK ghép; FK Author.id | Tác giả |
| ordinal | smallint | Không | >0; UQ edition_id+ordinal | Thứ tự trình bày |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 6. BookCategory → `book_category`

Truy vết: F01,F03. Quy tắc: Quan hệ N:N.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| edition_id | uuid | Không | PK ghép; FK BookEdition.id | Ấn bản |
| category_id | uuid | Không | PK ghép; FK Category.id | Thể loại |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 7. Location → `location`

Truy vết: F02. Quy tắc: Mã kệ duy nhất trong thư viện.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| code | varchar(32) | Không | UQ | Mã kệ/vị trí |
| name | varchar(120) | Không | — | Tên vị trí |
| status | varchar(16) | Không | ACTIVE/INACTIVE | Khả dụng |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 8. BookCopy → `book_copy`

Truy vết: F02,F07,F08,F10. Quy tắc: Không lưu tổng tồn; không đổi trạng thái ngoài lệnh nghiệp vụ.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| edition_id | uuid | Không | FK BookEdition.id | Ấn bản |
| barcode | varchar(64) | Không | UQ | Mã vạch |
| location_id | uuid | Có | FK Location.id | Vị trí hiện tại |
| status | varchar(16) | Không | AVAILABLE/ON_LOAN/HELD/REPAIR/LOST/RETIRED | Trạng thái vật lý |
| acquired_at | timestamptz | Không | — | Ngày tiếp nhận |
| source_receipt_item_id | uuid | Có | FK AcquisitionReceiptItem.id (mở rộng) | Dòng nhập nguồn |
| version | integer | Không | DEFAULT 1; >0 | Phiên bản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 9. MediaAsset → `media_asset`

Truy vết: F15,F20. Quy tắc: Chỉ lưu metadata; bìa công khai, export riêng tư; không lưu secret.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| edition_id | uuid | Có | FK BookEdition.id | Ấn bản nếu là bìa |
| object_key | text | Không | UQ | Khóa object storage |
| mime_type | varchar(100) | Không | — | MIME đã kiểm tra |
| byte_size | bigint | Không | >0 | Dung lượng |
| sha256 | char(64) | Không | — | Hash nội dung |
| visibility | varchar(16) | Không | PUBLIC/PRIVATE | Phạm vi tải |
| status | varchar(16) | Không | PENDING/READY/REJECTED/DELETED | Vòng đời tệp |
| uploaded_by | uuid | Không | FK Account.id | Người tải |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 10. Reader → `reader`

Truy vết: F06,F17,F18. Quy tắc: Không xóa cứng khi có lịch sử; không lưu dư nợ tổng.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| reader_code | varchar(32) | Không | UQ | Mã độc giả |
| full_name | varchar(200) | Không | — | Họ tên |
| birth_date | date | Không | — | Ngày sinh, tuổi tính khi cấp thẻ |
| reader_type | varchar(8) | Không | X/Y/Z dự thảo | Loại độc giả |
| email | varchar(254) | Có | — | Email liên hệ |
| phone | varchar(32) | Có | — | Điện thoại |
| address | text | Có | — | Địa chỉ |
| status | varchar(16) | Không | ACTIVE/SUSPENDED/INACTIVE | Trạng thái |
| version | integer | Không | DEFAULT 1 | Phiên bản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 11. ReaderCard → `reader_card`

Truy vết: F06,F12. Quy tắc: expires_at>issued_at; thẻ hợp lệ khi ACTIVE và trong khoảng hiệu lực; giữ lịch sử cấp lại.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| reader_id | uuid | Không | FK Reader.id | Chủ thẻ |
| card_no | varchar(64) | Không | UQ | Số thẻ |
| issued_at | timestamptz | Không | — | Thời điểm cấp |
| expires_at | timestamptz | Không | — | Hết hiệu lực |
| status | varchar(16) | Không | ACTIVE/BLOCKED/REVOKED | Trạng thái; hết hạn tính từ thời gian |
| issued_by | uuid | Không | FK Account.id | Người cấp |
| policy_version_id | uuid | Không | FK PolicyVersion.id | Quy định cấp thẻ |
| version | integer | Không | DEFAULT 1 | Phiên bản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 12. Account → `account`

Truy vết: F16,F21; kiểm quyền F01–F20. Quy tắc: OIDC: UQ issuer+subject; reader_id UQ khi có. Local auth là lựa chọn riêng, không lưu mật khẩu rõ.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| issuer | text | Không | — | Nhà phát hành định danh |
| subject | text | Không | UQ ghép issuer+subject | Định danh bên IdP |
| reader_id | uuid | Có | FK Reader.id; UQ | Ánh xạ độc giả |
| display_name | varchar(200) | Không | — | Tên hiển thị |
| status | varchar(16) | Không | ACTIVE/LOCKED/DISABLED | Trạng thái |
| auth_version | integer | Không | DEFAULT 1 | Thu hồi phiên khi tăng |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 13. Role → `role`

Truy vết: F21; quyền F01–F20. Quy tắc: Bốn vai trò trong tài liệu; không cấp quyền chỉ từ UI.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| code | varchar(64) | Không | UQ | Mã vai trò |
| name | varchar(120) | Không | — | Tên vai trò |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 14. Permission → `permission`

Truy vết: F21; quyền F01–F20. Quy tắc: Mã quyền ổn định theo hành động.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| code | varchar(100) | Không | UQ | Mã quyền |
| description | text | Không | — | Ý nghĩa quyền |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 15. AccountRole → `account_role`

Truy vết: F21. Quy tắc: Ghi audit khi cấp/thu hồi; tài khoản nhân viên không dùng chung.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| account_id | uuid | Không | PK ghép; FK Account.id | Tài khoản |
| role_id | uuid | Không | PK ghép; FK Role.id | Vai trò |
| granted_by | uuid | Không | FK Account.id | Người cấp |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 16. RolePermission → `role_permission`

Truy vết: F21. Quy tắc: Quan hệ N:N; kiểm quyền trên máy chủ.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| role_id | uuid | Không | PK ghép; FK Role.id | Vai trò |
| permission_id | uuid | Không | PK ghép; FK Permission.id | Quyền |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 17. PolicyVersion → `policy_version`

Truy vết: F14; áp dụng F06–F12. Quy tắc: Không sửa rules đã ACTIVE/SUPERSEDED; hiệu lực không chồng lấn; C01–C09 đã được chủ dự án duyệt.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| version_no | integer | Không | UQ; >0 | Số phiên bản |
| effective_from | timestamptz | Không | — | Bắt đầu hiệu lực |
| effective_to | timestamptz | Có | — | Kết thúc độc quyền |
| status | varchar(16) | Không | DRAFT/ACTIVE/SUPERSEDED | Trạng thái |
| rules | jsonb | Không | Schema validation | Hạn mức, tuổi, phí, thời hạn |
| rules_schema_version | integer | Không | >0 | Phiên bản schema JSON |
| approved_by | uuid | Có | FK Account.id | Bắt buộc khi ACTIVE |
| approved_at | timestamptz | Có | — | Thời điểm duyệt |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 18. Loan → `loan`

Truy vết: F07,F09,F18. Quy tắc: Trạng thái phiếu tính từ LoanItem; gia hạn toàn bộ mục OPEN hoặc rollback toàn bộ.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| loan_no | varchar(64) | Không | UQ | Số phiếu |
| reader_id | uuid | Không | FK Reader.id | Độc giả |
| card_id | uuid | Không | FK ReaderCard.id | Thẻ đã dùng |
| issued_by | uuid | Không | FK Account.id | Thủ thư |
| issued_at | timestamptz | Không | — | Ngày mượn |
| renewal_count | integer | Không | >=0; DEFAULT 0 | Số lần gia hạn phiếu |
| version | integer | Không | DEFAULT 1 | Phiên bản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 19. LoanItem → `loan_item`

Truy vết: F07,F08,F09,F19. Quy tắc: OPEN=closed_at NULL; partial UQ copy_id cho OPEN; due_at>=issued_at; closed_at>=issued_at; closure_reason đồng bộ closed_at.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| loan_id | uuid | Không | FK Loan.id | Phiếu mượn |
| copy_id | uuid | Không | FK BookCopy.id | Bản sao |
| issued_at | timestamptz | Không | — | Bắt đầu mượn |
| due_at | timestamptz | Không | — | Hạn trả hiện hành |
| closed_at | timestamptz | Có | — | Đóng mục |
| closure_reason | varchar(16) | Có | RETURNED/LOST/VOIDED | Lý do đóng |
| policy_version_id | uuid | Không | FK PolicyVersion.id | Policy ban đầu |
| applied_rules | jsonb | Không | — | Snapshot quy tắc ban đầu |
| version | integer | Không | DEFAULT 1 | Phiên bản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 20. RenewalEvent → `renewal_event`

Truy vết: F09. Quy tắc: Một event gồm các RenewalItem; append-only; UQ loan_id+sequence_no.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| loan_id | uuid | Không | FK Loan.id | Phiếu gia hạn |
| sequence_no | integer | Không | >0 | Thứ tự gia hạn |
| actor_id | uuid | Không | FK Account.id | Người thực hiện |
| renewed_at | timestamptz | Không | — | Thời điểm |
| policy_version_id | uuid | Không | FK PolicyVersion.id | Policy quyết định gia hạn |
| request_id | varchar(100) | Không | — | Mã tương quan yêu cầu |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 21. RenewalItem → `renewal_item`

Truy vết: F09. Quy tắc: new_due_at>old_due_at; item thuộc loan của event; kiểm trong transaction.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| renewal_event_id | uuid | Không | PK ghép; FK RenewalEvent.id | Lần gia hạn |
| loan_item_id | uuid | Không | PK ghép; FK LoanItem.id | Mục mượn |
| old_due_at | timestamptz | Không | — | Hạn trước |
| new_due_at | timestamptz | Không | — | Hạn sau |
| applied_rules | jsonb | Không | — | Quy tắc gia hạn đã dùng |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 22. ReturnEvent → `return_event`

Truy vết: F08. Quy tắc: UQ loan_item_id; append-only; mất ghi LOST và condition NULL, không giả định đã nhận sách.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| loan_item_id | uuid | Không | FK LoanItem.id; UQ | Mục được đóng |
| return_kind | varchar(16) | Không | RETURNED/LOST/VOIDED | Kiểu xử lý |
| condition | varchar(16) | Có | GOOD/DAMAGED | Tình trạng khi nhận |
| returned_at | timestamptz | Không | — | Thời điểm xử lý trả/mất |
| processed_by | uuid | Không | FK Account.id | Người xử lý |
| notes | text | Có | — | Biên bản/lý do |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 23. Reservation → `reservation`

Truy vết: F10. Quy tắc: FIFO created_at+id; READY cần copy/ready_at/expiry; UQ copy READY; UQ reader+edition QUEUED/READY; copy phải cùng edition; policy thời hạn snapshot.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| reader_id | uuid | Không | FK Reader.id | Độc giả |
| edition_id | uuid | Không | FK BookEdition.id | Ấn bản xếp hàng |
| copy_id | uuid | Có | FK BookCopy.id | Copy phân bổ khi READY |
| fulfilled_loan_item_id | uuid | Có | FK LoanItem.id; UQ | Mục đã nhận |
| status | varchar(16) | Không | QUEUED/READY/FULFILLED/CANCELLED/EXPIRED | Trạng thái |
| ready_at | timestamptz | Có | — | Bắt đầu giữ |
| ready_expires_at | timestamptz | Có | — | Hạn nhận |
| cancellation_reason | text | Có | — | Lý do hủy |
| policy_version_id | uuid | Không | FK PolicyVersion.id | Policy đặt chỗ |
| applied_rules | jsonb | Không | — | Snapshot; hạn READY chốt khi phân bổ |
| version | integer | Không | DEFAULT 1 | Phiên bản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 24. FineCharge → `fine_charge`

Truy vết: F08,F11,F12. Quy tắc: assessed_amount>0; 0 không tạo khoản; VND; ghi manual_reason nếu thủ công; dư nợ là projection.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| reader_id | uuid | Không | FK Reader.id | Người chịu phí |
| loan_item_id | uuid | Có | FK LoanItem.id | Mục gây phí |
| policy_version_id | uuid | Không | FK PolicyVersion.id | Policy tính phí |
| reason | varchar(16) | Không | LATE/DAMAGE/LOST/MANUAL | Loại phí |
| assessed_amount | numeric(14,0) | Không | >0 | Số tiền phát sinh VND |
| late_days | integer | Có | >=0 | Ngày trễ snapshot theo C08 |
| unit_rate | numeric(14,0) | Có | >=0 | Đơn giá snapshot |
| calculation | jsonb | Không | — | Công thức và dữ liệu tính |
| manual_reason | text | Có | — | Lý do thủ công |
| assessed_by | uuid | Không | FK Account.id | Người ghi phí |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 25. Payment → `payment`

Truy vết: F11. Quy tắc: Số tiền thu khác phí phát sinh; append-only; không tích hợp thanh toán online trong phạm vi này.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| reader_id | uuid | Không | FK Reader.id | Người nộp |
| receipt_no | varchar(64) | Không | UQ | Số biên nhận |
| amount | numeric(14,0) | Không | >0 | Tiền thu VND |
| method | varchar(24) | Không | CASH/TRANSFER_RECORD | Phương thức ghi nhận |
| received_at | timestamptz | Không | — | Ngày thu |
| received_by | uuid | Không | FK Account.id | Người thu |
| reference | text | Có | — | Tham chiếu chuyển khoản |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 26. PaymentAllocation → `payment_allocation`

Truy vết: F11. Quy tắc: Cùng reader; net phân bổ không vượt payment/charge; PK ghép đúng từ điển cũ; thêm phân bổ bằng chứng từ mới.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| payment_id | uuid | Không | PK ghép; FK Payment.id | Chứng từ thu |
| charge_id | uuid | Không | PK ghép; FK FineCharge.id | Khoản phí |
| amount | numeric(14,0) | Không | >0 | Số tiền phân bổ VND |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 27. Waiver → `waiver`

Truy vết: F11. Quy tắc: Append-only; không vượt dư nợ sau khóa charge; người duyệt có permission.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| charge_id | uuid | Không | FK FineCharge.id | Khoản phí |
| amount | numeric(14,0) | Không | >0 | Tiền miễn VND |
| approved_by | uuid | Không | FK Account.id | Người duyệt |
| reason | text | Không | Không rỗng | Lý do |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 28. PaymentReversal → `payment_reversal`

Truy vết: F11. Quy tắc: Tổng đảo<=Payment.amount; đảo phân bổ cần ghi đồng thời; net phân bổ<=net thu.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| payment_id | uuid | Không | FK Payment.id | Chứng từ gốc |
| amount | numeric(14,0) | Không | >0 | Tiền đảo VND |
| actor_id | uuid | Không | FK Account.id | Người duyệt |
| reason | text | Không | — | Lý do |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 29. AllocationReversal → `allocation_reversal`

Truy vết: F11. Quy tắc: FK ghép bảo đảm giao dịch gốc tồn tại; tổng đảo<=allocation.amount; khóa cả payment và charge.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| payment_id | uuid | Không | FK ghép PaymentAllocation.payment_id | Chứng từ gốc |
| charge_id | uuid | Không | FK ghép PaymentAllocation.charge_id | Khoản phí gốc |
| amount | numeric(14,0) | Không | >0 | Tiền đảo VND |
| actor_id | uuid | Không | FK Account.id | Người duyệt |
| reason | text | Không | — | Lý do |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 30. WaiverReversal → `waiver_reversal`

Truy vết: F11. Quy tắc: Tổng đảo<=Waiver.amount; hoàn dư nợ có audit, không sửa khoản cũ.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| waiver_id | uuid | Không | FK Waiver.id | Miễn giảm gốc |
| amount | numeric(14,0) | Không | >0 | Tiền đảo VND |
| actor_id | uuid | Không | FK Account.id | Người duyệt |
| reason | text | Không | — | Lý do |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 31. IdempotencyRecord → `idempotency_record`

Truy vết: F07–F11,F20. Quy tắc: UQ actor+operation+key; payload khác trả 409; kết quả commit cùng nghiệp vụ; hạn giữ bao phủ retry.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| actor_id | uuid | Không | FK Account.id | Chủ yêu cầu |
| operation | varchar(64) | Không | — | Loại lệnh |
| key | varchar(128) | Không | — | Khóa retry |
| payload_hash | char(64) | Không | — | Hash payload chuẩn hóa |
| response_status | smallint | Có | — | HTTP status sau hoàn tất |
| response_body | jsonb | Có | — | Kết quả đã redaction |
| state | varchar(16) | Không | PENDING/COMPLETED | Trạng thái |
| expires_at | timestamptz | Không | — | Hạn giữ |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 32. OutboxEvent → `outbox_event`

Truy vết: F19,F24. Quy tắc: Ghi cùng transaction; không gọi mạng khi giữ khóa; event id cũng là dedupe key cho consumer.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| aggregate_type | varchar(64) | Không | — | Loại aggregate |
| aggregate_id | uuid | Không | — | Tham chiếu logic, không FK đa hình |
| event_type | varchar(100) | Không | — | Loại sự kiện |
| payload | jsonb | Không | — | Dữ liệu tối thiểu đã redaction |
| processed_at | timestamptz | Có | — | Đã hoàn tất dispatch |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 33. Job → `job`

Truy vết: F19,F20,F24. Quy tắc: Lease/attempt/retry hữu hạn; expired lease được nhận lại; unique dedupe_key.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| outbox_event_id | uuid | Có | FK OutboxEvent.id | Nguồn event |
| dedupe_key | varchar(200) | Không | UQ | Khóa chống tạo trùng |
| job_type | varchar(64) | Không | — | Loại tác vụ |
| payload | jsonb | Không | — | Dữ liệu handler |
| status | varchar(16) | Không | QUEUED/RUNNING/SUCCEEDED/FAILED/DEAD | Trạng thái |
| attempt | integer | Không | >=0; DEFAULT 0 | Lần thử |
| lease_owner | varchar(100) | Có | — | Worker nhận |
| lease_until | timestamptz | Có | — | Hạn lease |
| next_attempt_at | timestamptz | Có | — | Lịch thử lại |
| last_error_code | varchar(100) | Có | — | Lỗi không chứa secret |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 34. ReportJob → `report_job`

Truy vết: F13,F20. Quy tắc: Gộp Report/ExportJob theo job_type; không tạo bảng thứ hai đồng nghĩa; kiểm quyền lúc yêu cầu và tải.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| job_id | uuid | Không | FK Job.id; UQ | Tác vụ thực thi |
| requested_by | uuid | Không | FK Account.id | Người yêu cầu |
| report_type | varchar(64) | Không | — | Loại báo cáo |
| filter_snapshot | jsonb | Không | — | Bộ lọc và scope đã kiểm quyền |
| as_of | timestamptz | Không | — | Mốc snapshot báo cáo |
| artifact_id | uuid | Có | FK MediaAsset.id | Tệp riêng tư |
| expires_at | timestamptz | Có | — | Hạn tải |
| row_count | bigint | Có | >=0 | Số dòng xuất |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 35. AuditLog → `audit_log`

Truy vết: F01–F24. Quy tắc: Append-only, quyền ghi riêng; actor NULL chỉ cho hệ thống/khách có actor_type; target là tham chiếu logic.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| actor_id | uuid | Có | FK Account.id | Người thao tác |
| actor_type | varchar(16) | Không | USER/SYSTEM/ANONYMOUS | Loại chủ thể |
| action | varchar(100) | Không | — | Hành động |
| permission_code | varchar(100) | Có | — | Quyền đã kiểm |
| target_type | varchar(64) | Không | — | Loại đối tượng |
| target_id | uuid | Có | — | ID logic, không FK đa hình |
| request_id | varchar(100) | Không | — | Tương quan |
| outcome | varchar(16) | Không | SUCCESS/DENIED/FAILED | Kết quả |
| metadata | jsonb | Không | — | Before/after đã redaction |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 36. AcquisitionReceipt → `acquisition_receipt`

Truy vết: F22. Quy tắc: DRAFT/POSTED/CANCELLED; POSTED bất biến, tạo copy đúng số lượng; tổng tiền tính từ dòng.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| receipt_no | varchar(64) | Không | UQ | Số phiếu |
| supplier | varchar(200) | Không | — | Nhà cung cấp |
| received_at | timestamptz | Không | — | Ngày nhận |
| status | varchar(16) | Không | DRAFT/POSTED/CANCELLED | Trạng thái |
| approved_by | uuid | Có | FK Account.id | Bắt buộc khi POSTED |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 37. AcquisitionReceiptItem → `acquisition_receipt_item`

Truy vết: F22. Quy tắc: quantity>0; unit_price>=0; total=quantity×unit_price; source FK BookCopy chỉ có khi triển khai F22.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| receipt_id | uuid | Không | FK AcquisitionReceipt.id | Phiếu nhập |
| edition_id | uuid | Không | FK BookEdition.id | Ấn bản |
| quantity | integer | Không | >0 | Số cuốn |
| unit_price | numeric(14,0) | Không | >=0 | Giá VND snapshot |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

### 38. BackupManifest → `backup_manifest`

Truy vết: F23. Quy tắc: Metadata backup không phải file backup; không chứa khóa giải mã; restore drill ghi bằng chứng.

| Cột | Kiểu PostgreSQL | NULL | Ràng buộc/default nguồn | Ý nghĩa |
| --- | --- | --- | --- | --- |
| id | uuid | Không | PK | Định danh bất biến |
| schema_version | varchar(64) | Không | — | Version migration |
| snapshot_at | timestamptz | Không | — | Mốc dữ liệu |
| encrypted_object_key | text | Không | UQ | Vị trí backup mã hóa |
| sha256 | char(64) | Không | — | Hash |
| verified_at | timestamptz | Có | — | Ngày kiểm chứng |
| restore_drill_result | jsonb | Có | — | Kết quả RPO/RTO và toàn vẹn |
| created_by | uuid | Có | FK Account.id | Người/worker tạo |
| created_at | timestamptz | Không | DEFAULT now() | Thời điểm ghi nhận |

## Ràng buộc và index triển khai

- Partial unique loan_item(copy_id) WHERE closed_at IS NULL; UNIQUE return_event(loan_item_id).
- Partial unique reservation(reader_id,edition_id) WHERE status IN (QUEUED,READY); partial unique reservation(copy_id) WHERE status=READY. Guard READY yêu cầu copy_id/ready_at/ready_expires_at không NULL và copy ở HELD.
- ISBN chuẩn hóa trước ghi, unique khi có; barcode unique toàn thư viện. Category cycle cần service/transaction, không chỉ FK tự tham chiếu.
- Index loan_item(due_at,id) WHERE closed_at IS NULL; reservation(edition_id,created_at,id) WHERE status=QUEUED; ledger theo reader/charge; job(status,next_attempt_at,lease_until); audit_log(target_type,target_id,created_at).
- PolicyVersion không chồng hiệu lực; dùng exclusion constraint khi range đã chuẩn hóa hoặc khóa khi duyệt. Rule lịch sử và policy snapshot bất biến.
- Không tạo CHECK dựa now() cho eligibility/năm xuất bản; kiểm tra tại transaction nghiệp vụ. Không persist balance/count/overdue như nguồn chân lý.

## Schema bổ sung ngoài danh mục 38 bảng

| Bảng | Cột và ràng buộc đề xuất | Sở hữu |
| --- | --- | --- |
| charge_assessment | id UUID PK; reader_id FK Reader NN; return_event_id FK ReturnEvent NN; kind DAMAGE/LOST NN; proposed_amount numeric(14,0) >=0 NN; reason text NN; proposed_by FK Account NN; status PENDING/ASSESSED/CLOSED_NO_CHARGE NN; approved_amount numeric(14,0) nullable; decided_by FK Account nullable; decided_at timestamptz nullable; decision_reason text nullable; fine_charge_id FK FineCharge nullable UQ; version integer >0 DEFAULT1; created_at timestamptz DEFAULT now(); UQ return_event_id+kind | Finance |
| notification | id UUID PK; event_id FK OutboxEvent nullable; reader_id FK Reader NN; kind READY/OVERDUE NN; reservation_id FK Reservation nullable; summary text NN; read_at timestamptz nullable; dedupe_key varchar(200) UQ NN; created_at timestamptz DEFAULT now() | Notifications |
| notification_delivery | id UUID PK; notification_id FK notification NN; channel EMAIL NN; status QUEUED/SENDING/DELIVERED/FAILED/SKIPPED NN; job_id FK Job NN; provider_message_id text nullable; delivered_at timestamptz nullable; last_error_code text nullable; UQ notification_id+channel | Notifications |
| notification_preference | reader_id UUID PK/FK Reader; email_consent boolean DEFAULTfalse; changed_by FK Account NN; updated_at timestamptz DEFAULT now() | Readers/consent |

Các bổ sung trên là thiết kế mới, chưa có trong DOCX 38 bảng. Consent được lưu riêng để không đổi nghĩa trường email Reader; email tồn tại không đồng nghĩa đồng ý nhận nhắc.

## Giao dịch, migration và dữ liệu mẫu

Một Unit of Work/Session cho toàn giao dịch. Khóa theo BookEdition→Reader→BookCopy→Loan/Item→Reservation→Charge/Payment, ID tăng dần mỗi nhóm; các lệnh độc lập bỏ qua nhóm không dùng nhưng không đảo thứ tự. Return phải đọc định danh trước rồi lấy khóa theo thứ tự; retry toàn transaction khi deadlock giới hạn.

Migration chia identity/policy→catalog/readers→circulation/finance→operations/extensions→schema bổ sung. Kiểm tra FK/duplicateOPEN trước bật unique; seed dữ liệu demo riêng, không tự seed vào production. Nếu dữ liệu cũ thiếu dueAt/provenance thì đưa vào danh sách cần xử lý, không đoán.

Không tự thêm Disposition/ledger mới vào 38 bảng: thanh lý dùng command+AuditLog, nếu cần chứng từ riêng phải được đặc tả bổ sung. Duyệt phí cần khóa Reader để checkout/renew/hold và assessment không race.

## Nghiệm thu thiết kế

Đối chiếu 38 bảng/288 trường với source-data-dictionary.json; mỗi cột có kiểu/NULL/constraint. Đối chiếu schema bổ sung với [assessment](charge-assessment.md), [events](event-job-contracts.md) và API. Migration/code sẽ được kiểm thử khi triển khai; việc trích xuất thành công không chứng minh DB đã tồn tại.

### Điểm mở N05 và bất biến bổ sung

AcquisitionReceipt.status nguồn là DRAFT/POSTED/CANCELLED. APPROVED trong kế hoạch/UML là extension chưa chốt; chưa thêm enum vào danh mục gốc. Cần chọn duyệt và post cùng command hoặc bổ sung APPROVED trước triển khai F22. Người giao BM01 chưa có cột nguồn.

ChargeAssessment ASSESSED bắt buộc approved_amount>0, decided_by/decided_at/decision_reason và fine_charge_id; CLOSED_NO_CHARGE bắt buộc approved_amount=0, thông tin quyết định và fine_charge_id NULL. PENDING chưa có quyết định/charge. Notification kind READY cần reservation_id; OVERDUE không cần; lease/retry qua Job.
