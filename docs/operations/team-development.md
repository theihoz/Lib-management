# Quy trình phát triển cho team

## 1. Nguồn chuẩn và phạm vi

Đọc [mục lục tài liệu](../README.md), DOCX thiết kế và UML một trang trước khi code.
Giữ tên actor/use case/lớp/bảng/thuộc tính theo DOCX; UML quyết định luồng đã mô tả.
C01–C09 đã được người dùng đồng ý áp dụng. Kế hoạch 20 bước cũ giữ để tra nghiệp vụ;
NestJS/Drizzle trong bản đó không phải lựa chọn backend hiện tại. Khi nguồn mâu thuẫn,
ghi rõ vấn đề trong issue/PR để thống nhất trước khi thay đổi quy tắc nghiệp vụ.

Hạ tầng hiện có chỉ gồm health endpoints và DB trống. 38 bảng/288 trường là dữ liệu
thiết kế được nhắc trong báo cáo, chưa là schema được tạo. Frontend/auth/hosting chưa chốt.
Mỗi PR nghiệp vụ cần ánh xạ chức năng → UC → API → dữ liệu → màn hình → kiểm thử.

## 2. Môi trường thống nhất

Dùng [Dev Container](../../.devcontainer/README.md) để sửa toàn bộ repository.
Python 3.13, uv 0.12.21, PostgreSQL 17; package nằm ở `apps/api/src/lib_management`.
Venv Linux ở `/opt/venv`, không dùng `.venv` macOS/Windows. Dev Container tự sync
khi tạo; sau đổi pyproject/lock chạy `cd apps/api && uv sync --locked --group dev`.
Mỗi thành viên có DB local riêng; không chia sẻ mật khẩu production hoặc dump chứa
thông tin độc giả. VS Code là cách mở IDE được cấu hình; chạy Compose qua terminal
cũng mount cùng thư mục, nhưng không tự chuyển terminal host vào container.

## 3. Nhánh, commit, PR

Áp dụng GitHub Flow: `main` → `feature/<chuc-nang>` hoặc `fix/<loi>` → PR → review
và CI → merge. `main` hiện là nền hạ tầng, chưa phải sản phẩm production đầy đủ.
Tạo nhánh từ main đã đồng bộ để làm từng chức năng.

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/catalogue
# Sửa và review diff trước khi stage từng file.
git add apps/api/src/lib_management/<file-can-commit>
git commit -m "feat(catalogue): add book lookup"
git push -u origin feature/catalogue
```

Commit Conventional Commits: `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, `chore`.
Không commit `.env`, file mount sinh tự động, venv/cache, log, token hoặc dump riêng tư.
Không force push nhánh dùng chung. Nhánh đã chia sẻ cập nhật bằng merge origin/main;
rebase chỉ dùng cho nhánh local chưa chia sẻ. Giải quyết conflict cùng chủ module.
Không lưu token/PAT trong Git remote URL; đăng nhập Git riêng trên host hoặc container.

PR nêu mục tiêu, UC, bảng/API ảnh hưởng, cách kiểm tra, migration/rollback và hạn chế.
Reviewer kiểm tra quyền đối tượng, transaction, retry/idempotency, lỗi biên, dữ liệu
và khớp tài liệu. Maintainer cấu hình required `ci-result`, review trước merge và
hạn chế bypass; những thiết lập này ở GitHub, không được YAML tự bật.

## 4. Chia phần việc

| Phần việc | Đầu ra / phụ thuộc |
| --- | --- |
| Catalogue | Đầu sách, bản sao, mã vạch; thống nhất schema trước quầy mượn |
| Độc giả / thẻ | Hồ sơ, hiệu lực, điều kiện mượn theo chính sách đã duyệt |
| Mượn / trả / giữ chỗ | Transaction, khóa, trạng thái, retry; trả độc lập thu tiền |
| Vi phạm / ledger | Charge, payment, allocation, waiver, reversal; giữ lịch sử |
| Nền tảng | Auth/quyền, migration, outbox, CI và vận hành theo quyết định được duyệt |
| Giao diện | Prototype đã có; lựa chọn công nghệ phải được thống nhất trước triển khai |

Team tự phân người phụ trách từng module; không suy diễn tên thành viên. PR đầu tiên
của module chốt contract chung và chủ sở hữu migration để tránh đổi tên bảng/API lệch nhau.

## 5. Lệnh chất lượng và DB kiểm thử

Từ `apps/api`:

```bash
uv sync --locked --group dev
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy src
uv run --locked pytest --ignore=tests/test_db_integration.py
uv build --no-sources
```

Integration chạy khi `RUN_DB_INTEGRATION=1`, với DB_HOST/PORT/USER/NAME/PASSWORD
trỏ **DB disposable riêng**, không DB dev có dữ liệu thật hoặc production. File
`tests/test_db_integration.py` có SELECT/readiness, mật khẩu sai, port đóng,
proxy mất phản hồi và pool đầy. CI cấp fixture riêng và chạy file này rõ ràng.
Kết quả mốc trước cleanup là 15 tests đạt; xem [bằng chứng](verification.md).
Không coi kết quả cũ là kiểm tra cho mọi commit mới.

## 6. Dependency, migration và release

Sửa manifest → `uv lock` → review diff → `uv sync --locked`; không sửa lock thủ công.
Docker pin image digest, CI pin action SHA; cập nhật qua PR và đọc compatibility notes.
Schema nghiệp vụ chưa có Alembic. Khi bổ sung, cần một migration owner, revision
không trùng, thử DB rỗng/upgrade và rollback theo dữ liệu; không tạo 38 bảng suy đoán.

Release image chỉ maintainer chạy workflow thủ công trên default branch sau merge.
Ghi digest từ job summary; không coi tag SHA là immutable registry policy.
Chưa có deploy staging/production. Checklist hosting/TLS/secrets/backup ở
[hướng dẫn vận hành](containers-ci.md).
