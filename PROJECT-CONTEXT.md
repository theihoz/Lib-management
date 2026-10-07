# Lib-management

## Mục đích và giai đoạn

Phần mềm quản lý thư viện. Dự án đang chuẩn bị hạ tầng và code nghiệp vụ;
backend đã chốt Python 3.13, FastAPI và PostgreSQL 17.

## Nguồn chuẩn và phạm vi

[Báo cáo thiết kế chuẩn](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit)
và dữ liệu chuẩn DOCX là nguồn tham chiếu nghiệp vụ. Giữ C01–C09, tên dữ liệu và
thứ tự nội dung chuẩn; schema 38 bảng/288 trường được triển khai trong nhiệm vụ sau.
Không khôi phục các tài liệu đã bị xóa. Không ghi secrets vào repository, tài liệu
hoặc image; chỉ cung cấp credentials lúc chạy.

Mốc hạ tầng hiện tại gồm API tối thiểu, DB local, health endpoints, Docker và CI,
cùng hợp đồng publish API thủ công lên GHCR sau quality gates trên cùng SHA.
Chưa triển khai CRUD, đăng nhập, schema nghiệp vụ hoặc frontend. Các template
web/Nginx hiện có không tham gia Compose hoặc CI backend.

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

Hosting/deployment destination, frontend và auth provider chưa có quyết định.
HTTPS, runtime secrets, DB role production, migration và backup/restore phải được
chuẩn bị trước deployment theo [hướng dẫn vận hành](docs/operations/containers-ci.md).
GitHub environment reviewers và branch protection phải do maintainer cấu hình
ngoài repository. Không tự coi các template là quyết định sản phẩm đã chốt.
