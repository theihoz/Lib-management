# Rà soát UML và cơ sở dữ liệu — 07/10/2026

## Phát hiện và sửa

| Mức | Bằng chứng trong canvas trước sửa | Cơ chế sai | Sửa trong file |
| --- | --- | --- | --- |
| High | `card_SD_Return__l4/l5`, `board_137/238/149`, `card_AD_F11__n1` | Luồng trả cũ tạo phí hỏng/mất ngay, trái C03 và ChargeAssessment PENDING | Phí trễ theo snapshot; hỏng/mất tạo PENDING; Quản lý quyết định trước FineCharge |
| High | `card_OV_ERD__n0/n19/n23/n24/n25/n26` | ERD cũ trỏ trường không có trong danh mục: active_cover_id, oidc_sub, Job.kind/created_by; audit/outbox/idempotency sai tên | Dùng subset trường từ danh mục chuẩn; Account issuer+subject; Job metadata chuẩn; PK id và UQ actor+operation+key cho idempotency |
| Medium | `card_OV_CLASS__n8/n10`, các bản lớp chi tiết | Reader.name và Loan.createdBy không khớp nguồn; nhiều thuộc tính camelCase/nullable sai | full_name/issued_by, snake_case; nullable lấy từ từ điển gốc |
| Medium | `sync_erd_Circulation_fk_ReturnEvent_loan_item_id`, `sync_erd_Circulation_fk_Reservation_fulfilled_loan_item_id`, `sync_erd_Operations_fk_ReportJob_job_id` | Nhãn con N trái UQ | Bội số con 0..1; FK nullable vẫn tách khỏi bội số ngược |
| Medium | `card_AD_F07/F09/F10/F12`, `card_SD_Checkout__l4` | Sơ đồ lõi thiếu guard PENDING dù extension có | Ghi guard tại các luồng checkout, renew, hold và eligibility |
| Medium | `card_OV_ERD__n11` và các bản PolicyVersion | UQ effective_from không có trong từ điển | UQ version_no; hiệu lực không chồng lấn là ràng buộc riêng |
| Medium | database-design.md, Account.auth_version và quy tắc Account/Role | Prose cũ tuyên bố tăng version thu hồi phiên và local-auth/bốn vai trò còn hiện hành | Nêu rõ cache quyền ứng dụng; JWT/provider revoke riêng; Keycloak đã chốt; 5 vai trò theo permission matrix |

## Đối chiếu bổ sung

Database design bổ sung bất biến liên bảng: thẻ/phiếu cùng độc giả, lượt giữ chỗ cùng ấn bản/bản sao/độc giả, assessment khớp return và khoản phí, allocation cùng chủ thể, READY notification đúng độc giả. FK tồn tại không đủ chứng minh các quan hệ này; kiểm tra trong transaction có khóa. Không thay 38 bảng/288 trường hoặc tự thêm cột nguồn.

## Xác minh

- Một diagram Draw.io; 3.020 cell ID duy nhất; source/target/parent đều hợp lệ; 94 khung giữ nguyên.
- Các projection lớp có tên trường và nullable khớp từ điển.
- 38 hộp ERD chi tiết có đúng thứ tự 288 trường gốc.
- Quét nhãn active (không xét archive) không còn active_cover_id, oidc_sub, policy_id, bảng giá 100.000–600.000 hoặc Job.requested_by.
- Vùng lịch sử giữ nguyên về ý nghĩa. N05 APPROVED còn đánh dấu cần chốt, không chuyển thành trạng thái đã duyệt.

## Giới hạn

Kiểm tra cấu trúc file và nội dung thiết kế; chưa render toàn canvas hoặc chứng minh migration/runtime. DOCX đã được đồng bộ ở bước nghiệm thu tài liệu bên dưới. Drive/Google Docs đã readback ở mục đồng bộ cuối; không dùng byte hash cũ để chứng minh bản live đã nhận cập nhật.


### Chốt gate restore trong F23

Job.status QUEUED không cấp quyền thực thi restore. RestoreJobPayload.approvalStatus=PENDING bị loại trước claim/lease; restore.approve và reason ghi approvedBy/approvedAt phía server dưới khóa Job, chuyển payload APPROVED. Worker kiểm lại metadata, checksum và target allowlist trước pg_restore; metadata sai/thiếu bị từ chối. F23 bỏ luồng chuyển target/promote cũ, chỉ ghi nhận kết quả restore cô lập. Không thêm trạng thái Job hoặc cột vào nguồn chuẩn. Kiểm tra lại: một canvas/3.020 cell/ID và toàn bộ tham chiếu hợp lệ.

Đối chiếu hình DOCX phát hiện nhãn “active cover” 0..1:0..1 còn tồn tại trong class/ERD overview. Đã sửa thành edition 0..1 — media 0..* theo MediaAsset.edition_id nullable; không thêm active_cover_id hoặc unique edition_id vào schema.


## Nghiệm thu đồng bộ DOCX

Bản library-software-design.docx được chỉnh trực tiếp các bảng tóm tắt dữ liệu, quyền, API và F23; đồng bộ Phụ lục A với supplemental-specification.md và thêm A.10. Không dựng lại toàn tài liệu; giữ 67 bảng Word, 76 hình và thứ tự các mục gốc. Danh mục nguồn 38 bảng/288 trường vẫn giữ nguyên tên, kiểu, NULL và constraint.

73 hình nguồn đã thay bằng PNG xuất từ cell hiện hành; ba hình assessment bổ sung giữ nguyên. Mỗi occurrence có relationship riêng khi nội dung khác nhau; đọc lại tất cả 73 ảnh embedded và đối chiếu SHA256 với ảnh tái xuất. Kích thước aspect-fit trong footprint cũ, không kéo giãn hình. Bộ xuất dùng geometry/style/HTML labels thật nhưng routing cạnh xấp xỉ ngoài ứng dụng Draw.io.

Render bằng runtime/LibreOffice đi kèm Codex: 149 trang. Đã xem contact sheets của toàn tài liệu và kiểm tra chi tiết các trang lớp, restore, sequence trả, bảng API, Account/Role và Phụ lục A. Không tuyên bố mọi trang đã được đọc chữ ở zoom100%; các vùng được giữ nguyên và các sơ đồ nhỏ vẫn nên tra trên canvas editable khi cần xem chi tiết. Layout theo nguồn nên còn khoảng trắng ở các trang từ điển dữ liệu; không tự thay bố cục chủ dự án.

## Đồng bộ cuối sau hai vòng architecture audit

- Drive: đúng file ID `1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn`; modifiedTime `2026-10-07T12:05:49.077Z`; 1.230.546 bytes; SHA256 `c4052199b78fafb106ce580f5bc8e6e7018b1558561cffc228e091dd27f3d068` khớp repo khi tải lại. Một canvas/3.020 cell/94 khung.
- Google Docs: đúng báo cáo `15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8`, tab t.0; đọc lại 82 inline images, 70 bảng, 24 mục chức năng và 82 số hình duy nhất. Thay 26 hình hiện có; thêm 8 hình state/activity F21–F24 đúng mục; sửa danh mục hình/mục lục thủ công và thêm 19.10. Revision cuối lưu trong manifest và snapshot.
- DOCX: 67 bảng/76 hình; thay 73 occurrence sơ đồ từ cell hiện hành, giữ ba hình assessment; nguồn 38 bảng/288 thuộc tính không đổi. Render 149 trang; xem contact sheets toàn tài liệu và chi tiết các trang thay đổi. Routing ảnh xuất ngoài Draw.io là xấp xỉ; chưa kiểm tra toàn canvas bằng GUI Draw.io.
- PDF Google Docs cuối xuất được (17.006.937 bytes), nhưng tải về HTTP403; chỉ xác nhận nội dung/cấu trúc connector, chưa xác nhận bố cục PDF live. DOCX repo là bản nguồn đã sửa, không là export báo cáo live.
- Runtime scaffold: Ruff/format/mypy đạt; mặc định 17 passed/5 skipped, PostgreSQL integration 22 passed. Contract tĩnh 77 operations/649 refs/95 schemas đạt; full OAS metaschema chưa chạy. F01–F24 nghiệp vụ, Keycloak, worker và frontend chưa được nghiệm thu runtime.
- N03–N07 còn mở; lời xác nhận chung không xác định lựa chọn chính sách. Thay đổi đang ở nhánh `fix/architecture-audit`, chưa commit/push.
