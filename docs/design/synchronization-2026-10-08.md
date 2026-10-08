# Rà soát đồng bộ theo Google Docs mới — 08/10/2026

## Trạng thái

Đã áp dụng vào repository trên host theo xác nhận trực tiếp của chủ dự án. UML được cập nhật tại cùng file Drive ID, tải lại và đối chiếu bytes/SHA256 khớp repository. Google Docs giữ nguyên revision mới đã đối chiếu. Chưa commit/push.

## Nguồn và phát hiện

Google Docs `15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8`, tab t.0, đã đọc lại revision ghi trong data-dictionary.json. Có 71 bảng native, 82 ảnh, 39 bảng mô tả 7 cột và 303 trường. Export DOCX tải thành công 15.381.741 bytes, đọc ZIP/XML xác nhận cùng số lượng bảng/trường/ảnh. Đây là xuất nguyên bản, không chỉnh bố cục tài liệu.

| Mục | Lệch hiện có | Sửa đã áp dụng |
| --- | --- | --- |
| Từ điển dữ liệu | Repo chỉ có nguồn 38 bảng/288 trường, Docs đã thêm ChargeAssessment | Thêm data-dictionary.md/json, đủ 39 bảng/303 trường, 7 cột |
| Nguồn DOCX | Bản nguồn đã sửa 07/10 không phải export live | Giữ nguồn để truy vết; thêm live-report.docx xuất trực tiếp từ Docs mới |
| Snapshot/manifest | Revision và số bảng 70 cũ | Snapshot mới; manifest ghi 71 bảng, revision, hash và trạng thái verified readback |
| UML | Khung ChargeAssessment là subset, chú thích chỉ ghi 38 + 4 | Hiện đủ 15 trường, chú thích 39 bảng mô tả + 3 extensions, giữ một canvas |
| Plan | Nguồn mô tả vẫn chỉ nói DOCX; task chưa ghi gate dữ liệu mới | Cập nhật tham chiếu chung; thêm BE00.S, BE05.S, FE07.S, INT00.S và ranh giới BE13 |
| API | DTO chỉ có 9 trường, dễ hiểu nhầm thiếu 6 cột DB | Giải thích projection an toàn và mapping; không đổi API để khớp số cột DB |
| Quyết định | Không có SQL type/width kind/status hoặc NN version/created_at | D01 chờ xác nhận trước migration; không suy ra từ DEFAULT hoặc API required |

Đối chiếu 288 trường gốc với Docs mới: tên, kiểu, độ rộng, nullable và ràng buộc khớp. Một mô tả Account.auth_version khác nguồn JSON lịch sử: Docs mới nói vô hiệu cache quyền ứng dụng, thu hồi JWT/phiên Keycloak riêng; đây là sửa từ audit trước, được giữ trong từ điển hiện hành. source-data-dictionary.json vẫn giữ dữ liệu trích xuất để truy vết.

## Kiểm tra cấu trúc

- 39 bảng; 303 trường; mỗi dòng đủ 7 cột; ChargeAssessment đủ 15 tên thuộc tính đúng thứ tự Docs.
- UML giữ 1 diagram, 3.020 cell, ID duy nhất, mọi parent/source/target tồn tại. Chỉ sửa 4 nhãn ở vùng hiện hành, không thêm canvas hoặc xóa vùng lịch sử.
- Ba notification extensions có đặc tả tổng quát trong database-design.md nhưng chưa có bảng 7 cột trong Docs. Tổng schema thiết kế dự kiến 42 bảng; không cộng các extension vào mốc 39/303, không coi đã có migration.
- OpenAPI ChargeAssessment là projection 9 trường, không phải bảng vật lý. Tiền API chuỗi số nguyên VND; DB numeric(14,0); command camelCase và entity snake_case được giữ.
- F01–F24, C01–C09 và các guard PENDING vẫn giữ. N03–N07 chưa được đóng. Không thêm hoặc chạy test ứng dụng trong lần soạn tài liệu này.

## Dev Team: Đồng bộ nguồn thiết kế

### PM

**First reaction:** Mốc nghiệm thu tài liệu là 39/303; cần phân biệt ba extension thông báo với danh mục chi tiết.

**Key concerns:** giữ scope F01–F24; phân biệt thiết kế với triển khai; giữ các câu hỏi mở.

**First action:** đối chiếu bảng/trường với nguồn live, ghi trạng thái từng artifact.

**Question for the team:** Ai xác nhận các quyết định schema còn mở trước migration?

### Architect

**First reaction:** Chuyển 7 cột làm rõ schema nhưng không tự chốt kiểu và nullability còn thiếu.

**Key concerns:** vòng đời assessment và transaction; phân biệt API required với DB NN; nguồn gốc 38 bảng và extension.

**First action:** dùng mapping Docs → DB → UML → API → plan.

**Question for the team:** D01 được phê duyệt và ghi lại tại đâu?

### Developer

**First reaction:** Thêm bảng mô tả chưa triển khai migration/nghiệp vụ.

**Key concerns:** mapping đủ 15 trường; DTO projection và UI không công khai dữ liệu tùy tiện; migration có gate cho D01.

**First action:** cập nhật các task và đầu ra bàn giao cụ thể.

**Question for the team:** Chốt D01 trước khi bắt đầu migration ChargeAssessment được không?

### QA

**First reaction:** Đúng số lượng chưa chứng minh đồng bộ ngữ nghĩa hoặc runtime.

**Key concerns:** kiểm tra từng tên/NULL/FK/UQ; giữ điểm chưa chốt; readback cloud riêng với local.

**First action:** xác minh cấu trúc, source parity và giới hạn bằng chứng.

**Question for the team:** Ai nghiệm thu artifact sau khi áp dụng vào repo và Drive?

### Tổng hợp

Cả bốn vai trò yêu cầu phân biệt 39 bảng mô tả với 3 extension và trạng thái triển khai. D01 là điều kiện chặn migration ChargeAssessment; vẫn có thể hoàn tất đồng bộ tài liệu bằng nhãn chưa chốt. Không có xung đột về phạm vi. Giữ projection API thay vì đưa toàn bộ 15 cột vào response chỉ để đủ số lượng.

## Kết quả áp dụng và giới hạn

- Đã kiểm tra precondition SHA256 của cả 44 file trước khi áp dụng: không có thay đổi mới bị ghi đè. Repo ở nhánh fix/architecture-audit; bản nguồn DOCX/JSON lịch sử giữ nguyên.
- Drive ID 1vSIbDUjE65ajxkSRIzZU6nlsjdSooSkn, modifiedTime 2026-10-08T05:02:35.993Z, 1.231.014 bytes. SHA256 tải lại: 8896fcfec135fb1abc20e44c441e3b42094fd8ef4f8ecb78c1e58a447f18ae98, khớp file repo.
- Google Docs revision không đổi so với bản nguồn chuẩn bị. Không viết lại Docs vì đây là nguồn mới dùng để cập nhật các artifact còn lệch. Export DOCX tải được và nằm trong repo.
- Kiểm tra cấu trúc UML/từ điển, ZIP/XML export, local OpenAPI refs, liên kết Markdown và diff whitespace. Không chạy test ứng dụng hoặc khẳng định migration/runtime đã đạt.
- Nhãn UML thay đổi được kiểm tra nội dung/kích thước; ảnh xem trước dựng từ geometry và text của cell, không thay xác minh toàn canvas bằng GUI Draw.io. Bố cục toàn bộ export DOCX chưa render lại trong lượt áp dụng này.
- D01 và N03–N07 còn mở. Ba notification extensions cần hoàn thiện bảng mô tả chi tiết trước migration tương ứng. Chưa commit/push.
