# FE09 — Báo cáo và quy định

**Trạng thái:** Planned · **Ngày:** 2026-10-07

**Phạm vi:** F13, F14, F19, F20
**Phụ thuộc:** FE01, BE02, BE09, BE10

## Nguồn và ranh giới

[Google Docs mới và từ điển 7 cột](../../design/data-dictionary.md) là chuẩn mô tả dữ liệu hiện hành (39 bảng/303 trường); DOCX gốc giữ provenance 38 bảng/288 trường, UML là góc nhìn luồng. Ba bảng notification mở rộng được đặc tả riêng; không cộng vào 39/303. Áp dụng [quyết định](../decisions.md) và [truy vết](../traceability.md). Tệp này là kế hoạch, không chứng minh chức năng đã triển khai.

## Hợp đồng và đầu ra

/manager/reports, /manager/policies, /staff/overdue.

## Task theo PR

| ID | Công việc | Đầu ra bàn giao |
| --- | --- | --- |
| FE09.1 | Bộ lọc thời gian, metric có định nghĩa và bảng quá hạn | Bố cục/component, state và hợp đồng màn hình |
| FE09.2 | Theo dõi job CSV, download và lỗi hết hạn/thu hồi quyền | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE09.3 | Form draft policy, diff, effectiveFrom và approval theo permission | Màn hình tích hợp, tương tác, motion và xử lý lỗi |
| FE09.4 | Viết kiểm thử tương ứng, cập nhật OpenAPI/tài liệu và ma trận truy vết | Ca kiểm thử, hướng dẫn chạy trong Dev Container, bằng chứng nghiệm thu trong PR |

Mỗi PR khai báo task ID và phụ thuộc. Task .4 có thể bổ sung ca kiểm thử trong các PR trước; không trì hoãn kiểm thử đến lúc tích hợp cuối.

## Nghiệm thu và tình huống lỗi

- Không sửa ACTIVE.
- report rỗng không coi lỗi.
- biểu đồ có bảng dữ liệu tương đương.

## Kiểm thử dự kiến

- Vitest/Testing Library cho form, trạng thái, lỗi và quyền hiển thị.
- Playwright cho workflow với API thật; keyboard, focus, nhãn trường và responsive.
- Mock theo OpenAPI cho phát triển sớm; mock thành công không thay nghiệm thu backend thật.

## Điều kiện hoàn thành

- Task và tiêu chí trên đạt; CI liên quan xanh; tài liệu và hợp đồng đồng bộ.
- Không chứa secrets; không tự thay quy tắc DOCX; bổ sung schema có lý do và migration.
- Cập nhật trạng thái thực tế tại mục lục khi PR được merge; giữ giới hạn xác minh rõ ràng.

## Redesign — Dashboard và phiên bản quy định

Đọc [định hướng](DESIGN-DIRECTION.md) và [motion](MOTION.md) trước khi thực hiện. Đây là đặc tả trình bày mới; không sửa quy tắc nghiệp vụ của module.

### Bố cục và điểm nhấn

Header kỳ báo cáo + metric strip có định nghĩa, chart cạnh bảng tương đương; không dashboard toàn card. Policy diff2cột cũ/mới và effectiveFrom rõ; CSV là job có tiến trình.

### Motion theo hành động

Filter crossfade120ms; chart không reveal lại khi poll; policy diff highlight180ms; progress chỉ theo dữ liệu thật.

Mọi transform/stagger bỏ khi reduced motion; trạng thái giữ text/icon. Skeleton dự trữ kích thước; polling không replay animation và không lấy focus.

### Chia PR redesign

Dựng metrics/query definitions; jobs/download; policy draft/diff/approval; empty/error states.

- FE09.D1: áp dụng layout/tokens/component, responsive và các trạng thái tĩnh.
- FE09.D2: nối motion theo trigger thật, reduced motion và focus management.
- FE09.D3: khi triển khai, nghiệm thu text fit, keyboard, API chậm/conflict và hình desktop/mobile; ghi rõ giới hạn xác minh.

Các D-task đi cùng task chức năng hiện có, không tạo thêm API nghiệp vụ chỉ để phục vụ hiệu ứng.

### Tiêu chí bổ sung

Không count-up số liệu gây hiểu sai; chart có table; CSV quyền thu hồi/expired hiển thị rõ; ACTIVE không có edit tùy ý.

Không delay nghiệp vụ để chờ motion. UI chưa có code; các tiêu chí này là kế hoạch, chưa được xác minh trên trình duyệt.
