# Tài liệu cho team Lib-management

## Đọc trước khi bắt đầu code

1. [Bối cảnh dự án](../PROJECT-CONTEXT.md) và [hợp đồng hạ tầng](operations/fastapi-infrastructure-spec.md).
2. [Onboarding và quy trình team](operations/team-development.md).
3. [Docker/CI/CD](operations/containers-ci.md), [Dev Container](../.devcontainer/README.md).
4. DOCX thiết kế và UML bên dưới để tra nghiệp vụ; PDF chỉ tham khảo cấu trúc, không sao chép.

Báo cáo Google Docs đã chọn để chỉnh sửa: https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit
Google Docs báo cáo đã cập nhật nội dung trực tiếp ngày 07/10/2026. DOCX trong Git dùng bản chủ dự án cung cấp và phụ lục đồng bộ; không coi nó là bản export nguyên vẹn của báo cáo live.
Khi cập nhật nghiệp vụ: giữ tên DOCX chuẩn, đối chiếu UML, ghi thay đổi cùng PR và
cập nhật manifest nếu thay đổi binary nguồn. Frontend đã chốt React + TypeScript + Vite; xem [kế hoạch frontend](plan/README.md#frontend).

## Dọn tài liệu trùng và file không còn dùng

Đã bỏ kế hoạch thực thi agent trong `docs/superpowers`, lệnh ECC `ORCHESTRATE.md`
và scratch agent đã hoàn tất. Kết quả review/kiểm tra cần bàn giao được giữ ở
[verification.md](operations/verification.md). Bỏ Node bootstrap script, `.nvmrc`,
Dockerfile web và Nginx template vì Compose/CI hiện chỉ dùng FastAPI; frontend React/TypeScript/Vite đã chốt ở thiết kế.
Giữ nguồn lịch sử trong archive. DOCX hiện hành đã cập nhật stack/phạm vi và phụ lục; UML được sửa trên cùng canvas. Prototype UI cũ đã bỏ, thay bằng wireframe và direction trong plan/frontend.

## Kho tài liệu đã có

## Thiết kế hiện hành

| Thư mục | Nội dung |
| --- | --- |
| [design](design/) | [Chỉ mục thiết kế](design/README.md): DOCX chuẩn, database, API, quyền, identity, events, threat model |
| [diagrams](diagrams/) | [Bộ UML chỉnh sửa được](diagrams/library-uml.drawio): 80 khung gốc và 14 khung bổ sung trên một canvas, mở bằng diagrams.net |
| [archive/planning](archive/planning/) | [Kế hoạch Markdown](archive/planning/PLAN.md), [bản DOCX](archive/planning/implementation-plan.docx) (bản lịch sử) |
| [plan](plan/) | Kế hoạch backend/frontend/tích hợp; hướng giao diện và token chuẩn tại [decisions](plan/decisions.md) |
| [archive/references](archive/references/) | Tài liệu tham khảo ban đầu để đối chiếu |

Google Docs thiết kế và kế hoạch được tải về ngày 06/10/2026. Đây là snapshot; thay đổi trên Google Docs sau thời điểm tải sẽ không tự cập nhật trong Git.

- [Google Docs thiết kế](https://docs.google.com/document/d/1aM0zXfRCbXduHbcH1MjuiCiB1BGI-0IPUnFsNsiWcc0/edit)
- [Google Docs kế hoạch](https://docs.google.com/document/d/1hivkkX9RcD3ashGMO3jt0byRqNn9wDm8pCnG-dAWWEM/edit)
- [Bộ UML trên Drive](https://drive.google.com/file/d/1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn/view)

## Tài liệu tham khảo

Các tài liệu trong `archive/references` là nguồn lịch sử, có thể chứa quy tắc mâu thuẫn hoặc sơ đồ chưa được sửa. DOCX và UML là nguồn tham khảo chính đã có. Người dùng đã đồng ý áp dụng C01–C09; snapshot cũ có thể vẫn ghi “cần duyệt”. Backend hiện hành là Python/FastAPI/PostgreSQL; đề xuất TypeScript/NestJS trong plan DOCX/Markdown cũ chỉ giữ làm lịch sử. Không coi bản xuất ngày 06/10 là bản cập nhật live của Google Docs.

| Tệp | Nguồn và mục đích |
| --- | --- |
| [library-thesis-reference.pdf](archive/references/library-thesis-reference.pdf) | PDF tham khảo đã dùng khi rà soát thiết kế |
| [original-architecture.docx](archive/references/original-architecture.docx) | Bản kiến trúc DOCX ban đầu |
| [original-uml.drawio](archive/references/original-uml.drawio) | Bản UML gốc trước chỉnh sửa |
| [source-1.docx](archive/references/source-1.docx) | Google Docs nguồn về DFD và thuật toán |
| [source-2.docx](archive/references/source-2.docx) | Google Docs nguồn về UML và use case |
| [source-3.docx](archive/references/source-3.docx) | Google Docs nguồn về yêu cầu và QĐ01–QĐ08 |

Ba bản Google Docs nguồn trong `archive/references` được lưu từ lần rà soát thiết kế trước. Các liên kết nguồn, thời điểm sửa của ba tài liệu hiện hành và SHA256 nằm trong [source-manifest.json](source-manifest.json).

## Cách sử dụng

1. Đọc [kế hoạch triển khai hiện hành](plan/README.md), [quyết định](plan/decisions.md) và [truy vết F01–F24](plan/traceability.md). Kế hoạch trong `archive/planning` chỉ giữ làm lịch sử.
2. Mở file `.drawio` bằng [diagrams.net](https://app.diagrams.net/). Tệp có **một trang canvas duy nhất**, gồm 10 loại sơ đồ có tổng quát, 24 State và 24 Activity theo chức năng, 6 Sequence chi tiết cùng phần chú giải cho từng sơ đồ. Vùng cuối giữ sơ đồ gốc để đối chiếu. Phóng to để đọc từng vùng; canvas lớn không theo khổ A4. Mục lục và tọa độ Y của các vùng nằm trên cùng trang.
3. Đọc kế hoạch FE00 và hướng giao diện trong `plan/decisions.md`. Các tệp UI cũ đã được bỏ; frontend chưa có code.
4. Dùng [quy trình team](operations/team-development.md) cho môi trường và Git; lệnh điều phối agent cũ đã được dọn.
5. Khi cập nhật tài liệu, ghi cùng PR với thay đổi yêu cầu hoặc mã nguồn và cập nhật manifest của tệp thay đổi.

## Bảo vệ và merge

[Rule main và trạng thái GitHub](operations/branch-protection.md). Các quy tắc quy trình không thay thế branch protection phía GitHub.

## Nguồn hiện hành sau đồng bộ 08/10/2026

Google Docs báo cáo mới là bản hiện hành: 71 bảng tài liệu, trong đó 39 bảng mô tả 7 cột/303 trường = 38 bảng gốc/288 trường + ChargeAssessment/15 trường. Ba notification extensions nằm ngoài mốc này; schema thiết kế dự kiến tổng 42 bảng, chưa có migration nghiệp vụ.

Từ điển hiện hành: docs/design/data-dictionary.md và data-dictionary.json (đường dẫn tính từ root repo). docs/design/live-report.docx là export trực tiếp từ Docs mới; library-software-design.docx vẫn giữ bản nguồn đã hiệu chỉnh 07/10 để truy vết, không phải export mới. source-data-dictionary.json là dữ liệu trích xuất 38 bảng nguồn. Không dùng bảng 5 cột cũ để phủ định Docs mới.

D01: SQL type/độ rộng kind/status và NOT NULL version/created_at của ChargeAssessment chưa chốt; giữ nguyên nhãn trong nguồn. N03–N07 còn mở. Các task BE00.S, BE05.S, FE07.S và INT00.S mô tả gate triển khai; chưa đổi trạng thái Planned.
