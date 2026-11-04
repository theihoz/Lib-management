# Lib-management

## Mục đích và giai đoạn

Phần mềm quản lý thư viện. Dự án đã triển khai lõi 10 tuần ở mức code (chưa nghiệm thu E2E, xem
[audit](docs/quality/2026-11-03-spec-conformance-audit.md)); backend đã chốt Python 3.13, FastAPI và PostgreSQL 17.

## Nguồn chuẩn và phạm vi

[Báo cáo thiết kế chuẩn](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit)
và dữ liệu chuẩn DOCX là nguồn tham chiếu nghiệp vụ. Giữ C01–C09, tên dữ liệu và
thứ tự nội dung chuẩn; schema gốc 38 bảng/288 trường, thêm 4 bảng thiết kế cho duyệt phí/thông báo; migration nghiệp vụ lõi đã có (0003–0005), phase 2 chưa. Xem [thiết kế chi tiết](docs/design/README.md).
Không ghi secrets vào repository, tài liệu
hoặc image; chỉ cung cấp credentials lúc chạy.

Mốc hạ tầng hiện tại gồm API tối thiểu, DB local, health endpoints, Docker và CI,
cùng hợp đồng publish API thủ công lên GHCR sau quality gates trên cùng SHA.
Mốc M0 đã có: migration identity/platform, xác thực Keycloak JWT + permission DB, `GET /api/v1/auth/me`, worker outbox/job, và frontend `apps/web`. Sau M0 đã có code cho catalog, độc giả/thẻ, mượn/trả/gia hạn, phí, quá hạn, báo cáo/CSV và policy (F14) kèm UI; Pages chỉ phục vụ bản build tĩnh, hosting production chưa chốt. Xem [docs/specs](docs/specs/README.md).

## Tiêu chí hoàn thành

- Local API và PostgreSQL chạy được; dữ liệu volume được giữ qua restart.
- Liveness độc lập DB và readiness SELECT 1 có kết quả thành công/thất bại đúng.
- CI kiểm tra source/lockfile, lint, format, typecheck, tests, wheel và production build.
- Publish contract được xác minh: manual/default branch, CI cùng SHA, environment
  image-publish, packages/write chỉ job publish, build trước login, full SHA tag,
  OCI labels, logout và digest summary.

Xác minh local hoặc tĩnh không chứng minh workflow GitHub/GHCR đã chạy hay
production đã được triển khai. Readiness hiện chưa chứng minh schema nghiệp vụ.

## Chưa chốt

Hosting/deployment destination chưa có quyết định. Frontend đã chốt React + TypeScript + Vite; auth dùng Keycloak OIDC/PKCE. Tài khoản độc giả do nhân viên cấp/liên kết. Toàn bộ F01–F24 nằm trong phạm vi; xem [bộ kế hoạch](docs/plan/README.md).
HTTPS, runtime secrets, DB role production, migration và backup/restore phải được
chuẩn bị trước deployment theo [hướng dẫn vận hành](docs/operations/containers-ci.md).
GitHub environment reviewers và branch protection phải do maintainer cấu hình
ngoài repository. Không tự coi các template là quyết định sản phẩm đã chốt.

## Làm việc theo team

Dùng [quy trình team](docs/operations/team-development.md) và Dev Container mount toàn bộ repository. Nguồn tài liệu trong [docs/README.md](docs/README.md) giữ bản DOCX/UML/PDF đã có cùng trạng thái lịch sử rõ ràng. Không phụ thuộc plugin/agent để clone và code dự án.

## Kế hoạch triển khai hiện hành

Từ 03/11/2026 ưu tiên lõi 10 tuần F01–F09, F11–F14, F16, F18–F20 (còn lại phase 2), xem [quyết định](docs/plan/decisions.md#quyết-định-03112026--phạm-vi-lõi-10-tuần). Spec triển khai: [spec lõi](docs/superpowers/specs/2026-11-03-core-library-design.md).

[docs/plan](docs/plan/README.md) chia theo backend, frontend và tích hợp, mỗi module có task nhỏ theo PR. M0 có 9 bảng identity/platform, JWT Keycloak, CLI vận hành; lõi bổ sung catalog, độc giả, lưu thông, phí và báo cáo (66/85 operation được phục vụ; 19 còn lại thuộc phase 2: F15, F21–F24, replay job). Frontend có auth Keycloak PKCE, client sinh từ OpenAPI và 36 màn thuộc lõi. Chưa có Playwright E2E với Keycloak/API/PostgreSQL thật. C01–C09 đã duyệt (C01/C03 cập nhật 04/11/2026 theo spec nhóm: ngưỡng nợ 50.000 VND cấu hình được, khung phí BM09; đối chiếu [QĐ01–QĐ26](docs/specs/source-rules.md)); phí hỏng/mất do Quản lý xác nhận, khoản chờ duyệt chặn mượn/gia hạn/đặt trước nhưng không chặn trả; thông báo portal và email.

## Nguồn hiện hành sau đồng bộ 08/10/2026

Google Docs báo cáo mới là bản hiện hành: 71 bảng tài liệu, trong đó 39 bảng mô tả 7 cột/303 trường = 38 bảng gốc/288 trường + ChargeAssessment/15 trường. Ba notification extensions nằm ngoài mốc này; schema thiết kế dự kiến tổng 42 bảng, migration lõi đã có, các bảng notification chưa.

Từ điển hiện hành: docs/design/data-dictionary.md và data-dictionary.json (đường dẫn tính từ root repo). docs/design/live-report.docx là export trực tiếp từ Docs mới; library-software-design.docx vẫn giữ bản nguồn đã hiệu chỉnh 07/10 để truy vết, không phải export mới. source-data-dictionary.json là dữ liệu trích xuất 38 bảng nguồn. Không dùng bảng 5 cột cũ để phủ định Docs mới.

D01 đã được chủ dự án chốt 03/11/2026 trong spec lõi: kind varchar(16), status varchar(24), version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(). N03–N07 còn mở. Các task BE00.S, BE05.S, FE07.S và INT00.S mô tả gate triển khai; chưa đổi trạng thái Planned.
