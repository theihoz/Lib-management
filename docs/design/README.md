# Thiết kế hiện hành — Lib-management

Ngày đồng bộ: 07/10/2026. Nghiệp vụ đang ở giai đoạn thiết kế; chưa có migration/CRUD/frontend/Keycloak hoàn chỉnh.

## Nguồn và thứ tự đọc

Tên và thuộc tính: [DOCX](library-software-design.docx), 38 bảng/288 trường gốc. Quyết định trực tiếp của chủ dự án và [decisions](../plan/decisions.md) quy định stack, F01–F24 và C01–C09. [Dữ liệu trích xuất](source-data-dictionary.json) giữ cấu trúc nguồn để đối chiếu; nhãn lịch sử trong rules không là quyết định hiện hành. Các bổ sung được ghi riêng.

| Tài liệu | Dùng để |
| --- | --- |
| [Database](database-design.md) | 38 bảng gốc, 4 bảng bổ sung, kiểu/NULL/FK/index/transaction/migration |
| [Ma trận quyền](permission-matrix.md) | Permission, actor và scope; không kế thừa quyền mặc nhiên |
| [Identity](identity-design.md) | Keycloak PKCE, provisioning, khóa/thu hồi/reconciliation |
| [Duyệt phí](charge-assessment.md) | PENDING, manager decision, idempotency và chặn đúng tác vụ |
| [API](api-contract.md) / [OpenAPI JSON](openapi.json) | Contract thiết kế, DTO, quyền và lỗi; chưa là runtime export |
| [Sự kiện và job](event-job-contracts.md) | Envelope, dedupe, lease/retry, consent, READY expiry |
| [Threat model](security-threat-model.md) | Ranh giới tin cậy, kiểm soát và tình huống kiểm chứng |
| [Nghiệm thu](../quality/acceptance-matrix.md) | Truy vết F01–F24; hiện Not run |
| [Wireframe](../plan/frontend/WIREFRAMES.md) | 12 màn hình × desktop/mobile và trạng thái |
| [UML](../diagrams/library-uml.drawio) | Một canvas chỉnh sửa được, có ERD chi tiết và luồng bổ sung |
| [Báo cáo đồng bộ](synchronization-report.md) | Sửa gì/vì sao, chứng cứ và câu hỏi còn mở |

## Quy tắc bảo trì

Cập nhật cùng PR: quyết định → DB/permission/API → UML → kế hoạch → acceptance. Không đổi bảng gốc chỉ vì một DTO khác tên; tên vật lý snake_case, command camelCase có ánh xạ rõ. Bản tham khảo cũ trong archive giữ lịch sử; không dùng stack hoặc OPEN cũ để phủ định quyết định đã duyệt. Canvas UML có vùng ARCHIVE; hình lịch sử không phải schema migration.

Google Docs báo cáo được cập nhật trực tiếp: https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit

[Phần bổ sung báo cáo](supplemental-specification.md) và [snapshot text của Docs live](live-report-snapshot.md) phục vụ đối chiếu offline; snapshot không là DOCX export hoặc bộ hình.
