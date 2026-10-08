# Từ điển dữ liệu hiện hành — 08/10/2026

Nguồn: Google Docs báo cáo hiện hành, mục 13.4. Có **39 bảng / 303 trường** = 38 bảng gốc / 288 trường + ChargeAssessment / 15 trường. Ba bảng Notification, NotificationDelivery và NotificationPreference là extension đặc tả riêng trong database-design.md; không tính vào 39/303. Schema thiết kế gồm 42 bảng, chưa có migration nghiệp vụ.

Not NULL Có = bắt buộc tại DB; Không = cho phép NULL nhưng có thể bắt buộc theo trạng thái. Chưa chốt = nguồn chưa quy định. Độ rộng varchar là số ký tự tối đa; numeric là precision,scale; — là không khai báo tham số độ rộng, không phải 0. Chuỗi chưa chốt không xác định varchar/text/enum. API required không tự quyết định DB NOT NULL.

## Danh mục

| STT | Lớp / bảng logic | Bảng vật lý | Số trường |
| --- | --- | --- | --- |
| 1 | Publisher | publisher | 5 |
| 2 | Author | author | 5 |
| 3 | Category | category | 6 |
| 4 | BookEdition | book_edition | 10 |
| 5 | BookAuthor | book_author | 4 |
| 6 | BookCategory | book_category | 3 |
| 7 | Location | location | 5 |
| 8 | BookCopy | book_copy | 9 |
| 9 | MediaAsset | media_asset | 10 |
| 10 | Reader | reader | 11 |
| 11 | ReaderCard | reader_card | 10 |
| 12 | Account | account | 8 |
| 13 | Role | role | 4 |
| 14 | Permission | permission | 4 |
| 15 | AccountRole | account_role | 4 |
| 16 | RolePermission | role_permission | 3 |
| 17 | PolicyVersion | policy_version | 10 |
| 18 | Loan | loan | 9 |
| 19 | LoanItem | loan_item | 11 |
| 20 | RenewalEvent | renewal_event | 8 |
| 21 | RenewalItem | renewal_item | 6 |
| 22 | ReturnEvent | return_event | 8 |
| 23 | Reservation | reservation | 13 |
| 24 | FineCharge | fine_charge | 12 |
| 25 | Payment | payment | 9 |
| 26 | PaymentAllocation | payment_allocation | 4 |
| 27 | Waiver | waiver | 6 |
| 28 | PaymentReversal | payment_reversal | 6 |
| 29 | AllocationReversal | allocation_reversal | 7 |
| 30 | WaiverReversal | waiver_reversal | 6 |
| 31 | IdempotencyRecord | idempotency_record | 10 |
| 32 | OutboxEvent | outbox_event | 7 |
| 33 | Job | job | 12 |
| 34 | ReportJob | report_job | 10 |
| 35 | AuditLog | audit_log | 11 |
| 36 | AcquisitionReceipt | acquisition_receipt | 7 |
| 37 | AcquisitionReceiptItem | acquisition_receipt_item | 6 |
| 38 | BackupManifest | backup_manifest | 9 |
| 39 | ChargeAssessment | charge_assessment | 15 |

## 1. Publisher — Nhà xuất bản

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | name | varchar | 200 | Có | CHECK không rỗng | Tên nhà xuất bản |
| 3 | address | text | — | Không | — | Địa chỉ liên hệ |
| 4 | status | varchar | 16 | Có | ACTIVE/INACTIVE | Trạng thái danh mục |
| 5 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 2. Author — Tác giả

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | name | varchar | 200 | Có | CHECK không rỗng | Tên tác giả |
| 3 | biography | text | — | Không | — | Giới thiệu |
| 4 | status | varchar | 16 | Có | ACTIVE/INACTIVE | Trạng thái |
| 5 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 3. Category — Thể loại

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | code | varchar | 32 | Có | UQ | Mã thể loại |
| 3 | name | varchar | 120 | Có | — | Tên thể loại |
| 4 | parent_id | uuid | — | Không | FK Category.id | Thể loại cha |
| 5 | is_root | boolean | — | Có | DEFAULT false | Cờ gốc được bảo vệ |
| 6 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 4. BookEdition — Ấn bản sách

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | isbn | varchar | 13 | Không | UQ | ISBN chuẩn hóa |
| 3 | title | varchar | 300 | Có | CHECK không rỗng | Nhan đề |
| 4 | publication_year | smallint | — | Có | — | Năm xuất bản |
| 5 | publisher_id | uuid | — | Không | FK Publisher.id | Nhà xuất bản |
| 6 | language | varchar | 32 | Không | — | Ngôn ngữ |
| 7 | description | text | — | Không | — | Mô tả nội dung |
| 8 | status | varchar | 16 | Có | ACTIVE/INACTIVE | Trạng thái |
| 9 | version | integer | — | Có | DEFAULT 1; >0 | Phiên bản cập nhật |
| 10 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 5. BookAuthor — Tác giả của ấn bản

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | edition_id | uuid | — | Có | PK ghép; FK BookEdition.id | Ấn bản |
| 2 | author_id | uuid | — | Có | PK ghép; FK Author.id | Tác giả |
| 3 | ordinal | smallint | — | Có | >0; UQ edition_id+ordinal | Thứ tự trình bày |
| 4 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 6. BookCategory — Thể loại của ấn bản

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | edition_id | uuid | — | Có | PK ghép; FK BookEdition.id | Ấn bản |
| 2 | category_id | uuid | — | Có | PK ghép; FK Category.id | Thể loại |
| 3 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 7. Location — Vị trí kho

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | code | varchar | 32 | Có | UQ | Mã kệ/vị trí |
| 3 | name | varchar | 120 | Có | — | Tên vị trí |
| 4 | status | varchar | 16 | Có | ACTIVE/INACTIVE | Khả dụng |
| 5 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 8. BookCopy — Bản sao vật lý

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | edition_id | uuid | — | Có | FK BookEdition.id | Ấn bản |
| 3 | barcode | varchar | 64 | Có | UQ | Mã vạch |
| 4 | location_id | uuid | — | Không | FK Location.id | Vị trí hiện tại |
| 5 | status | varchar | 16 | Có | AVAILABLE/ON_LOAN/HELD/REPAIR/LOST/RETIRED | Trạng thái vật lý |
| 6 | acquired_at | timestamptz | — | Có | — | Ngày tiếp nhận |
| 7 | source_receipt_item_id | uuid | — | Không | FK AcquisitionReceiptItem.id (mở rộng) | Dòng nhập nguồn |
| 8 | version | integer | — | Có | DEFAULT 1; >0 | Phiên bản |
| 9 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 9. MediaAsset — Tệp và ảnh bìa

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | edition_id | uuid | — | Không | FK BookEdition.id | Ấn bản nếu là bìa |
| 3 | object_key | text | — | Có | UQ | Khóa object storage |
| 4 | mime_type | varchar | 100 | Có | — | MIME đã kiểm tra |
| 5 | byte_size | bigint | — | Có | >0 | Dung lượng |
| 6 | sha256 | char | 64 | Có | — | Hash nội dung |
| 7 | visibility | varchar | 16 | Có | PUBLIC/PRIVATE | Phạm vi tải |
| 8 | status | varchar | 16 | Có | PENDING/READY/REJECTED/DELETED | Vòng đời tệp |
| 9 | uploaded_by | uuid | — | Có | FK Account.id | Người tải |
| 10 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 10. Reader — Độc giả

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | reader_code | varchar | 32 | Có | UQ | Mã độc giả |
| 3 | full_name | varchar | 200 | Có | — | Họ tên |
| 4 | birth_date | date | — | Có | — | Ngày sinh, tuổi tính khi cấp thẻ |
| 5 | reader_type | varchar | 8 | Có | X/Y/Z dự thảo | Loại độc giả |
| 6 | email | varchar | 254 | Không | — | Email liên hệ |
| 7 | phone | varchar | 32 | Không | — | Điện thoại |
| 8 | address | text | — | Không | — | Địa chỉ |
| 9 | status | varchar | 16 | Có | ACTIVE/SUSPENDED/INACTIVE | Trạng thái |
| 10 | version | integer | — | Có | DEFAULT 1 | Phiên bản |
| 11 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 11. ReaderCard — Thẻ thư viện

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | reader_id | uuid | — | Có | FK Reader.id | Chủ thẻ |
| 3 | card_no | varchar | 64 | Có | UQ | Số thẻ |
| 4 | issued_at | timestamptz | — | Có | — | Thời điểm cấp |
| 5 | expires_at | timestamptz | — | Có | — | Hết hiệu lực |
| 6 | status | varchar | 16 | Có | ACTIVE/BLOCKED/REVOKED | Trạng thái; hết hạn tính từ thời gian |
| 7 | issued_by | uuid | — | Có | FK Account.id | Người cấp |
| 8 | policy_version_id | uuid | — | Có | FK PolicyVersion.id | Quy định cấp thẻ |
| 9 | version | integer | — | Có | DEFAULT 1 | Phiên bản |
| 10 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 12. Account — Tài khoản

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | issuer | text | — | Có | — | Nhà phát hành định danh |
| 3 | subject | text | — | Có | UQ ghép issuer+subject | Định danh bên IdP |
| 4 | reader_id | uuid | — | Không | FK Reader.id; UQ | Ánh xạ độc giả |
| 5 | display_name | varchar | 200 | Có | — | Tên hiển thị |
| 6 | status | varchar | 16 | Có | ACTIVE/LOCKED/DISABLED | Trạng thái |
| 7 | auth_version | integer | — | Có | DEFAULT 1 | Vô hiệu cache quyền ứng dụng; thu hồi phiên/JWT Keycloak là thao tác riêng |
| 8 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 13. Role — Vai trò

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | code | varchar | 64 | Có | UQ | Mã vai trò |
| 3 | name | varchar | 120 | Có | — | Tên vai trò |
| 4 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 14. Permission — Quyền

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | code | varchar | 100 | Có | UQ | Mã quyền |
| 3 | description | text | — | Có | — | Ý nghĩa quyền |
| 4 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 15. AccountRole — Gán vai trò

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | account_id | uuid | — | Có | PK ghép; FK Account.id | Tài khoản |
| 2 | role_id | uuid | — | Có | PK ghép; FK Role.id | Vai trò |
| 3 | granted_by | uuid | — | Có | FK Account.id | Người cấp |
| 4 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 16. RolePermission — Quyền của vai trò

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | role_id | uuid | — | Có | PK ghép; FK Role.id | Vai trò |
| 2 | permission_id | uuid | — | Có | PK ghép; FK Permission.id | Quyền |
| 3 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 17. PolicyVersion — Phiên bản quy định

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | version_no | integer | — | Có | UQ; >0 | Số phiên bản |
| 3 | effective_from | timestamptz | — | Có | — | Bắt đầu hiệu lực |
| 4 | effective_to | timestamptz | — | Không | — | Kết thúc độc quyền |
| 5 | status | varchar | 16 | Có | DRAFT/ACTIVE/SUPERSEDED | Trạng thái |
| 6 | rules | jsonb | — | Có | Schema validation | Hạn mức, tuổi, phí, thời hạn |
| 7 | rules_schema_version | integer | — | Có | >0 | Phiên bản schema JSON |
| 8 | approved_by | uuid | — | Không | FK Account.id | Bắt buộc khi ACTIVE |
| 9 | approved_at | timestamptz | — | Không | — | Thời điểm duyệt |
| 10 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 18. Loan — Phiếu mượn

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | loan_no | varchar | 64 | Có | UQ | Số phiếu |
| 3 | reader_id | uuid | — | Có | FK Reader.id | Độc giả |
| 4 | card_id | uuid | — | Có | FK ReaderCard.id | Thẻ đã dùng |
| 5 | issued_by | uuid | — | Có | FK Account.id | Thủ thư |
| 6 | issued_at | timestamptz | — | Có | — | Ngày mượn |
| 7 | renewal_count | integer | — | Có | >=0; DEFAULT 0 | Số lần gia hạn phiếu |
| 8 | version | integer | — | Có | DEFAULT 1 | Phiên bản |
| 9 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 19. LoanItem — Chi tiết mượn

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | loan_id | uuid | — | Có | FK Loan.id | Phiếu mượn |
| 3 | copy_id | uuid | — | Có | FK BookCopy.id | Bản sao |
| 4 | issued_at | timestamptz | — | Có | — | Bắt đầu mượn |
| 5 | due_at | timestamptz | — | Có | — | Hạn trả hiện hành |
| 6 | closed_at | timestamptz | — | Không | — | Đóng mục |
| 7 | closure_reason | varchar | 16 | Không | RETURNED/LOST/VOIDED | Lý do đóng |
| 8 | policy_version_id | uuid | — | Có | FK PolicyVersion.id | Policy ban đầu |
| 9 | applied_rules | jsonb | — | Có | — | Snapshot quy tắc ban đầu |
| 10 | version | integer | — | Có | DEFAULT 1 | Phiên bản |
| 11 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 20. RenewalEvent — Lần gia hạn phiếu

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | loan_id | uuid | — | Có | FK Loan.id | Phiếu gia hạn |
| 3 | sequence_no | integer | — | Có | >0 | Thứ tự gia hạn |
| 4 | actor_id | uuid | — | Có | FK Account.id | Người thực hiện |
| 5 | renewed_at | timestamptz | — | Có | — | Thời điểm |
| 6 | policy_version_id | uuid | — | Có | FK PolicyVersion.id | Policy quyết định gia hạn |
| 7 | request_id | varchar | 100 | Có | — | Mã tương quan yêu cầu |
| 8 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 21. RenewalItem — Hạn trước sau gia hạn

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | renewal_event_id | uuid | — | Có | PK ghép; FK RenewalEvent.id | Lần gia hạn |
| 2 | loan_item_id | uuid | — | Có | PK ghép; FK LoanItem.id | Mục mượn |
| 3 | old_due_at | timestamptz | — | Có | — | Hạn trước |
| 4 | new_due_at | timestamptz | — | Có | — | Hạn sau |
| 5 | applied_rules | jsonb | — | Có | — | Quy tắc gia hạn đã dùng |
| 6 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 22. ReturnEvent — Sự kiện đóng mục mượn

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | loan_item_id | uuid | — | Có | FK LoanItem.id; UQ | Mục được đóng |
| 3 | return_kind | varchar | 16 | Có | RETURNED/LOST/VOIDED | Kiểu xử lý |
| 4 | condition | varchar | 16 | Không | GOOD/DAMAGED | Tình trạng khi nhận |
| 5 | returned_at | timestamptz | — | Có | — | Thời điểm xử lý trả/mất |
| 6 | processed_by | uuid | — | Có | FK Account.id | Người xử lý |
| 7 | notes | text | — | Không | — | Biên bản/lý do |
| 8 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 23. Reservation — Đặt trước

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | reader_id | uuid | — | Có | FK Reader.id | Độc giả |
| 3 | edition_id | uuid | — | Có | FK BookEdition.id | Ấn bản xếp hàng |
| 4 | copy_id | uuid | — | Không | FK BookCopy.id | Copy phân bổ khi READY |
| 5 | fulfilled_loan_item_id | uuid | — | Không | FK LoanItem.id; UQ | Mục đã nhận |
| 6 | status | varchar | 16 | Có | QUEUED/READY/FULFILLED/CANCELLED/EXPIRED | Trạng thái |
| 7 | ready_at | timestamptz | — | Không | — | Bắt đầu giữ |
| 8 | ready_expires_at | timestamptz | — | Không | — | Hạn nhận |
| 9 | cancellation_reason | text | — | Không | — | Lý do hủy |
| 10 | policy_version_id | uuid | — | Có | FK PolicyVersion.id | Policy đặt chỗ |
| 11 | applied_rules | jsonb | — | Có | — | Snapshot; hạn READY chốt khi phân bổ |
| 12 | version | integer | — | Có | DEFAULT 1 | Phiên bản |
| 13 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 24. FineCharge — Khoản phí phạt

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | reader_id | uuid | — | Có | FK Reader.id | Người chịu phí |
| 3 | loan_item_id | uuid | — | Không | FK LoanItem.id | Mục gây phí |
| 4 | policy_version_id | uuid | — | Có | FK PolicyVersion.id | Policy tính phí |
| 5 | reason | varchar | 16 | Có | LATE/DAMAGE/LOST/MANUAL | Loại phí |
| 6 | assessed_amount | numeric | 14,0 | Có | >0 | Số tiền phát sinh VND |
| 7 | late_days | integer | — | Không | >=0 | Ngày trễ snapshot theo C08 |
| 8 | unit_rate | numeric | 14,0 | Không | >=0 | Đơn giá snapshot |
| 9 | calculation | jsonb | — | Có | — | Công thức và dữ liệu tính |
| 10 | manual_reason | text | — | Không | — | Lý do thủ công |
| 11 | assessed_by | uuid | — | Có | FK Account.id | Người ghi phí |
| 12 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 25. Payment — Chứng từ thu

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | reader_id | uuid | — | Có | FK Reader.id | Người nộp |
| 3 | receipt_no | varchar | 64 | Có | UQ | Số biên nhận |
| 4 | amount | numeric | 14,0 | Có | >0 | Tiền thu VND |
| 5 | method | varchar | 24 | Có | CASH/TRANSFER_RECORD | Phương thức ghi nhận |
| 6 | received_at | timestamptz | — | Có | — | Ngày thu |
| 7 | received_by | uuid | — | Có | FK Account.id | Người thu |
| 8 | reference | text | — | Không | — | Tham chiếu chuyển khoản |
| 9 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 26. PaymentAllocation — Phân bổ tiền thu

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | payment_id | uuid | — | Có | PK ghép; FK Payment.id | Chứng từ thu |
| 2 | charge_id | uuid | — | Có | PK ghép; FK FineCharge.id | Khoản phí |
| 3 | amount | numeric | 14,0 | Có | >0 | Số tiền phân bổ VND |
| 4 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 27. Waiver — Miễn giảm

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | charge_id | uuid | — | Có | FK FineCharge.id | Khoản phí |
| 3 | amount | numeric | 14,0 | Có | >0 | Tiền miễn VND |
| 4 | approved_by | uuid | — | Có | FK Account.id | Người duyệt |
| 5 | reason | text | — | Có | Không rỗng | Lý do |
| 6 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 28. PaymentReversal — Đảo chứng từ thu

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | payment_id | uuid | — | Có | FK Payment.id | Chứng từ gốc |
| 3 | amount | numeric | 14,0 | Có | >0 | Tiền đảo VND |
| 4 | actor_id | uuid | — | Có | FK Account.id | Người duyệt |
| 5 | reason | text | — | Có | — | Lý do |
| 6 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 29. AllocationReversal — Đảo phân bổ

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | payment_id | uuid | — | Có | FK ghép PaymentAllocation.payment_id | Chứng từ gốc |
| 3 | charge_id | uuid | — | Có | FK ghép PaymentAllocation.charge_id | Khoản phí gốc |
| 4 | amount | numeric | 14,0 | Có | >0 | Tiền đảo VND |
| 5 | actor_id | uuid | — | Có | FK Account.id | Người duyệt |
| 6 | reason | text | — | Có | — | Lý do |
| 7 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 30. WaiverReversal — Đảo miễn giảm

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | waiver_id | uuid | — | Có | FK Waiver.id | Miễn giảm gốc |
| 3 | amount | numeric | 14,0 | Có | >0 | Tiền đảo VND |
| 4 | actor_id | uuid | — | Có | FK Account.id | Người duyệt |
| 5 | reason | text | — | Có | — | Lý do |
| 6 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 31. IdempotencyRecord — Chống giao dịch trùng

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | actor_id | uuid | — | Có | FK Account.id | Chủ yêu cầu |
| 3 | operation | varchar | 64 | Có | — | Loại lệnh |
| 4 | key | varchar | 128 | Có | — | Khóa retry |
| 5 | payload_hash | char | 64 | Có | — | Hash payload chuẩn hóa |
| 6 | response_status | smallint | — | Không | — | HTTP status sau hoàn tất |
| 7 | response_body | jsonb | — | Không | — | Kết quả đã redaction |
| 8 | state | varchar | 16 | Có | PENDING/COMPLETED | Trạng thái |
| 9 | expires_at | timestamptz | — | Có | — | Hạn giữ |
| 10 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 32. OutboxEvent — Sự kiện sau commit

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | aggregate_type | varchar | 64 | Có | — | Loại aggregate |
| 3 | aggregate_id | uuid | — | Có | — | Tham chiếu logic, không FK đa hình |
| 4 | event_type | varchar | 100 | Có | — | Loại sự kiện |
| 5 | payload | jsonb | — | Có | — | Dữ liệu tối thiểu đã redaction |
| 6 | processed_at | timestamptz | — | Không | — | Đã hoàn tất dispatch |
| 7 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 33. Job — Tác vụ nền

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | outbox_event_id | uuid | — | Không | FK OutboxEvent.id | Nguồn event |
| 3 | dedupe_key | varchar | 200 | Có | UQ | Khóa chống tạo trùng |
| 4 | job_type | varchar | 64 | Có | — | Loại tác vụ |
| 5 | payload | jsonb | — | Có | — | Dữ liệu handler |
| 6 | status | varchar | 16 | Có | QUEUED/RUNNING/SUCCEEDED/FAILED/DEAD | Trạng thái |
| 7 | attempt | integer | — | Có | >=0; DEFAULT 0 | Lần thử |
| 8 | lease_owner | varchar | 100 | Không | — | Worker nhận |
| 9 | lease_until | timestamptz | — | Không | — | Hạn lease |
| 10 | next_attempt_at | timestamptz | — | Không | — | Lịch thử lại |
| 11 | last_error_code | varchar | 100 | Không | — | Lỗi không chứa secret |
| 12 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 34. ReportJob — Báo cáo và xuất dữ liệu

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | job_id | uuid | — | Có | FK Job.id; UQ | Tác vụ thực thi |
| 3 | requested_by | uuid | — | Có | FK Account.id | Người yêu cầu |
| 4 | report_type | varchar | 64 | Có | — | Loại báo cáo |
| 5 | filter_snapshot | jsonb | — | Có | — | Bộ lọc và scope đã kiểm quyền |
| 6 | as_of | timestamptz | — | Có | — | Mốc snapshot báo cáo |
| 7 | artifact_id | uuid | — | Không | FK MediaAsset.id | Tệp riêng tư |
| 8 | expires_at | timestamptz | — | Không | — | Hạn tải |
| 9 | row_count | bigint | — | Không | >=0 | Số dòng xuất |
| 10 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 35. AuditLog — Nhật ký kiểm toán

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | actor_id | uuid | — | Không | FK Account.id | Người thao tác |
| 3 | actor_type | varchar | 16 | Có | USER/SYSTEM/ANONYMOUS | Loại chủ thể |
| 4 | action | varchar | 100 | Có | — | Hành động |
| 5 | permission_code | varchar | 100 | Không | — | Quyền đã kiểm |
| 6 | target_type | varchar | 64 | Có | — | Loại đối tượng |
| 7 | target_id | uuid | — | Không | — | ID logic, không FK đa hình |
| 8 | request_id | varchar | 100 | Có | — | Tương quan |
| 9 | outcome | varchar | 16 | Có | SUCCESS/DENIED/FAILED | Kết quả |
| 10 | metadata | jsonb | — | Có | — | Before/after đã redaction |
| 11 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 36. AcquisitionReceipt — Phiếu tiếp nhận *

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | receipt_no | varchar | 64 | Có | UQ | Số phiếu |
| 3 | supplier | varchar | 200 | Có | — | Nhà cung cấp |
| 4 | received_at | timestamptz | — | Có | — | Ngày nhận |
| 5 | status | varchar | 16 | Có | DRAFT/POSTED/CANCELLED | Trạng thái |
| 6 | approved_by | uuid | — | Không | FK Account.id | Bắt buộc khi POSTED |
| 7 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 37. AcquisitionReceiptItem — Chi tiết tiếp nhận *

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | receipt_id | uuid | — | Có | FK AcquisitionReceipt.id | Phiếu nhập |
| 3 | edition_id | uuid | — | Có | FK BookEdition.id | Ấn bản |
| 4 | quantity | integer | — | Có | >0 | Số cuốn |
| 5 | unit_price | numeric | 14,0 | Có | >=0 | Giá VND snapshot |
| 6 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 38. BackupManifest — Hồ sơ sao lưu *

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh bất biến |
| 2 | schema_version | varchar | 64 | Có | — | Version migration |
| 3 | snapshot_at | timestamptz | — | Có | — | Mốc dữ liệu |
| 4 | encrypted_object_key | text | — | Có | UQ | Vị trí backup mã hóa |
| 5 | sha256 | char | 64 | Có | — | Hash |
| 6 | verified_at | timestamptz | — | Không | — | Ngày kiểm chứng |
| 7 | restore_drill_result | jsonb | — | Không | — | Kết quả RPO/RTO và toàn vẹn |
| 8 | created_by | uuid | — | Không | FK Account.id | Người/worker tạo |
| 9 | created_at | timestamptz | — | Có | DEFAULT now() | Thời điểm ghi nhận |

## 39. ChargeAssessment — Hồ sơ đề xuất và quyết định phí

| TT | Tên thuộc tính (Field name) | Kiểu dữ liệu | Độ rộng | Not NULL | Ràng buộc / Miền giá trị | Diễn giải |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | id | uuid | — | Có | PK | Định danh hồ sơ đề xuất phí. |
| 2 | reader_id | uuid | — | Có | FK Reader.id; khớp độc giả của Loan | Độc giả liên quan; máy chủ xác định. |
| 3 | return_event_id | uuid | — | Có | FK ReturnEvent.id; UQ ghép với kind | Sự kiện trả/ghi nhận mất làm căn cứ. |
| 4 | kind | Chuỗi | Chưa chốt | Có | DAMAGE / LOST; UQ(return_event_id, kind) | Loại đề xuất phí hỏng/mất. |
| 5 | proposed_amount | numeric | 14,0 | Có | ≥ 0; chưa tính vào dư nợ | Số tiền Thủ thư đề xuất, VND. |
| 6 | reason | text | — | Có | Lý do bắt buộc | Căn cứ đề xuất mức phí. |
| 7 | proposed_by | uuid | — | Có | FK Account.id; lấy từ phiên | Thủ thư lập đề xuất. |
| 8 | status | Chuỗi | Chưa chốt | Có | PENDING / ASSESSED / CLOSED_NO_CHARGE | Trạng thái xử lý hồ sơ. |
| 9 | approved_amount | numeric | 14,0 | Không | PENDING: NULL; ASSESSED: > 0; CLOSED_NO_CHARGE: 0 | Mức phí Quản lý quyết định. |
| 10 | decided_by | uuid | — | Không | FK Account.id; bắt buộc khi kết thúc | Quản lý ra quyết định. |
| 11 | decided_at | timestamptz | — | Không | Bắt buộc khi kết thúc; máy chủ ghi | Thời điểm quyết định. |
| 12 | decision_reason | text | — | Không | Bắt buộc khi kết thúc | Lý do duyệt hoặc không thu phí. |
| 13 | fine_charge_id | uuid | — | Không | FK FineCharge.id; UQ; chỉ có khi ASSESSED | Khoản phí tạo trong cùng giao dịch. |
| 14 | version | integer | — | Chưa chốt | > 0; DEFAULT 1; nguồn chưa ghi NN | Phiên bản kiểm soát cập nhật đồng thời. |
| 15 | created_at | timestamptz | — | Chưa chốt | DEFAULT now(); nguồn chưa ghi NN | Thời điểm tạo hồ sơ. |

## Quyết định schema còn thiếu

- D01: SQL type/độ rộng cho ChargeAssessment.kind và status; NOT NULL cho version và created_at. Chủ dự án chưa chốt; không tự gán trong migration. DEFAULT không tự suy ra NOT NULL.
- Các bất biến PENDING/ASSESSED/CLOSED_NO_CHARGE và quan hệ liên bảng theo database-design.md/charge-assessment.md vẫn áp dụng.
- N03–N07 tiếp tục mở. Ba notification extensions cần hoàn thiện kiểu/NULL/ràng buộc trước migration tương ứng; không đổi scope F24.
