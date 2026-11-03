# Rà soát khoảng thiếu lõi — 03/11/2026

Nguồn: thread `01a1a043-34b0-7a33-abbe-b028a8dc251d` đã kết thúc; mã gốc `main@84441fb`. Người dùng chọn triển khai toàn bộ lõi 10 tuần gồm gia hạn, phí, báo cáo và CSV. Spec bổ sung: [core-library-design](../superpowers/specs/2026-11-03-core-library-design.md), hiện chờ duyệt các quyết định mới.

| Nhóm | Quan sát trên main | Xử lý / trạng thái |
| --- | --- | --- |
| Backend M0 | 9 bảng identity/platform, auth/me, worker, UoW/idempotency/audit/outbox | Có mã và CI main đạt; hai lỗi dưới được sửa tại branch hiện tại |
| DB outage | auth/me trả500 khi kết nối DB thất bại, lệch spec503 | Regression qua kết nối thật tới port đóng: đã sửa503; response không lộ chi tiết |
| Worker lease | Không tự heartbeat; lease hết hạn có thể bị hồi sinh; attempt cũ cùng owner có thể finish lượt mới | Đã thêm heartbeat tự động và guard owner/attempt/expiry; 13 worker integration test đạt |
| Frontend | FE00.1 scaffold; thiếu M0 PR2–5 | Dùng spec M0 có sẵn, sau đó nối từng module thật |
| F14 | Không có trong hai danh sách scope; chưa có policy DB/API/UI | Spec đề xuất đưa BE02/FE09.3 vào lõi; chưa đánh Implemented |
| Tài chính D01 | Kiểu/NULL của assessment còn mở | Đề xuất cụ thể trong spec; chưa ghi đã được chủ dự án duyệt |
| Catalog/reader/circulation | Thiết kế có, runtime chưa có | Lập mốc C2–C4; nghiệm thu UI/API/PG thật, không thay bằng mock |
| F09 lookup | Chưa có tra cứu loan cho nhân viên nếu không biết UUID | Spec bổ sung GET loans theo barcode/card/reader; tách khỏi F17 |
| Reports/CSV | Có operation thiết kế, thiếu result DTO/read path/storage | Spec bổ sung result endpoint, private content download, snapshot/metric/CSV rules |
| Release | INT02 gộp cả phase2, INT03 phụ thuộc | Spec tạo cổng release riêng cho lõi; chưa tự đổi phase2 thành cam kết |
| Tài liệu | Onboarding còn mô tả trước M0; manifest OpenAPI sai hash | Đồng bộ trạng thái đã biết và tính hash lại; không tuyên bố cloud đã đồng bộ |

## Bằng chứng sửa M0 trong branch

- TDD: ca DB outage thất bại với500 trước sửa; ba ca lease mới thất bại trước sửa.
- Sau sửa: `pytest -q` với RUN_DB_INTEGRATION=1 trên database PostgreSQL mới riêng, tự xóa sau chạy: **106 passed**.
- `ruff check .`, `ruff format --check .`, `mypy src`: đạt.
- Chưa có luồng nghiệp vụ UI/API/DB mới; các AT nghiệp vụ giữ Not run. Kết quả test branch không thay bằng chứng merge/release.

## Thay đổi đồng thời ngoài phạm vi

Giữ các chỉnh sửa cá nhân ở devcontainer/ke-hoach-du-an và các file frontend/Figma phát sinh từ phiên khác. Stage/commit theo đường dẫn đã review; không dùng git add toàn workspace.
