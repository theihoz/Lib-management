# Đồng bộ UML — 07/10/2026

Giữ một canvas, toàn bộ cell nguồn và vùng lịch sử. Cập nhật stack/phạm vi/quyết định; bổ sung 8 ERD chi tiết theo danh mục 38 bảng và 6 khung kiến trúc, ERD 4 bảng mới, state/activity/sequence/use case duyệt phí. Mỗi khung có giải thích. FineCharge dùng assessed_amount; phí hỏng/mất chỉ tạo sau Quản lý quyết định.

Tổng 94 khung (80 gốc + 14 bổ sung), 3.020 cells. Sơ đồ cấp cao là góc nhìn tổng quát; thuộc tính chi tiết theo ERD mới và database-design.md. ARCHIVE giữ nhãn lịch sử. APPROVED ở F22 đánh dấu N05 cần chốt, không coi đã có trong enum nguồn DRAFT/POSTED/CANCELLED.

Các ảnh [supplemental](supplemental/) là góc nhìn dùng trong Docs/DOCX; nguồn chỉnh sửa DOT/SVG giữ cạnh ảnh. Chúng mô tả cùng logic trên canvas, không là canvas Draw.io thứ hai. Wireframe riêng tại ../plan/frontend/wireframes.html.


## Rà soát kiến trúc 07/10/2026

Sửa trực tiếp nhãn các cell hiện có, giữ 94 khung/3.020 cells/một canvas:

- Lớp dùng thuộc tính snake_case theo từ điển gốc; Reader.full_name và Loan.issued_by thay nhãn cũ name/createdBy. Dấu nullable lấy từ nguồn, gồm BookCopy.location_id và ReturnEvent.condition.
- ERD tổng quát dùng tên bảng số ít, policy_version_id; bỏ active_cover_id không có trong nguồn. Account dùng issuer+subject; AuditLog/OutboxEvent/Job/IdempotencyRecord dùng các trường có thật trong danh mục. Chi tiết đầy đủ vẫn ở 8 khung ERD 38 bảng.
- FK có UQ của ReturnEvent, fulfilled Reservation và ReportJob ghi con 0..1 thay con N.
- Chú thích và sequence F08/F11 tách phí trễ theo snapshot khỏi đề xuất hỏng/mất PENDING. Xóa phương án bảng giá 100.000–600.000 vì C03 đã duyệt phí thủ công có lý do. Thêm PENDING vào kiểm tra checkout/renew/hold và eligibility; trạng thái UNPAID/PARTIALLY_SETTLED/SETTLED là projection ledger.

Đây là thay đổi file repository. DOCX được render và đồng bộ ở bước nghiệm thu bên dưới; Drive/Google Docs đã readback ở mục đồng bộ cuối, migration/runtime chưa được xác nhận.


### Chốt gate restore trong F23

Job.status QUEUED không cấp quyền thực thi restore. RestoreJobPayload.approvalStatus=PENDING bị loại trước claim/lease; restore.approve và reason ghi approvedBy/approvedAt phía server dưới khóa Job, chuyển payload APPROVED. Worker kiểm lại metadata, checksum và target allowlist trước pg_restore; metadata sai/thiếu bị từ chối. F23 bỏ luồng chuyển target/promote cũ, chỉ ghi nhận kết quả restore cô lập. Không thêm trạng thái Job hoặc cột vào nguồn chuẩn. Kiểm tra lại: một canvas/3.020 cell/ID và toàn bộ tham chiếu hợp lệ.


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

## Đồng bộ Docs mới 08/10/2026

- Nguồn live:39 bảng / 303 trường/7 cột,71 bảng tài liệu/82 ảnh; giữ38 bảng / 288 trường nguồn và provenance.
- Bổ sung data-dictionary.md/json và export live-report.docx; cập nhật snapshot, nguồn chuẩn của plan, gate BE00/BE05/FE07/INT00/BE13.
- UML sửa4 nhãn trong canvas hiện có: tổng số và projection ChargeAssessment đủ15 trường; giữ94 khung/3.020 cell/một canvas. Không đổi quy tắc hoặc trạng thái nghiệp vụ.
- D01 được đánh dấu rõ; ba notification extensions đặc tả riêng, không gán kiểu/NULL chưa được duyệt.
- Các ghi nhận07/10 ở trên là lịch sử. Xem synchronization-2026-10-08.md để biết bằng chứng hiện hành và trạng thái cloud; không dùng hash/revision lịch sử cho bản mới.

Đã áp dụng trên host theo xác nhận chủ dự án. Drive đã tải lại, SHA256 `8896fcfec135fb1abc20e44c441e3b42094fd8ef4f8ecb78c1e58a447f18ae98` khớp repo; Google Docs revision giữ nguyên bản mới. Chưa commit/push.
