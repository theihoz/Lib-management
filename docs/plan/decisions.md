# Quyết định triển khai

Ngày chốt: 2026-10-07. Đây là quyết định đã thống nhất trong phiên làm việc; nhãn OPEN trong snapshot cũ không phủ định quyết định này.

## Nguồn chuẩn và phạm vi

- Toàn bộ F01–F24, gồm quản trị, nhập/thanh lý, backup/restore và thông báo.
- DOCX thiết kế chính trong Downloads có danh mục 38 bảng; bản trong repository cần đối chiếu trước migration. UML là nguồn luồng; PDF chỉ tham khảo, không sao chép.
- PascalCase là thực thể logic, thuộc tính/bảng vật lý theo snake_case; ánh xạ chính xác trong traceability và migration. Không suy diễn schema đã được triển khai.
- Cập nhật snapshot binary chỉ sau đối chiếu và lưu manifest; bước này chỉ tạo kế hoạch Markdown.

## Công nghệ

- Backend Python 3.13, FastAPI, PostgreSQL 17, SQLAlchemy 2 Session đồng bộ; Alembic. Router đồng bộ cho thao tác DB; không gọi DB đồng bộ trực tiếp trong async route.
- Modular monolith; API/worker riêng; một Unit of Work/Session dùng chung cho giao dịch liên module. Repository không tự commit.
- Frontend React + TypeScript + Vite, React Router, TanStack Query, React Hook Form + Zod; CSS variables; npm và lockfile. Node 24 LTS trong Dev Container; ghim dependency bằng lockfile, không dùng latest trong image release.
- Client TypeScript sinh từ OpenAPI bằng openapi-typescript, request qua openapi-fetch; CI phát hiện drift. Vitest/Testing Library và Playwright.
- Keycloak Authorization Code + PKCE với client public và Bearer JWT. Token chỉ trong bộ nhớ; kiểm tra issuer/audience/JWKS/expiry. Account/permission tại ứng dụng; khóa Account được kiểm tra ở request.
- Nhân viên cấp/liên kết tài khoản độc giả; không tự đăng ký, không JIT cấp admin. Mật khẩu thuộc Keycloak; không lưu tại ứng dụng.
- R2 qua storage adapter; SMTP qua notification adapter; PostgreSQL outbox/jobs bền vững. Redis chỉ cho rate limit dùng chung, không làm nguồn nghiệp vụ.

## C01–C09

| Mã | Quy tắc áp dụng |
| --- | --- |
| C01 | Dư nợ bằng 0; chưa dùng ngưỡng 50.000 VND |
| C02 | Tối đa 4 cuốn mỗi phiếu; chưa bật activeLoanLimit/activeHoldLimit |
| C03 | Phí hỏng/mất thủ công có lý do, Thủ thư đề xuất và Quản lý xác nhận; không tự tạo bảng giá 100.000–600.000 |
| C04 | Hạn ban đầu 4 ngày; tối đa 1 lần gia hạn thêm 4 ngày từ hạn cũ; thẻ còn hiệu lực |
| C05 | Xuất CSV do Quản lý; Excel/PDF ngoài phạm vi đã chốt |
| C06 | Portal có Account gắn Reader; chỉ xem/đặt/hủy trong scope của mình |
| C07 | READY hết hạn 3 ngày từ readyAt, không từ thời điểm giao email |
| C08 | lateDays=max(0,returnLocalDate-dueLocalDate); 1.000 VND/ngày/cuốn; cùng ngày có thể quá hạn nhưng phí 0 |
| C09 | Năm xuất bản từ currentYear−8 đến currentYear, bao gồm hai biên |

## Quyết định bổ sung

- ChargeAssessment PENDING: ghi nhận trả ngay, đóng LoanItem; chặn mượn/gia hạn/đặt trước đến khi Quản lý xác nhận phí hoặc kết thúc không thu có lý do. Không chặn nhận trả. Người xác nhận, số tiền/lý do và audit do server ghi.
- Thông báo portal + email; READY phát sự kiện ngay. Nhắc quá hạn tổng hợp 08:00 Asia/Ho_Chi_Minh, tối đa một email mỗi độc giả/ngày, chỉ gửi khi có consent. Giờ 08:00 là mặc định kế hoạch có thể đổi bằng cấu hình.
- Bổ sung ChargeAssessment và metadata Notification/NotificationDelivery có schema rõ trong plan module; không gọi chúng là các bảng đã có trong danh mục 38.
- Thứ tự khóa: BookEdition → Reader → BookCopy → Loan/LoanItem → Reservation → Charge/Payment; ID tăng dần mỗi nhóm. Cả checkout/return/renew/payment/expiry phải tuân thủ.
- Snapshot policy/dueAt bất biến; ledger chỉ thêm; không lưu dư nợ/số tồn/trạng thái quá hạn làm nguồn chân lý.
- Restore chỉ vào target cô lập allowlist, kiểm tra trước; không promote hoặc thay DB đang phục vụ tự động.
- Giữ tài liệu lịch sử; không khôi phục tệp UI hoặc PR template người dùng đang xóa.
- Hosting production chưa chốt; kế hoạch container/CI tạo artifact và hướng dẫn vận hành, không đồng nghĩa đã deploy.

## Hướng giao diện

Quầy nhân viên gọn, yên tĩnh, dễ quét dữ liệu; portal mobile-first. Chi tiết nhận diện là thanh điều kiện độc giả luôn thấy tại quầy mượn. Dùng Arial/system sans, body 16px; nền trắng, chữ #17212B, primary #174B73, border #C6D0D9, danger #B42318, success #146C43, warning #8A4B08 từ DOCX. Khoảng cách 4/8/12/16/24/32px; target bấm ít nhất 44px; focus rõ, trạng thái có chữ/icon; không lồng card, không hiệu ứng trang giới thiệu. FE00 kiểm tra contrast và text fit trước bàn giao.

Liên kết docs/ui trong README cũ trỏ đến các tệp đang bị xóa. Không phụ thuộc các tệp này; dựng tài liệu token từ DOCX đã xác minh.

## Tham khảo kỹ thuật

- [Vite](https://vite.dev/guide/)
- [Keycloak JavaScript adapter](https://www.keycloak.org/securing-apps/javascript-adapter)
- [SQLAlchemy transaction](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
