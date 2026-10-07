# Kế hoạch triển khai Lib-management

**Trạng thái:** Planned · **Ngày:** 2026-10-07

Bộ kế hoạch mới bao phủ F01–F24. Mỗi module một file Markdown, task bên trong là đơn vị PR. Đây là tài liệu triển khai, chưa có code nghiệp vụ được tạo trong bước này.

## Đọc trước

1. [Quyết định và quy tắc](decisions.md).
2. [Ma trận F01–F24](traceability.md).
3. Chọn module bên dưới, hoàn thành phụ thuộc trước và dùng tiêu chí nghiệm thu trong file.

## Backend

| ID | Module | Phạm vi | Phụ thuộc |
| --- | --- | --- | --- |
| BE00 | [Nền tảng backend](backend/BE00-foundation.md) | Toàn hệ thống | Không |
| BE01 | [Tài khoản và phân quyền](backend/BE01-identity.md) | F16, F21 | BE00 |
| BE02 | [Phiên bản quy định](backend/BE02-policy.md) | F14 | BE00, BE01 |
| BE03 | [Danh mục và bản sao](backend/BE03-catalog.md) | F01–F05, F18 | BE00, BE01; BE02 cho kiểm tra năm |
| BE04 | [Độc giả và thẻ](backend/BE04-readers.md) | F06, F12 | BE01, BE02; BE05/BE06/BE08 cho eligibility đầy đủ |
| BE05 | [Sổ phí và duyệt phí](backend/BE05-finance.md) | F11; hỗ trợ F08, F12 | BE01, BE02, BE04 |
| BE06 | [Cho mượn](backend/BE06-checkout.md) | F07 | BE02, BE03, BE04, BE05 |
| BE07 | [Nhận trả và ghi nhận tình trạng](backend/BE07-returns.md) | F08 | BE05, BE06 |
| BE08 | [Giữ chỗ và gia hạn](backend/BE08-reservations-renewals.md) | F09, F10 | BE06, BE07; worker BE00 |
| BE09 | [Lịch sử, tra cứu và quá hạn](backend/BE09-history-search-overdue.md) | F17, F18, F19 | BE03, BE04, BE05, BE06, BE08 |
| BE10 | [Báo cáo và CSV](backend/BE10-reporting-exports.md) | F13, F20 | BE09, BE00; adapter lưu trữ BE11 |
| BE11 | [Ảnh bìa và lưu trữ](backend/BE11-media.md) | F15; hỗ trợ F20 | BE01, BE03, BE00 |
| BE12 | [Nhập sách và thanh lý](backend/BE12-acquisitions-disposal.md) | F22 | BE01, BE03, BE06, BE08 |
| BE13 | [Thông báo portal và email](backend/BE13-notifications.md) | F24 | BE00, BE07, BE08, BE09 |
| BE14 | [Sao lưu và phục hồi cô lập](backend/BE14-backup-restore.md) | F23 | BE00, BE01; schema nghiệp vụ hoàn chỉnh |

## Frontend

| ID | Module | Phạm vi | Phụ thuộc |
| --- | --- | --- | --- |
| FE00 | [Nền tảng frontend và thiết kế](frontend/FE00-foundation-design.md) | Toàn hệ thống | INT00 |
| FE01 | [Đăng nhập và điều hướng](frontend/FE01-auth-navigation.md) | F16, F21 | FE00, BE01 |
| FE02 | [Danh mục, tìm sách và ảnh bìa](frontend/FE02-catalog.md) | F01–F05, F15, F18 | FE00, FE01, BE03, BE11 |
| FE03 | [Hồ sơ độc giả và cấp thẻ](frontend/FE03-readers-cards.md) | F06, F12 | FE01, BE04 |
| FE04 | [Quầy mượn](frontend/FE04-checkout.md) | F07, F12 | FE01, FE02, FE03, BE06 |
| FE05 | [Quầy trả](frontend/FE05-returns.md) | F08 | FE01, BE07 |
| FE06 | [Giữ chỗ và gia hạn](frontend/FE06-reservations-renewals.md) | F09, F10 | FE01, BE08 |
| FE07 | [Duyệt phí, thu và miễn/đảo](frontend/FE07-finance.md) | F11 | FE01, BE05 |
| FE08 | [Portal độc giả](frontend/FE08-reader-portal.md) | F10, F17, F18, F24 | FE01, FE02, BE08, BE09, BE13 |
| FE09 | [Báo cáo và quy định](frontend/FE09-reports-policy.md) | F13, F14, F19, F20 | FE01, BE02, BE09, BE10 |
| FE10 | [Tài khoản, nhập và thanh lý](frontend/FE10-administration-inventory.md) | F21, F22 | FE01, BE01, BE12 |
| FE11 | [Màn hình vận hành](frontend/FE11-operations.md) | F23, F24 | FE01, BE13, BE14 |

## Tích hợp

| ID | Kế hoạch | Phụ thuộc |
| --- | --- | --- |
| INT00 | [Hợp đồng API](integration/INT00-api-contract.md) | BE00; FE00 dùng contract để phát triển mock |
| INT01 | [Luồng thư viện đầu tiên](integration/INT01-first-library-workflow.md) | BE01–BE07, FE01–FE05 |
| INT02 | [Luồng mở rộng xuyên hệ thống](integration/INT02-extended-workflows.md) | BE08–BE14 và FE06–FE11 |
| INT03 | [Container, CI và bàn giao team](integration/INT03-containers-ci-release.md) | BE00, FE00; hoàn thiện sau INT01/INT02 |

## Thứ tự và làm song song

- M0: INT00 + BE00/BE01 + FE00/FE01. Contract được thống nhất trước khi mock/client sinh tự động.
- M1: BE02/BE03 có thể làm song song; BE04 nối BE05/BE06/BE08 qua port eligibility. Không tạo phụ thuộc import vòng hoặc service commit riêng.
- M2: BE05 → BE06 → BE07 và FE02–FE05 → INT01: đăng nhập, tìm sách, cấp thẻ, mượn, trả.
- M3: BE08/BE09 cùng FE06–FE08; hoàn thiện pending-charge, gia hạn/giữ chỗ và sổ phí.
- M4: BE10–BE14 và frontend tương ứng → INT02. BE11 adapter có thể làm sớm song song Catalog; BE13 nền worker từ M0.
- M5: INT03 hoàn thiện CI/container/E2E và tài liệu bàn giao. Kiểm tra CI/module liên quan được làm ngay từ PR đầu.

## Quy ước task và hoàn thành

- ID BE/FE/INT giữ cố định; .1/.2/.3 là đầu việc triển khai, .4 là nghiệm thu/tài liệu có thể rải trong các PR.
- Trạng thái dùng Planned → In progress → In review → Done; chỉ đổi khi có bằng chứng. Không gán người/deadline khi team chưa phân công.
- Mỗi PR nêu task ID, phụ thuộc, thay đổi schema/API, ca kiểm thử và giới hạn xác minh.
- Dùng Dev Container toàn repository, không phụ thuộc đường dẫn host macOS. Windows dùng Docker Desktop/WSL2 và cùng lệnh container.
- Chỉ soạn tài liệu trong nhiệm vụ hiện tại; không chạy test ứng dụng, thêm dependency hoặc commit/push.

## Rà soát bốn góc nhìn

- PM: ưu tiên luồng phục vụ thư viện; không bỏ sót F21–F24 và truy vết đến nghiệm thu.
- Architect: giữ modular monolith, ownership và một transaction liên module; contract OpenAPI làm ranh giới frontend.
- Developer: một PR/task, client sinh tự động và môi trường portable.
- QA: quyền/scope, cạnh tranh, retry và accessibility phải có ca nghiệm thu chung.
- Điểm căng thẳng: chia theo module dễ làm mất luồng sử dụng. INT01/INT02 sở hữu nghiệm thu xuyên hệ thống; module chạy riêng không đủ để kết luận hoàn thành.

## Nguồn và giới hạn

- [Thiết kế DOCX](../design/library-software-design.docx), [UML](../diagrams/library-uml.drawio); đối chiếu bản DOCX chính do người dùng cung cấp trước migration.
- [Kế hoạch cũ](../archive/planning/PLAN.md) chỉ tham khảo nghiệp vụ/thứ tự; đề xuất stack cũ không còn là quyết định hiện hành.
- Các tệp docs/ui đang bị xóa tại checkout; không khôi phục chúng. Token và hướng UI lấy từ DOCX, mô tả tại FE00/decisions.
- Hosting production chưa chốt; publish image không chứng minh đã deploy.
