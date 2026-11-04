# Quy định nguồn QĐ01–QĐ26 và nơi triển khai

Đối chiếu ngày 04/11/2026 ([quyết định](../plan/decisions.md#quyết-định-04112026--đối-chiếu-lại-spec-nhóm-lab-2-v2-lab-3-lab-4)). Khi spec nhóm đổi, cập nhật bảng này cùng code và test trong một PR.

## Nguồn

| Tài liệu | Nội dung dùng |
| --- | --- |
| [Bảng yêu cầu](https://docs.google.com/document/d/1UZsEh4NGKM_OBGHocXhkOOpvqz3SDKbG/edit) | 20 yêu cầu, BM01–BM03, QĐ01–QĐ08 |
| [Lab 2 DFD v2](https://docs.google.com/document/d/1QBCDsxck3rTL1FHh9mfNos_Nd772UhyOAC4oJuFt4FE/edit) | BM01–BM15, QĐ01–QĐ26, thuật toán từng yêu cầu (bản mới nhất) |
| [Lab 2 DFD v1](https://docs.google.com/document/d/1Dio7YudemqoVkzgHp6QNtwlJFf2eNKh2PzeZH2IZxqg/edit) | Bản cũ của Lab 2, dùng đối chiếu |
| [Lab 3 UML](https://docs.google.com/document/d/11tcWnRM4Wdc23r0-Fq5F7didcXUskmpM8DDybzkzFy4/edit) | 38 bảng, miền giá trị, mặc định PhienBanQuyDinh, ReportJob.report_type |
| [Lab 4 Giao diện](https://docs.google.com/document/d/17i5MAqcagM54Xi6sl8rNXyBShp1pic6Tb23eCWRZ19w/edit) | FE01–FE11, trường nhập FE09.06 |
| [Thiết kế phần mềm v1.0](https://docs.google.com/document/d/1aM0zXfRCbXduHbcH1MjuiCiB1BGI-0IPUnFsNsiWcc0/edit) | Nguồn C01–C09 (bản dự thảo ghi OPEN; đã chốt trong decisions) |

## Quy định

Giá trị cấu hình được nằm trong `PolicyVersion.rules` (schema v2, `PolicyRules` trong [schemas.py](../../apps/api/src/lib_management/circulation/schemas.py)); mặc định ở `RULES` trong [service.py](../../apps/api/src/lib_management/circulation/service.py). Test ở [test_library_flows.py](../../apps/api/tests/business/test_library_flows.py) (chạy với `RUN_BUSINESS_DB_TESTS=1`).

| QĐ | Nội dung | Triển khai | Test |
| --- | --- | --- | --- |
| QĐ01 | Tuổi độc giả 12–55 | `minReaderAge`/`maxReaderAge`; kiểm tra khi lập hồ sơ, đổi ngày sinh và cấp thẻ (`readers/service.py`) | `test_reader_age_follows_qd01` |
| QĐ02 | Thẻ đúng 6 tháng; thẻ phải còn hạn khi mượn | `cardValidityMonths`, `add_calendar_months`; `eligibility()` lý do `CARD_NOT_VALID` | luồng mượn |
| QĐ03 | Chỉ nhận sách xuất bản trong 8 năm | `publicationYearWindow`, `validate_year` (C09) | catalog |
| QĐ04 | 3 thể loại chính A, B, C | Migration 0008 tạo gốc A/B/C bảo vệ; mọi thể loại khác thuộc cây A/B/C (`category_parent`) | `test_categories_hang_below_main_a_b_c` |
| QĐ05 | Tối đa 4 cuốn mỗi lần mượn | `maxBooksPerLoan`, kiểm tra ở `POST /loans` | `test_checkout_respects_policy_book_limit` |
| QĐ06 | Mượn tối đa 4 ngày; gia hạn 1 lần +4 ngày | `initialLoanDays`, `maxRenewals`, `renewalDays` | `test_checkout_scanner_renewal_and_good_return` |
| QĐ07 | Trễ 1.000 VND/ngày/cuốn; mất 100.000–600.000 | `overdueFinePerDay` (C08); `damageLostFees`, `check_lost_fee` | `test_lost_fee_must_follow_qd07_range` |
| QĐ08 | Không cho mượn khi nợ phạt hoặc trễ hạn | Thay bằng ngưỡng QĐ12 cho nợ phạt; trễ hạn chặn qua `OVERDUE_ITEMS` | `test_outstanding_balance_blocks_only_above_threshold` |
| QĐ09 | Mã và tên thể loại duy nhất; không xóa thể loại có sách | `uq_category_code`, `uq_category_name_lower`; không có API xóa thể loại | `test_category_name_is_unique` |
| QĐ10 | ISBN duy nhất | `book_edition.isbn` UNIQUE, chuẩn hóa ISBN | catalog |
| QĐ11 | Thu không vượt dư nợ | `POST /payments`: phân bổ ≤ dư nợ từng khoản | `test_damage_assessment_payment_replay_and_reversal` |
| QĐ12 | Chặn khi nợ vượt ngưỡng (mặc định 50.000) hoặc có sách quá hạn | `allowedOutstandingBalance`, `outstanding_limit()` | `test_outstanding_balance_blocks_only_above_threshold` |
| QĐ13 | Từ ngày ≤ Đến ngày ≤ hôm nay | `ReportFilters.interval` + kiểm tra ở form FE09 | `test_report_period_follows_qd13` |
| QĐ14 | Top sách/độc giả xếp giảm dần theo lượt mượn | `TOP_BOOKS_SQL`, `ACTIVE_READERS_SQL` | `test_bm08_reports_rank_and_count_loans` |
| QĐ15 | Biểu đồ/bảng, xuất CSV, lưu kết quả | Artifact JSON/CSV của ReportJob; biểu đồ LOAN_TREND ở FE09.03 | `test_bm08_reports_rank_and_count_loans` |
| QĐ16 | Chỉ Quản lý đổi cấu hình; hiện giá trị hiện tại | Quyền `policy.write`/`policy.approve`; FE09.06 hiện giá trị đang hiệu lực | `test_policy_accepts_manager_values` |
| QĐ17 | Phí ≥ 0, ngưỡng > 0, số ngày nguyên dương | `PolicyRules` (server) và `validateDraft` (web) | `test_policy_rejects_invalid_values`, `policyRules.test.ts` |
| QĐ18–QĐ19 | Ảnh bìa PNG/JPG/WebP lên Cloudflare R2 | Phase 2 (F15) | — |
| QĐ20–QĐ21 | Chỉ nhân viên có tài khoản; báo lỗi đăng nhập chung | Keycloak OIDC + Account ACTIVE; thông báo lỗi do Keycloak | `tests/test_jwt.py` |
| QĐ22 | Tra cứu lịch sử độc giả có mã tồn tại | FE03.02 hồ sơ: đang mượn, phạt còn nợ, đặt trước, lịch sử; portal `/me` tab Lịch sử (`/me/loans?status=ALL`) | `test_reader_profile_data_for_yc17`, `test_reader_renews_only_own_loan` |
| QĐ23 | Từ khóa không trống; báo "Không tìm thấy" | Từ khóa trống/khoảng trắng không gửi đi; bảng/lưới và Ctrl+K hiện "Không tìm thấy" | `palette.test.ts`, E2E `catalog.e2e.ts` |
| QĐ24 | Quá hạn khi hôm nay > hạn trả; số ngày trễ = hôm nay − hạn | `/overdue-items`, `late_days` theo ngày thư viện (C08) | `test_overdue_items_include_reader_title_and_late_days` |
| QĐ25 | Chỉ nhân viên đăng nhập được xuất dữ liệu | Quyền `export.create`/`export.download` | quyền |
| QĐ26 | Không có dữ liệu thì không tạo tệp và thông báo | Handler bỏ qua artifact; download trả 409 `NO_DATA`; FE09.04 báo người dùng | `test_export_without_data_creates_no_file` |

## Biểu mẫu và mặc định BM09

| Tham số BM09 | Khóa rules | Mặc định |
| --- | --- | --- |
| Tên thư viện | `libraryName` | Thư viện Lib-management |
| Phí phạt trả trễ / ngày | `overdueFinePerDay` | 1.000 VND |
| Ngưỡng chặn nợ phạt | `allowedOutstandingBalance` | 50.000 VND |
| Số ngày giữ chỗ | `readyHoldDays` | 3 |
| Số ngày mượn tối đa | `initialLoanDays` | 4 |
| Hỏng nhẹ / hỏng nặng / mất | `damageLostFees` | 20.000 / 50.000 / 100.000 VND (spec để trống; mất theo QĐ07) |

Mức phí hỏng nhẹ/nặng là giá trị khởi đầu do nhóm chọn vì BM09 để trống; Quản lý đổi trong bản nháp quy định.

## Mâu thuẫn giữa các nguồn

| Chủ đề | Các nguồn | Áp dụng |
| --- | --- | --- |
| Nợ phạt chặn mượn | QĐ08 "không nợ" ↔ QĐ12, yêu cầu #12, BM09 "vượt 50.000" | QĐ12 (ngưỡng cấu hình) |
| Thời hạn giữ chỗ | Lab 2 YC9 "24 giờ" ↔ yêu cầu #10, BM09, Lab 3 "3 ngày" | 3 ngày (C07) |
| Loại độc giả | BM02, Lab 2, Lab 3 "X/Y/Z" ↔ Lab 4 "không tự chốt" | X/Y/Z |
| Xác thực | Yêu cầu #16 "tài khoản nội bộ, tự provision" ↔ quyết định Keycloak | Keycloak; provisioning qua CLI (03/11) |
| Đặt trước | Lab 2: đang mượn + đang đặt ≤ 4, chỉ đặt sách đã mượn hết | Ghi nhận cho phase 2 (F10) |
