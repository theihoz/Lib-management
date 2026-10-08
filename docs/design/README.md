# Thiết kế hiện hành — Lib-management

Ngày đối chiếu Docs mới: 08/10/2026. Nghiệp vụ đang ở giai đoạn thiết kế; chưa có migration/CRUD/frontend/Keycloak hoàn chỉnh.

## Nguồn và thứ tự đọc

Tên và thuộc tính hiện hành: [từ điển 7 cột](data-dictionary.md), 39 bảng/303 trường từ Google Docs mới; [export DOCX live](live-report.docx). [DOCX nguồn đã hiệu chỉnh](library-software-design.docx) giữ provenance 38 bảng/288 trường gốc. Quyết định trực tiếp của chủ dự án và [decisions](../plan/decisions.md) quy định stack, F01–F24 và C01–C09. [Dữ liệu trích xuất](source-data-dictionary.json) giữ cấu trúc nguồn để đối chiếu; nhãn lịch sử trong rules không là quyết định hiện hành. Các bổ sung được ghi riêng.

| Tài liệu | Dùng để |
| --- | --- |
| [Architecture audit](architecture-audit-2026-10-07.md) | Phát hiện, sửa lỗi, kiểm tra vòng hai và giới hạn xác minh |
| [Kiến trúc hệ thống](system-architecture.md) | Ranh giới module, request/session, transaction và trạng thái triển khai |
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

Nghiệm thu cuối sau architecture audit: health/PostgreSQL 22 tests đạt; DOCX/UML/Google Docs đã đồng bộ nội dung. Xem [bằng chứng và giới hạn](../quality/architecture-acceptance-2026-10-07.md). Ghi nhận nghiệm thu 07/10 là lịch sử; xem [rà soát mới](synchronization-2026-10-08.md) cho trạng thái hiện hành. Chức năng nghiệp vụ vẫn Not run.

## Nguồn hiện hành sau đồng bộ 08/10/2026

Google Docs báo cáo mới là bản hiện hành: 71 bảng tài liệu, trong đó 39 bảng mô tả 7 cột/303 trường = 38 bảng gốc/288 trường + ChargeAssessment/15 trường. Ba notification extensions nằm ngoài mốc này; schema thiết kế dự kiến tổng 42 bảng, chưa có migration nghiệp vụ.

Từ điển hiện hành: docs/design/data-dictionary.md và data-dictionary.json (đường dẫn tính từ root repo). docs/design/live-report.docx là export trực tiếp từ Docs mới; library-software-design.docx vẫn giữ bản nguồn đã hiệu chỉnh 07/10 để truy vết, không phải export mới. source-data-dictionary.json là dữ liệu trích xuất 38 bảng nguồn. Không dùng bảng 5 cột cũ để phủ định Docs mới.

D01: SQL type/độ rộng kind/status và NOT NULL version/created_at của ChargeAssessment chưa chốt; giữ nguyên nhãn trong nguồn. N03–N07 còn mở. Các task BE00.S, BE05.S, FE07.S và INT00.S mô tả gate triển khai; chưa đổi trạng thái Planned.
