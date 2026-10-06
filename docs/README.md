# Mục lục tài liệu

## Thiết kế hiện hành

| Thư mục | Nội dung |
| --- | --- |
| [design](design/) | [Tài liệu thiết kế phần mềm](design/library-software-design.docx), xuất từ Google Docs |
| [diagrams](diagrams/) | [Bộ UML chỉnh sửa được](diagrams/library-uml.drawio), mở bằng diagrams.net |
| [plan](plan/) | [Kế hoạch Markdown](plan/PLAN.md), [bản DOCX](plan/implementation-plan.docx) và [lệnh ECC từng bước](plan/ORCHESTRATE.md) |
| [ui](ui/) | [Quy tắc giao diện](ui/DESIGN.md), token JSON/CSS và [prototype HTML](ui/design-preview.html) |
| [references](references/) | Tài liệu tham khảo ban đầu để đối chiếu |

Google Docs thiết kế và kế hoạch được tải về ngày 06/10/2026. Đây là snapshot; thay đổi trên Google Docs sau thời điểm tải sẽ không tự cập nhật trong Git.

- [Google Docs thiết kế](https://docs.google.com/document/d/1aM0zXfRCbXduHbcH1MjuiCiB1BGI-0IPUnFsNsiWcc0/edit)
- [Google Docs kế hoạch](https://docs.google.com/document/d/1hivkkX9RcD3ashGMO3jt0byRqNn9wDm8pCnG-dAWWEM/edit)
- [Bộ UML trên Drive](https://drive.google.com/file/d/1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn/view)

## Tài liệu tham khảo

Các tài liệu trong `references` là nguồn lịch sử, có thể chứa quy tắc mâu thuẫn hoặc sơ đồ chưa được sửa. Dùng tài liệu trong `design` và `plan` cho thiết kế hiện hành; C01–C09 vẫn cần được duyệt.

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
2. Mở file `.drawio` bằng [diagrams.net](https://app.diagrams.net/) để sửa các trang UML.
3. Mở `ui/design-preview.html` trong trình duyệt để xem prototype. Dữ liệu chỉ là minh họa; chưa kết nối API.
4. Lệnh trong `plan/ORCHESTRATE.md` dùng từ thư mục gốc repository trong môi trường ECC hỗ trợ slash command; không chạy như lệnh shell thông thường.
5. Khi cập nhật tài liệu, ghi cùng PR với thay đổi yêu cầu hoặc mã nguồn và cập nhật manifest của tệp thay đổi.
