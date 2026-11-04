# Quyết định triển khai

Ngày chốt: 2026-10-07. Đây là quyết định đã thống nhất trong phiên làm việc; nhãn OPEN trong snapshot cũ không phủ định quyết định này.

## Nguồn chuẩn và phạm vi

- Toàn bộ F01–F24, gồm quản trị, nhập/thanh lý, backup/restore và thông báo.
- Google Docs mới và data-dictionary.md/json là nguồn mô tả hiện hành: 39 bảng/303 trường (38 bảng/288 trường gốc + ChargeAssessment/15 trường). Ba notification extensions đặc tả riêng, tổng thiết kế 42 bảng; migration chưa triển khai. UML là góc nhìn luồng; PDF tham khảo cấu trúc/nghiệp vụ, không sao chép.
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
| C01 | Chặn mượn khi dư nợ **vượt** ngưỡng cấu hình `allowedOutstandingBalance` (mặc định 50.000 VND) hoặc có sách quá hạn (QĐ12; sửa 04/11/2026, trước đây dư nợ bằng 0) |
| C02 | Tối đa `maxBooksPerLoan` (mặc định 4) cuốn mỗi phiếu (QĐ05); chưa bật activeLoanLimit/activeHoldLimit (phase 2 đặt trước: đang mượn + đang đặt ≤ 4) |
| C03 | Khung phí BM09 `damageLostFees` (hỏng nhẹ/hỏng nặng/mất) là mức Thủ thư đề xuất mặc định; Quản lý vẫn xác nhận từng khoản. Phí mất trong 100.000–600.000 VND (QĐ07) (sửa 04/11/2026) |
| C04 | Hạn ban đầu 4 ngày; tối đa 1 lần gia hạn thêm 4 ngày từ hạn cũ; thẻ còn hiệu lực |
| C05 | Xuất CSV do Quản lý; Excel/PDF ngoài phạm vi đã chốt |
| C06 | Portal có Account gắn Reader; chỉ xem/đặt/hủy trong scope của mình |
| C07 | READY hết hạn `readyHoldDays` (mặc định 3) ngày từ readyAt, không từ thời điểm giao email |
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

## Đồng bộ 08/10/2026 — nguồn mô tả hiện hành

Docs mới/từ điển 7 cột có 39 bảng / 303 trường; 38 bảng / 288 trường là nguồn gốc, ChargeAssessment 15 trường là bổ sung đã mô tả. Notification/NotificationDelivery/NotificationPreference còn đặc tả riêng, chưa tính trong 39/303. Tổng schema thiết kế 42 bảng chưa triển khai.

D01 mới: SQL type/width ChargeAssessment.kind/status; NOT NULL version/created_at còn chưa quy định. Chủ dự án xác nhận trước migration; không đổi C01–C09 hoặc đóng N03–N07 từ việc bổ sung bảng mô tả.

## Quyết định 03/11/2026 — phạm vi lõi 10 tuần

Theo kế hoạch dự án 10 tuần/5 người (rủi ro số 1: phạm vi F01–F24 quá lớn), ưu tiên triển khai được điều chỉnh. Mục này thay thứ tự ưu tiên ở dòng "Toàn bộ F01–F24" phía trên; không xóa chức năng khỏi thiết kế.

- Lõi cam kết trong 10 tuần: F01–F09, F11–F14, F16, F18–F20.
- Phase 2: F10 (giữ chỗ), F15 (ảnh bìa), F17 (lịch sử portal), F21 (quản trị tài khoản qua API), F22 (nhập/thanh lý), F23 (backup/restore), F24 (thông báo).
- Nền tảng (audit, idempotency, outbox/job, RBAC đủ 39 permission) vẫn làm đầy đủ ở M0 để phase 2 không phải đổi schema nền. Trong lõi, role được gán bằng CLI vận hành thay cho API F21.
- Thiết kế, C01–C09 và các quyết định khác giữ nguyên. Spec triển khai: [docs/specs](../specs/README.md).

## Quyết định bổ sung 03/11/2026 — F14, D01 và triển khai lõi

Người dùng đã duyệt [spec toàn bộ lõi](../superpowers/specs/2026-11-03-core-library-design.md) và yêu cầu triển khai: F14 (BE02 và UI FE09.3) thuộc lõi; D01 dùng kind varchar(16), status varchar(24), version integer NOT NULL DEFAULT1 và created_at timestamptz NOT NULL DEFAULT now(). C01–C09 giữ nguyên. Báo cáo lấy snapshot lúc worker bắt đầu, không hỗ trợ client asOf lịch sử trong lõi. API provisioning F16/F21 hoãn, CLI liên kết Account–Reader thuộc lõi. Gate release lõi độc lập phase2; artifact storage private phục vụ CSV vẫn thuộc lõi.

## Quyết định 03/11/2026 — phân quyền theo tên vai trò

Chủ dự án yêu cầu phân quyền "đúng với tên vai trò", thay mô hình tách nhiệm vụ trong ma trận quyền cũ (khi đó Admin hệ thống chỉ có quản trị tài khoản, Quản lý không làm nghiệp vụ quầy, nên các tài khoản này gần như không dùng được màn hình nào trong lõi).

- Thủ thư giữ nguyên quyền nghiệp vụ quầy.
- Quản lý = toàn bộ quyền Thủ thư + duyệt phí, miễn/đảo, xuất CSV, quy định, duyệt nhập/thanh lý, xem tác vụ nền.
- Admin hệ thống = toàn bộ 39 permission.
- Admin vận hành = sao lưu/khôi phục, tác vụ nền, xem báo cáo và CSV; không có quyền quầy hay hồ sơ độc giả.
- Độc giả giữ quyền own; UI ẩn màn nhân viên với tài khoản chỉ có quyền độc giả.

Chi tiết: [ma trận quyền](../design/permission-matrix.md).

## Quyết định 04/11/2026 — đối chiếu lại spec nhóm (Lab 2 v2, Lab 3, Lab 4)

Chủ dự án yêu cầu đọc lại toàn bộ spec của nhóm và sửa các quy định còn sai/thiếu. Nguồn và bảng đối chiếu QĐ01–QĐ26 ↔ code/test: [source-rules.md](../specs/source-rules.md).

- C01 đổi theo QĐ12 (Lab 2 v2) và yêu cầu #12/BM09: ngưỡng 50.000 VND cấu hình được; chặn khi dư nợ **lớn hơn** ngưỡng. Policy v1 cũ giữ ngưỡng 0 vì policy đã duyệt là bất biến.
- C03 đổi theo QĐ07/BM09: có khung phí hỏng nhẹ/hỏng nặng/mất làm mức đề xuất, giữ bước Quản lý xác nhận.
- QĐ16/QĐ17 và Lab 4 FE09.06: Quản lý chỉnh được mọi giá trị trong bản nháp (rules schema v2), server kiểm tra phí ≥ 0, ngưỡng > 0, số ngày là số nguyên dương. Trước đây server chỉ nhận đúng bộ giá trị mặc định.
- Báo cáo theo BM08/Lab 3: OVERVIEW, LOAN_TREND, INVENTORY, TOP_BOOKS, ACTIVE_READERS, LOAN_CSV, FINE_CSV; QĐ13 kỳ không vượt hôm nay; QĐ26 không có dữ liệu thì không tạo tệp.
- Độc giả: loại X/Y/Z (BM02), email duy nhất (Lab 2 YC6), tuổi 12–55 kiểm tra cả khi lập hồ sơ (QĐ01). Thể loại: 3 thể loại chính A/B/C (QĐ04), tên duy nhất (QĐ09).
- Mâu thuẫn giữa các nguồn, giữ nguyên: giữ chỗ 3 ngày (yêu cầu #10, BM09, Lab 3) thay vì 24 giờ (Lab 2 YC9); loại X/Y/Z theo BM02/Lab 2/Lab 3 dù Lab 4 ghi "không tự chốt"; xác thực Keycloak thay cho tài khoản nội bộ và auto-provision (yêu cầu #16, đã hoãn từ 03/11).
