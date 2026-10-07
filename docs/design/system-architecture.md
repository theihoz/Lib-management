# Kiến trúc hệ thống Lib-management

Ngày rà soát: 2026-10-07. Trạng thái: thiết kế triển khai; runtime hiện chỉ có scaffold và health endpoints. Áp dụng [quyết định](../plan/decisions.md), [từ điển DB](database-design.md), [API](api-contract.md) và [ma trận quyền](permission-matrix.md).

## Thành phần và trạng thái

| Thành phần | Trách nhiệm | Trạng thái |
| --- | --- | --- |
| React/TypeScript/Vite | Quầy nhân viên và portal; gọi API, PKCE | Planned |
| Keycloak | Xác thực, mật khẩu, phát JWT | Planned |
| FastAPI | Kiểm tra token/account, quyền và scope; lệnh nghiệp vụ | Health đã có; nghiệp vụ Planned |
| PostgreSQL 17 | Nguồn dữ liệu nghiệp vụ, ledger, idempotency, outbox/job | DB local đã có; migration nghiệp vụ Planned |
| Worker riêng | Dispatch outbox, job có lease, thông báo/export | Planned |
| Storage/SMTP adapter | Tệp và gửi email ngoài transaction | Planned |
| Redis | Rate limit dùng chung khi triển khai | Planned; không là nguồn dữ liệu nghiệp vụ |

## Ranh giới module

| Module | Thực thể/trách nhiệm chính | Phụ thuộc nghiệp vụ |
| --- | --- | --- |
| Identity | Account, quyền, liên kết Reader, provisioning | Reader; Keycloak adapter |
| Catalog | Đầu sách, ấn bản, bản sao, phân loại | Policy, media adapter |
| Reader | Độc giả, thẻ, hiệu lực | Policy |
| Circulation | Loan/LoanItem, ReturnEvent, Reservation, gia hạn | Catalog, Reader, Policy, Finance eligibility |
| Finance | FineCharge, ChargeAssessment, thanh toán/phân bổ | Reader, LoanItem |
| Acquisition/disposal | Tiếp nhận, thanh lý, inventory | Catalog; quyết định N05 trước migration |
| Reporting | Query/read projection, ReportJob, CSV | Dữ liệu các module; không tự sửa ledger |
| Operations | Backup/restore vào target cô lập, jobs | Adapter có allowlist; không tự promote |
| Notification | Consent, portal/delivery, outbox consumer | Reader, trạng thái Reservation/LoanItem |

Module chia bằng package trong một modular monolith. Không tạo service mạng riêng cho từng bảng. Router gọi service; service dùng repository và một Unit of Work; repository không tự commit. Module khác gọi giao diện service hoặc query đã định nghĩa, không sửa bảng của module khác bằng SQL tùy tiện.

## Request, session và giao dịch

1. Router kiểm tra JWT, Account còn hoạt động, permission và scope; DTO chỉ nhận field khách hàng được phép ghi.
2. Router có DB đồng bộ dùng `def`. Một Session được sở hữu trong phạm vi request/service transaction, không chia sẻ Session qua các tác vụ chạy song song hoặc chuyển nó sang worker. Async health probe là đường riêng, không quyết định lựa chọn Session nghiệp vụ.
3. Service mở một Unit of Work dùng chung cho mọi thay đổi liên module; kiểm tra lại điều kiện nghiệp vụ dưới khóa. Service commit một lần sau toàn bộ lệnh; lỗi rollback cả lệnh.
4. Ghi audit, idempotency result và outbox cùng transaction nghiệp vụ khi lệnh yêu cầu. Gọi Keycloak/SMTP/storage sau commit qua job/adapter; không giữ khóa trong lúc gọi mạng.
5. Tuân thủ thứ tự khóa đã duyệt: BookEdition → Reader → BookCopy → Loan/LoanItem → Reservation → Charge/Payment; ID tăng dần trong mỗi nhóm. Mọi luồng phải dùng chung giao thức này để tránh đảo thứ tự khóa.

Dư nợ tính từ ledger; tồn kho và quá hạn tính từ dữ liệu nguồn. Không dùng cache như nguồn quyết định eligibility. Khoản assessment PENDING chặn mượn/gia hạn/đặt trước, không chặn trả; nhân viên đề xuất và Quản lý quyết định theo [thiết kế duyệt phí](charge-assessment.md).

## Migration, contract và release

- Migration Alembic chạy ở bước riêng trước rollout, không chạy mỗi replica và không `create_all` trong startup production.
- Health readiness hiện chỉ kiểm tra kết nối; BE00 bổ sung kiểm tra schema revision trước nhận traffic nghiệp vụ.
- OpenAPI trong docs là contract dự kiến. Health phải khớp runtime; mỗi endpoint nghiệp vụ chỉ được đánh dấu đã triển khai sau khi code, kiểm tra quyền/scope, contract test và nghiệm thu tương ứng đạt.
- CI so sánh contract theo phần đã triển khai, không yêu cầu scaffold có toàn bộ endpoint Planned. Khi triển khai DTO, đối chiếu [từ điển nguồn](source-data-dictionary.json), ánh xạ tên và ERD trong UML cùng PR.
- Chưa có hosting production được duyệt. Publish image không đồng nghĩa deployment hoặc backup/restore đã nghiệm thu.

## Nguồn kỹ thuật

- [FastAPI: sync/async handlers](https://fastapi.tiangolo.com/async/).
- [SQLAlchemy: Session ownership and concurrency](https://docs.sqlalchemy.org/en/20/orm/session_basics.html).
- [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0.html).
