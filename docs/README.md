# Tài liệu cho team Lib-management

## Đọc trước khi bắt đầu code

1. [Bối cảnh dự án](../PROJECT-CONTEXT.md) và [hợp đồng hạ tầng](operations/fastapi-infrastructure-spec.md).
2. [Onboarding và quy trình team](operations/team-development.md).
3. [Docker/CI/CD](operations/containers-ci.md), [Dev Container](../.devcontainer/README.md).
4. DOCX thiết kế và UML bên dưới để tra nghiệp vụ; PDF chỉ tham khảo cấu trúc, không sao chép.

Báo cáo Google Docs đã chọn để chỉnh sửa: https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit
Các file Git là snapshot; chưa tải lại nội dung Google Docs mới trong lần cleanup này.
Khi cập nhật nghiệp vụ: giữ tên DOCX chuẩn, đối chiếu UML, ghi thay đổi cùng PR và
cập nhật manifest nếu thay đổi binary nguồn. Prototype UI là minh họa, frontend chưa chốt.

## Dọn tài liệu trùng và file không còn dùng

Đã bỏ kế hoạch thực thi agent trong `docs/superpowers`, lệnh ECC `ORCHESTRATE.md`
và scratch agent đã hoàn tất. Kết quả review/kiểm tra cần bàn giao được giữ ở
[verification.md](operations/verification.md). Bỏ Node bootstrap script, `.nvmrc`,
Dockerfile web và Nginx template vì Compose/CI hiện chỉ dùng FastAPI; frontend chưa chốt.
Giữ nguyên DOCX/UML/PDF/prototype và kế hoạch nghiệp vụ cũ để đối chiếu; không ghi
đè nội dung thiết kế binary chỉ để đồng bộ stack. Kế hoạch cũ có banner lịch sử.

## Kho tài liệu đã có

## Thiết kế hiện hành

| Thư mục | Nội dung |
| --- | --- |
| [design](design/) | [Tài liệu thiết kế phần mềm](design/library-software-design.docx), xuất từ Google Docs |
| [diagrams](diagrams/) | [Bộ UML chỉnh sửa được](diagrams/library-uml.drawio): 80 sơ đồ trên một trang canvas, mở bằng diagrams.net |
| [plan](plan/) | [Kế hoạch Markdown](plan/PLAN.md), [bản DOCX](plan/implementation-plan.docx) (bản lịch sử) |
| [ui](ui/) | [Quy tắc giao diện](ui/DESIGN.md), token JSON/CSS và [prototype HTML](ui/design-preview.html) |
| [references](references/) | Tài liệu tham khảo ban đầu để đối chiếu |

Google Docs thiết kế và kế hoạch được tải về ngày 06/10/2026. Đây là snapshot; thay đổi trên Google Docs sau thời điểm tải sẽ không tự cập nhật trong Git.

- [Google Docs thiết kế](https://docs.google.com/document/d/1aM0zXfRCbXduHbcH1MjuiCiB1BGI-0IPUnFsNsiWcc0/edit)
- [Google Docs kế hoạch](https://docs.google.com/document/d/1hivkkX9RcD3ashGMO3jt0byRqNn9wDm8pCnG-dAWWEM/edit)
- [Bộ UML trên Drive](https://drive.google.com/file/d/1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn/view)

## Tài liệu tham khảo

Các tài liệu trong `references` là nguồn lịch sử, có thể chứa quy tắc mâu thuẫn hoặc sơ đồ chưa được sửa. DOCX và UML là nguồn tham khảo chính đã có. Người dùng đã đồng ý áp dụng C01–C09; snapshot cũ có thể vẫn ghi “cần duyệt”. Backend hiện hành là Python/FastAPI/PostgreSQL; đề xuất TypeScript/NestJS trong plan DOCX/Markdown cũ chỉ giữ làm lịch sử. Không coi bản xuất ngày 06/10 là bản cập nhật live của Google Docs.

| Tệp | Nguồn và mục đích |
| --- | --- |
| [library-thesis-reference.pdf](references/library-thesis-reference.pdf) | PDF tham khảo đã dùng khi rà soát thiết kế |
| [original-architecture.docx](references/original-architecture.docx) | Bản kiến trúc DOCX ban đầu |
| [original-uml.drawio](references/original-uml.drawio) | Bản UML gốc trước chỉnh sửa |
| [source-1.docx](references/source-1.docx) | Google Docs nguồn về DFD và thuật toán |
| [source-2.docx](references/source-2.docx) | Google Docs nguồn về UML và use case |
| [source-3.docx](references/source-3.docx) | Google Docs nguồn về yêu cầu và QĐ01–QĐ08 |

Ba bản Google Docs nguồn trong `references` được lưu từ lần rà soát thiết kế trước. Các liên kết nguồn, thời điểm sửa của ba tài liệu hiện hành và SHA256 nằm trong [source-manifest.json](source-manifest.json).

## Cách sử dụng

1. Đọc `plan/PLAN.md` để xem thứ tự, phụ thuộc và tiêu chí nghiệm thu của 20 bước.
2. Mở file `.drawio` bằng [diagrams.net](https://app.diagrams.net/). Tệp có **một trang canvas duy nhất**, gồm 10 loại sơ đồ có tổng quát, 24 State và 24 Activity theo chức năng, 6 Sequence chi tiết cùng phần chú giải cho từng sơ đồ. Vùng cuối giữ sơ đồ gốc để đối chiếu. Phóng to để đọc từng vùng; canvas lớn không theo khổ A4. Mục lục và tọa độ Y của các vùng nằm trên cùng trang.
3. Mở `ui/design-preview.html` trong trình duyệt để xem prototype. Dữ liệu chỉ là minh họa; chưa kết nối API.
4. Dùng [quy trình team](operations/team-development.md) cho môi trường và Git; lệnh điều phối agent cũ đã được dọn.
5. Khi cập nhật tài liệu, ghi cùng PR với thay đổi yêu cầu hoặc mã nguồn và cập nhật manifest của tệp thay đổi.
