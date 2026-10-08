# FE11 — Màn hình vận hành

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F23, F24
**Phụ thuộc:** FE01, BE13, BE14

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/operations/jobs, /operations/backups, /operations/restores.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE11.1 | Danh sách job/dead-letter, chi tiết retry và replay có quyền | Bố cục/component, state và hợp đồng màn hình |
| FE11.2 | Tạo backup, xem manifest/checksum và trạng thái | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE11.3 | Đề nghị/duyệt restore target cô lập và xem kết quả diễn tập | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE11.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không có nút restore trực tiếp DB đang dùng.
- lỗi không lộ secrets/PII.
- polling dừng khi terminal.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Bảng điều khiển vận hành

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Job table với state/attempt/next retry; detail có timeline và lỗi đã lọc secrets. Backup manifest/checksum rõ; restore chỉ lựa target cô lập, bước đề nghị/duyệt riêng.

### Motion theo hành động

Status chip120ms chỉ khi state đổi; timeline append180ms; không chạy animation liên tục cho job dài. Pending có label tĩnh ở reduced motion.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Job detail/replay; backup manifest; restore request/approval/result; cảnh báo scope thao tác.

- FE11.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE11.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE11.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Không có restore trực tiếp production; polling dừng terminal; error không lộ PII/secrets; fail không hiển thị trạng thái thành công.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
