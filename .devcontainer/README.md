# Dev Container cho macOS, Windows và Linux

Mỗi thành viên clone repository trên **máy của mình**, cùng branch và cấu hình.
Không cần Python/uv trên host: `initializeCommand` dùng Docker chạy Python bootstrap.
Workspace bên trong Linux luôn là **`/workspaces/lib-management`**, không dùng
`/Users/...` hoặc `C:\...` làm đường dẫn container. Compose mount repo tương đối
`..`, nên đổi tên/di chuyển folder hoặc username host không làm sai workspace.

## Mở bằng VS Code

1. Cài Git, VS Code, extension **Dev Containers**, Docker Desktop/Engine và Compose.
2. Clone repo, checkout branch chứa bản sửa nếu PR chưa merge, mở thư mục root.
3. Chọn **Dev Containers: Rebuild and Reopen in Container** khi cập nhật cấu hình;
   những lần sau chọn **Reopen in Container**. Docker phải đang chạy.
4. Terminal có đường dẫn `/workspaces/lib-management`; dependencies tự sync.

### Windows

Dùng Docker Desktop ở chế độ **Linux containers**, bật **Use the WSL 2 based engine**
và **Resources → WSL Integration** cho distro bạn dùng. Không dùng Windows containers
cho image Python Debian này. Khuyến nghị clone vào filesystem WSL, ví dụ `~/code`,
rồi mở bằng `code .` từ terminal WSL. VS Code cần extension WSL nếu mở cách này.

```bash
# Trong WSL:
mkdir -p ~/code
cd ~/code
git clone https://github.com/theihoz/Lib-management.git
cd Lib-management
code .
```

Cũng có thể mở clone ở `C:\code\Lib-management` bằng VS Code Windows với Docker
Desktop. Không lưu repo trong OneDrive/network share; bật quyền chia sẻ folder nếu
Docker Desktop yêu cầu. `.gitattributes` giữ LF cho shell/Python/config; không đổi
shell script sang CRLF. WSL dùng Git Linux và clone riêng, tránh trộn Git Windows
với linked worktree tạo bằng Git WSL trên cùng thư mục.

### macOS và Linux

macOS dùng Docker Desktop, cho phép mount thư mục clone nếu được hỏi. Linux dùng
Docker Engine + Compose và đảm bảo user có quyền gọi Docker. Bootstrap chọn UID/GID
của folder mount (fallback 10001 khi host adapter báo root), để user container ghi
được file ở WSL/Linux. Dev Containers vẫn có thể đồng bộ UID của remoteUser.

## Workspace, Git và dependencies

Python 3.13, uv và Git có sẵn. Venv Dev Container nằm ở
`/home/developer/.venv`, thuộc home của developer và tách khỏi `.venv` host.
Venv `/opt/venv` chỉ thuộc image API dev/production, không phải venv workspace mới.
Tạo lại workspace thì dependencies sync lại; PostgreSQL vẫn ở named volume riêng.

`prepare.py` giữ mật khẩu DB local đã có; máy mới tạo ngẫu nhiên vào
`.devcontainer/.env`. File env và override `workspace.generated.json` không commit;
mỗi máy chạy initialize để sinh đường dẫn/UID phù hợp. Không gửi env cho teammate.
Git trong clone dùng `.git` đã mount. Linked worktree chuẩn được mount metadata
vào `/workspace-git`, với GIT_DIR/GIT_WORK_TREE riêng cho container, không ghi lại
`.git` host. Script setup chỉ trust đúng workspace, không safe.directory=*.

## Chạy API trong terminal container

```bash
cd /workspaces/lib-management/apps/api
uv run --locked uvicorn lib_management.main:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

Swagger: <http://localhost:8000/docs>. Không chạy API Compose khác cùng cổng 8000.
DB chỉ truy cập qua `db:5432` trong network; không cần cổng DB trên host.

## Dùng terminal, không có VS Code

Từ root clone, bootstrap bằng Docker rồi tạo workspace:

**macOS/Linux/WSL (bash/zsh):**

```bash
docker run --rm --mount "type=bind,source=$(pwd),target=/workspace" --env "LOCAL_WORKSPACE_HOST=$(pwd)" python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 python /workspace/.devcontainer/prepare.py
```

**Windows PowerShell:**

```powershell
docker run --rm --mount "type=bind,source=$($PWD.Path),target=/workspace" --env "LOCAL_WORKSPACE_HOST=$($PWD.Path)" python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 python /workspace/.devcontainer/prepare.py
```

**Các lệnh sau giống nhau ở cả hai terminal:**

```bash
docker compose -f .devcontainer/compose.yaml -f .devcontainer/workspace.generated.json up -d --build
docker compose -f .devcontainer/compose.yaml -f .devcontainer/workspace.generated.json exec workspace bash
```

Trong container chạy `bash .devcontainer/setup.sh` một lần để sync dependencies.
`exit` không dừng container; dùng cùng lệnh `exec` để quay lại. Dừng từ host bằng:

```bash
docker compose -f .devcontainer/compose.yaml -f .devcontainer/workspace.generated.json down
```

Không thêm `-v` nếu cần giữ DB. Không đổi mật khẩu env để chữa DB volume cũ;
PostgreSQL giữ mật khẩu role từ lần khởi tạo. Sau chuyển repo/đổi máy, chạy lại
bootstrap và rebuild. Docker bind mounts dùng filesystem của Docker host; cấu hình
này cho Docker local/Docker Desktop, không tự mount filesystem laptop lên Docker
server từ xa. Nếu muốn nhiều máy cùng vào **một server**, dùng Remote SSH + Dev
Containers trên server; VS Code Live Share là lựa chọn riêng cho pair programming.

## Giới hạn xác minh

Cấu hình được sửa từ Dev Container đang mở trên macOS. Chưa chạy Windows native/
WSL2 hoặc thao tác Rebuild UI trên máy Windows; không coi Linux container là bằng
chứng đã chạy thành công Windows. Teammate cần làm theo mục Windows và gửi Dev
Containers log nếu Docker/WSL hoặc share folder vẫn lỗi.

Tham khảo: [VS Code Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers).
