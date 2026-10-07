# Môi trường phát triển

Mở **thư mục gốc repository/worktree** trong VS Code có extension Dev Containers,
chọn **Dev Containers: Reopen in Container**. `initializeCommand` chuẩn bị mount
và mật khẩu DB ngẫu nhiên vào `.devcontainer/.env` (không commit).
Container mount toàn bộ dự án ở đúng đường dẫn của máy host; worktree Git cũng
mount thư mục Git chung để `git status` hoạt động. Git dùng chung metadata với
host, nên commit/reset trong container cũng tác động repository host.

Python 3.13, uv và Git có sẵn. Dependencies nằm tại `/opt/venv`, tách khỏi
virtualenv macOS. PostgreSQL dùng volume riêng của `lib-management-devcontainer`.
API khởi động thủ công trong terminal container:

```bash
cd apps/api
uv run --locked uvicorn lib_management.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

Swagger: <http://localhost:8000/docs>.
Không chạy Compose API thông thường đồng thời trên cổng 8000.

Không có IDE hỗ trợ Dev Containers thì dùng terminal từ gốc repository:

```bash
python3 .devcontainer/prepare.py
docker compose -f .devcontainer/compose.yaml -f .devcontainer/workspace.generated.json up -d --build
docker compose -f .devcontainer/compose.yaml -f .devcontainer/workspace.generated.json exec workspace bash
```

Lần tạo bằng terminal cần cài dependencies một lần trong container:
`cd apps/api && uv sync --locked --group dev`.
Thoát shell vẫn giữ container chạy. Dừng bằng:

```bash
docker compose -f .devcontainer/compose.yaml -f .devcontainer/workspace.generated.json down
```

Không thêm `-v` nếu muốn giữ dữ liệu PostgreSQL.
Sau khi di chuyển repository, chạy lại `prepare.py` và tạo lại container.
