# Nghiệm thu cấu trúc hợp đồng API và phân quyền — 07/10/2026

## Phạm vi và phương pháp

Rà soát đọc trong Dev Container đang mở (`/workspaces/lib-management`), đối chiếu hợp đồng planned với từ điển nguồn và ma trận quyền. Không triển khai chức năng nghiệp vụ, không sửa nguồn thiết kế trong bước nghiệm thu này. Kết quả dưới đây là kiểm tra tĩnh; không suy ra 24 chức năng đã hoạt động.

## Kết quả

| Kiểm tra | Trạng thái | Bằng chứng và giới hạn |
| --- | --- | --- |
| Từ điển nguồn → entity schema | Pass | 38 bảng, 288 trường; tên trường khớp hoàn toàn; required tương ứng NOT NULL, nullable và x-db-constraint đúng từ điển. `docs/design/source-data-dictionary.json`, `docs/design/openapi.json#components.schemas` |
| Định danh operation và reference | Pass | 77 operationId duy nhất, 649 reference nội bộ giải được; 95 component schema. `docs/design/openapi.json` |
| Tách planned và implemented | Pass | 75 operation nghiệp vụ planned, 2 health implemented; không gắn nhãn đã triển khai cho authorization hoặc nghiệp vụ. |
| Permission, Bearer và guard phiên | Pass | Mã quyền khớp ma trận, kể cả nhóm viết tắt; anonymous chỉ GET catalog; các route còn lại yêu cầu Bearer. `/auth/me` dùng x-account-guard=ACTIVE, không tạo permission giả. `docs/design/permission-matrix.md`, `docs/design/api-contract.md` |
| Đọc đặt trước và đề xuất phí | Pass | `/me/reservations` dùng reservation.read; DAMAGE/LOST yêu cầu thêm assessment.propose qua extension điều kiện. Extension là thiết kế, phải được thực thi bằng dependency/service khi code. |
| Ownership job | Pass | Report/export lấy ReportJob.requested_by; provision lấy metadata server Job.payload.requesterAccountId. Job không có cột requested_by; nhánh thiếu metadata bị từ chối. `docs/design/event-job-contracts.md`, `docs/design/identity-design.md` |
| DTO và chống gán trường nội bộ | Pass | Request body đã khai báo đều required; ProvisionRequest/RestoreRequest không chứa requester/approver và cấm trường dư. ProvisionJobPayload/RestoreJobPayload được phân biệt là payload nội bộ. |
| Ngữ cảnh quyền cho FE01 | Pass | AuthContext chứa AccountView và permission tính từ DB, không thêm cột Account; UI không quyết định authorization. |
| Điều kiện duyệt restore | Pass | Payload PENDING/APPROVED riêng với Job QUEUED; planned dispatcher/worker phải kiểm trước lease và trước pg_restore. Endpoint approval đã có, không thêm enum Job; không chọn thêm quy định cấm tự duyệt. |
| Artifact hết hạn | Pass | Download đặc tả410 sau khi kiểm scope; job chưa xong409, ngoài scope404; URL không vượt hạn artifact. |
| Đối chiếu giá trị health theo status | Pass | Hợp đồng live200=ok, ready200=ready, ready503=not_ready; kết quả runtime/test do báo cáo backend ghi riêng. |
| Kiểm tra metaschema OpenAPI/JSON Schema đầy đủ | Not run | Container không có jsonschema; chưa cài thư viện. Các kiểm tra reference/cấu trúc nêu trên không thay thế validator đầy đủ. |
| Authorization runtime, Keycloak và database nghiệp vụ | Not run | Runtime mới có health scaffold. Không có bằng chứng permission, ownership, DTO hoặc restore guard đã thực thi. |
| Nghiệm thu F01–F24 | Not run | Giữ nguyên trạng thái nghiệp vụ trong `docs/quality/acceptance-matrix.md`; bước này không chạy test nghiệp vụ. |
| Google Docs và Drive readback | Not run trong báo cáo này | Parent thực hiện đồng bộ/readback riêng; báo cáo này không xác nhận cloud hoặc rendering Draw.io. |

## Kết luận và điểm còn mở

Không thấy sai lệch cấu trúc mới trong phạm vi kiểm tra ở snapshot hiện tại. Các extension quyền, schema payload và guard restore vẫn phải được triển khai và kiểm thử trước nghiệm thu chức năng. Những quyết định N03–N07 còn mở trong tài liệu nguồn không được tự chốt ở đây. Không xác nhận production-ready hoặc đủ bảo mật chỉ từ hợp đồng thiết kế.

## Đồng bộ cuối sau hai vòng architecture audit

- Drive: đúng file ID `1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn`; modifiedTime `2026-10-07T12:05:49.077Z`; 1.230.546 bytes; SHA256 `c4052199b78fafb106ce580f5bc8e6e7018b1558561cffc228e091dd27f3d068` khớp repo khi tải lại. Một canvas/3.020 cell/94 khung.
- Google Docs: đúng báo cáo `15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8`, tab t.0; đọc lại 82 inline images, 70 bảng, 24 mục chức năng và 82 số hình duy nhất. Thay 26 hình hiện có; thêm 8 hình state/activity F21–F24 đúng mục; sửa danh mục hình/mục lục thủ công và thêm 19.10. Revision cuối lưu trong manifest và snapshot.
- DOCX: 67 bảng/76 hình; thay 73 occurrence sơ đồ từ cell hiện hành, giữ ba hình assessment; nguồn 38 bảng/288 thuộc tính không đổi. Render 149 trang; xem contact sheets toàn tài liệu và chi tiết các trang thay đổi. Routing ảnh xuất ngoài Draw.io là xấp xỉ; chưa kiểm tra toàn canvas bằng GUI Draw.io.
- PDF Google Docs cuối xuất được (17.006.937 bytes), nhưng tải về HTTP403; chỉ xác nhận nội dung/cấu trúc connector, chưa xác nhận bố cục PDF live. DOCX repo là bản nguồn đã sửa, không là export báo cáo live.
- Runtime scaffold: Ruff/format/mypy đạt; mặc định 17 passed/5 skipped, PostgreSQL integration 22 passed. Contract tĩnh 77 operations/649 refs/95 schemas đạt; full OAS metaschema chưa chạy. F01–F24 nghiệp vụ, Keycloak, worker và frontend chưa được nghiệm thu runtime.
- N03–N07 còn mở; lời xác nhận chung không xác định lựa chọn chính sách. Thay đổi đang ở nhánh `fix/architecture-audit`, chưa commit/push.
