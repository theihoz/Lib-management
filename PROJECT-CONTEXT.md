# Lib-management

## Mục đích và giai đoạn

Phần mềm quản lý thư viện. Dự án đang chuẩn bị hạ tầng và code nghiệp vụ;
backend đã chốt Python 3.13, FastAPI và PostgreSQL 17.

## Nguồn chuẩn và phạm vi

[Báo cáo thiết kế chuẩn](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit)
và dữ liệu chuẩn DOCX là nguồn tham chiếu nghiệp vụ. Giữ C01–C09, tên dữ liệu và
thứ tự nội dung chuẩn; schema gốc 38 bảng/288 trường, thêm 4 bảng thiết kế cho duyệt phí/thông báo; migration nghiệp vụ chưa triển khai. Xem [thiết kế chi tiết](docs/design/README.md).
Không ghi secrets vào repository, tài liệu
hoặc image; chỉ cung cấp credentials lúc chạy.

Mốc hạ tầng hiện tại gồm API tối thiểu, DB local, health endpoints, Docker và CI,
cùng hợp đồng publish API thủ công lên GHCR sau quality gates trên cùng SHA.
Chưa triển khai CRUD, đăng nhập, schema nghiệp vụ hoặc frontend. Frontend/Nginx chưa được cấu hình trong stack hiện tại.

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

[docs/plan](docs/plan/README.md) chia theo backend, frontend và tích hợp, mỗi module có task nhỏ theo PR. Đây là kế hoạch chưa triển khai: schema nghiệp vụ, Keycloak và frontend chưa được tạo. C01–C09 đã duyệt; phí hỏng/mất do Quản lý xác nhận, khoản chờ duyệt chặn mượn/gia hạn/đặt trước nhưng không chặn trả; thông báo portal và email.

## Nguồn hiện hành sau đồng bộ 08/10/2026

Google Docs báo cáo mới là bản hiện hành: 71 bảng tài liệu, trong đó 39 bảng mô tả 7 cột/303 trường = 38 bảng gốc/288 trường + ChargeAssessment/15 trường. Ba notification extensions nằm ngoài mốc này; schema thiết kế dự kiến tổng 42 bảng, chưa có migration nghiệp vụ.

Từ điển hiện hành: docs/design/data-dictionary.md và data-dictionary.json (đường dẫn tính từ root repo). docs/design/live-report.docx là export trực tiếp từ Docs mới; library-software-design.docx vẫn giữ bản nguồn đã hiệu chỉnh 07/10 để truy vết, không phải export mới. source-data-dictionary.json là dữ liệu trích xuất 38 bảng nguồn. Không dùng bảng 5 cột cũ để phủ định Docs mới.

D01: SQL type/độ rộng kind/status và NOT NULL version/created_at của ChargeAssessment chưa chốt; giữ nguyên nhãn trong nguồn. N03–N07 còn mở. Các task BE00.S, BE05.S, FE07.S và INT00.S mô tả gate triển khai; chưa đổi trạng thái Planned.
