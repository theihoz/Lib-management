# Ma trận nghiệm thu Lib-management

Ngày: 2026-10-07, cập nhật 2026-11-03. Trạng thái dùng: **Not run**; **Partial** = có pytest chạy trên PostgreSQL thật trong CI (`tests/business`, `tests/integration`, CI xanh trên `main`) nhưng chưa đủ biên lỗi/UI; **Pass** chỉ khi đủ bằng chứng. Chưa có Playwright E2E, nên không ca nào được ghi Pass cho luồng UI→API→DB.

Ghi chú 2026-11-03: Partial = `test_checkout_scanner_renewal_and_good_return` (AT07–AT09), `test_damage_assessment_payment_replay_and_reversal` (AT08, AT11), `test_overdue_items_include_reader_title_and_late_days` (AT19), `test_public_catalog_does_not_require_auth` (AT18). Các ca còn lại của spec lõi §7 (5 cuốn, nửa đêm, cuối tháng, lịch policy cạnh tranh, CSV 410/formula) chưa có test riêng. Mỗi feature gắn [truy vết](../plan/traceability.md), OpenAPI và wireframe tương ứng.

Ghi chú 2026-11-04 (đối chiếu [QĐ01–QĐ26](../specs/source-rules.md)): Partial thêm `test_categories_hang_below_main_a_b_c` (AT03, QĐ04), `test_reader_age_follows_qd01` (AT06), `test_checkout_respects_policy_book_limit` (AT07, 4/5 copy), `test_outstanding_balance_blocks_only_above_threshold` (AT12, QĐ12), `test_bm08_reports_rank_and_count_loans` + `test_export_without_data_creates_no_file` (AT13, QĐ14/QĐ26); `test_policy_rejects_invalid_values` kiểm QĐ17 nhưng chưa phủ AT14. Chồng hiệu lực policy và các luồng E2E vẫn chưa chạy.

| ID | F | Luồng | Dữ liệu/biên lỗi | Kết quả mong đợi | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| AT01 | F01 | Ấn bản | ISBN trùng/year ngoài biên | 409/422, không đổi copies | Not run |
| AT02 | F02 | Bản sao | Barcode trùng một phần lô | Rollback cả lô | Not run |
| AT03 | F03 | Thể loại | Parent là hậu duệ/root delete | 409, cây giữ nguyên | Partial |
| AT04 | F04 | Tác giả | Hai tác giả trùng tên | ID riêng, không tự hợp nhất | Not run |
| AT05 | F05 | NXB | Xóa khi đang tham chiếu | Chặn, giữ FK | Not run |
| AT06 | F06 | Thẻ | Tuổi12/55, ngày31 và expiresAt | Biên hợp lệ, hết hạn đúng mốc | Partial |
| AT07 | F07 | Mượn | 4/5copy, hai quầy, retry | Một OPEN/copy, atomic, cùng key cùng receipt | Partial |
| AT08 | F08 | Trả | Nợ/thẻ hết hạn, hỏng/mất | Vẫn trả; PENDING assessment, copy đúng trạng thái | Partial |
| AT09 | F09 | Gia hạn | Lần2, mục đã trả, có hold | Không sửa từng phần; due cũ+4ngày | Partial |
| AT10 | F10 | Giữ chỗ | FIFO trùng thời gian/expiry | ID tie-break; không pickup expired | Not run |
| AT11 | F11 | Phí | Duyệt đồng thời/thu quá dư/miễn/đảo | Một charge; ledger không âm, không xóa lịch sử | Partial |
| AT12 | F12 | Điều kiện | Preview allowed rồi dữ liệu đổi | Transaction kiểm lại; trả reasons đúng | Partial |
| AT13 | F13 | Báo cáo | Join nhiều ledger/phiếu, rỗng | Không nhân tiền/số phiếu; rỗng hợp lệ | Partial |
| AT14 | F14 | Policy | Chồng hiệu lực/sửaACTIVE | 409; lịch sử không hồi tố | Not run |
| AT15 | F15 | Ảnh | Magic bytes sai/DB lỗi | Không ACTIVE; dọn orphan | Not run |
| AT16 | F16 | Auth | Issuer/audience sai/khóaAccount | 401/403, không JIT | Pass local 2026-11-03 (pytest + Keycloak dev); chờ CI |
| AT17 | F17 | Lịch sử | ReaderA xemB | 404 scoped; không PII | Not run |
| AT18 | F18 | Search | Input SQL/text dài, publiccatalog | Parameterized, bounded, không readerPII | Partial |
| AT19 | F19 | Quá hạn | Đúng dueAt/gia hạn | Derived từ dueAt, không flag cũ | Partial |
| AT20 | F20 | CSV | Formula/revoked/expired | Escape,403/404 scope,410expiry | Not run |
| AT21 | F21 | Quyền | Staff grantadmin | 403, không tự tăng quyền | Not run |
| AT22 | F22 | Nhập/thanh lý | Barcode trùng/ON_LOANdispose | Atomic receipt; guard chặn | Not run |
| AT23 | F23 | Backup | Checksum sai/restorefail | Không đổi servingDB; có drill result | Not run |
| AT24 | F24 | Notify | Timeout/staleREADY/consentfalse | Retry bounded/skipped, không kéo expiry | Not run |

## Kịch bản xuyên module

| ID | Chuẩn bị và thao tác | Kết quả |
| --- | --- | --- |
| CX01 | Hai Session/connection checkout cùng copy | Chính xác một thành công; request khác409, invariant còn đúng |
| CX02 | PENDING assessment được tạo đồng thời checkout/renew/hold trên cùng Reader | Khóa Reader serialize; nếu PENDING commit trước thì chặn; phiếu commit trước không hồi tố |
| CX03 | Hai requests duyệt assessment với key khác | Một terminal/charge; request sau409 |
| CX04 | Crash worker sau gửi email trước ghi delivered | Có thể gửi lặp nếu provider không dedupe; không DB duplicate hoặc tăng READY expiry |
| CX05 | Export tạo khi có quyền, thu hồi trước download | Không phát URL mới; URL đã phát còn hiệu lực đến TTL phải được ghi nhận |
| CX06 | Restore job thất bại sau tạo isolated DB | ServingDB không đổi; target tạm có trạng thái lỗi và cleanup có audit |

## Cách nghiệm thu khi triển khai

- Pytest unit/service; PostgreSQL17 thật cho constraints/transactions/migrations; fixture reset riêng không xóa volume người dùng.
- Playwright cho UI/API thật; keyboard/zoom200%/320–390px mobile/tablet/desktop; prefers-reduced-motion; network delay và retry.
- ASVS chọn lọc/threat cases và role×scope từ permission-matrix; fixture secrets giả.
- Benchmark NFR nguồn: p95checkout/return500ms; search1s;100kcopies/50kreaders/1mhistory/50staff; export100kdòng2phút; ghi máy/workload/queryplan và kết quả, không tự coi mục tiêu là đạt.
- Backup đề xuất RPO24h/RTO4h, retention audit12tháng/artifact24h/idempotency7ngày cần owner duyệt trước production.
- Mỗi lần chạy lưu commit SHA, môi trường, fixture, ca PASS/FAIL và lỗi; chỉ đổi Not run sau có bằng chứng.
