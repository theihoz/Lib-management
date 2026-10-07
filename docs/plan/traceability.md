# Ma trận truy vết F01–F24

Mã chức năng/use case lấy từ DOCX chính; task là planned, không phải đã triển khai. Dữ liệu/API và tiêu chí chi tiết nằm trong file module. INT00 áp dụng mọi chức năng.

| F | UC | Chức năng | Backend | Frontend | Nghiệm thu tích hợp |
| --- | --- | --- | --- | --- | --- |
| F01 | UC1 | Ấn bản | [BE03](backend/BE03-catalog.md) | [FE02](frontend/FE02-catalog.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F02 | UC2 | Bản sao/barcode | [BE03](backend/BE03-catalog.md) | [FE02](frontend/FE02-catalog.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F03 | UC3 | Thể loại | [BE03](backend/BE03-catalog.md) | [FE02](frontend/FE02-catalog.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F04 | UC1.1 | Tác giả | [BE03](backend/BE03-catalog.md) | [FE02](frontend/FE02-catalog.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F05 | UC1.2 | Nhà xuất bản | [BE03](backend/BE03-catalog.md) | [FE02](frontend/FE02-catalog.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F06 | UC5 | Độc giả/thẻ | [BE04](backend/BE04-readers.md) | [FE03](frontend/FE03-readers-cards.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F07 | UC6 | Cho mượn | [BE06](backend/BE06-checkout.md) | [FE04](frontend/FE04-checkout.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F08 | UC7 | Nhận trả | [BE07](backend/BE07-returns.md) | [FE05](frontend/FE05-returns.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F09 | UC8 | Gia hạn | [BE08](backend/BE08-reservations-renewals.md) | [FE06](frontend/FE06-reservations-renewals.md) | [INT02](integration/INT02-extended-workflows.md) |
| F10 | UC9 | Giữ chỗ | [BE08](backend/BE08-reservations-renewals.md) | [FE06](frontend/FE06-reservations-renewals.md), [FE08](frontend/FE08-reader-portal.md) | [INT02](integration/INT02-extended-workflows.md) |
| F11 | UC10/UC22 | Phí/thu/miễn/đảo | [BE05](backend/BE05-finance.md) | [FE07](frontend/FE07-finance.md) | [INT02](integration/INT02-extended-workflows.md) |
| F12 | UC11 | Điều kiện độc giả | [BE04](backend/BE04-readers.md) | [FE03](frontend/FE03-readers-cards.md), [FE04](frontend/FE04-checkout.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F13 | UC16 | Báo cáo | [BE10](backend/BE10-reporting-exports.md) | [FE09](frontend/FE09-reports-policy.md) | [INT02](integration/INT02-extended-workflows.md) |
| F14 | UC17 | Quy định | [BE02](backend/BE02-policy.md) | [FE09](frontend/FE09-reports-policy.md) | [INT02](integration/INT02-extended-workflows.md) |
| F15 | UC4 | Ảnh bìa | [BE11](backend/BE11-media.md) | [FE02](frontend/FE02-catalog.md) | [INT02](integration/INT02-extended-workflows.md) |
| F16 | UC0 | Đăng nhập | [BE01](backend/BE01-identity.md) | [FE01](frontend/FE01-auth-navigation.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F17 | UC13 | Lịch sử | [BE09](backend/BE09-history-search-overdue.md) | [FE08](frontend/FE08-reader-portal.md) | [INT02](integration/INT02-extended-workflows.md) |
| F18 | UC12 | Tìm kiếm | [BE03](backend/BE03-catalog.md), [BE09](backend/BE09-history-search-overdue.md) | [FE02](frontend/FE02-catalog.md), [FE03](frontend/FE03-readers-cards.md) | [INT01](integration/INT01-first-library-workflow.md) |
| F19 | UC14 | Quá hạn | [BE09](backend/BE09-history-search-overdue.md) | [FE09](frontend/FE09-reports-policy.md), [FE08](frontend/FE08-reader-portal.md) | [INT02](integration/INT02-extended-workflows.md) |
| F20 | UC15 | CSV | [BE10](backend/BE10-reporting-exports.md) | [FE09](frontend/FE09-reports-policy.md) | [INT02](integration/INT02-extended-workflows.md) |
| F21 | UC18 | Quản trị tài khoản | [BE01](backend/BE01-identity.md) | [FE10](frontend/FE10-administration-inventory.md) | [INT02](integration/INT02-extended-workflows.md) |
| F22 | UC19 | Nhập/thanh lý | [BE12](backend/BE12-acquisitions-disposal.md) | [FE10](frontend/FE10-administration-inventory.md) | [INT02](integration/INT02-extended-workflows.md) |
| F23 | UC20 | Backup/restore | [BE14](backend/BE14-backup-restore.md) | [FE11](frontend/FE11-operations.md) | [INT02](integration/INT02-extended-workflows.md) |
| F24 | UC21 | Thông báo | [BE13](backend/BE13-notifications.md) | [FE08](frontend/FE08-reader-portal.md), [FE11](frontend/FE11-operations.md) | [INT02](integration/INT02-extended-workflows.md) |

## Quyền và sở hữu

- Độc giả: catalog công khai; chỉ holds/history/notifications của mình sau đăng nhập.
- Thủ thư: danh mục, độc giả/thẻ, lưu thông, thu tiền và đề xuất phí theo permission.
- Quản lý: duyệt phí, miễn/đảo, báo cáo/CSV, quy định và nhập/thanh lý theo permission.
- Admin hệ thống: tài khoản/quyền. Admin vận hành: jobs/backup/restore theo permission riêng. Không coi tên admin là tự có mọi quyền.

## Đối chiếu dữ liệu

- BE00.1 lập đầy đủ ánh xạ 38 bảng/288 trường theo DOCX chính trước migration; không dùng số lượng bảng để suy đoán thuộc tính.
- Catalog: Publisher, Author, Category, BookEdition, BookAuthor, BookCategory, Location, BookCopy, MediaAsset (storage lifecycle ở BE11).
- Readers: Reader, ReaderCard. Identity: Account, Role, Permission, AccountRole, RolePermission.
- Policy: PolicyVersion. Circulation: Loan, LoanItem, RenewalEvent, RenewalItem, ReturnEvent, Reservation.
- Finance: FineCharge, Payment, PaymentAllocation, Waiver, PaymentReversal, AllocationReversal, WaiverReversal.
- Operations/report: IdempotencyRecord, OutboxEvent, Job, ReportJob, AuditLog.
- Extensions: AcquisitionReceipt, AcquisitionReceiptItem, BackupManifest.
- Bổ sung được giải thích riêng: ChargeAssessment; Notification/NotificationDelivery metadata. Không ghi đè tên bảng chuẩn.
