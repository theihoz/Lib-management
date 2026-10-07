"""Prepare local credentials and optional Git worktree mount using Docker Python."""

import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import secrets

root = Path(__file__).resolve().parent.parent
folder = root / ".devcontainer"
credentials = folder / ".env"
if not credentials.exists():
    password = secrets.token_hex(24)
    with credentials.open("x") as stream:
        stream.write(f"POSTGRES_PASSWORD={password}\nDB_PASSWORD={password}\n")
    credentials.chmod(0o600)
    # Bootstrap runs as root. Preserve host access on native Linux / WSL binds.
    if os.geteuid() == 0:
        owner = folder.stat()
        os.chown(credentials, owner.st_uid, owner.st_gid)

owner = folder.stat()
workspace = {"build": {"args": {
    "DEVELOPER_UID": str(owner.st_uid or 10001),
    "DEVELOPER_GID": str(owner.st_gid or 10001),
}}}
git_file = root / ".git"
if git_file.is_file():
    marker = git_file.read_text().strip()
    if not marker.startswith("gitdir: "):
        raise SystemExit("Unsupported .git file. Open a regular clone of the repository.")
    host_root = os.environ.get("LOCAL_WORKSPACE_HOST")
    if not host_root:
        raise SystemExit("Git worktrees require LOCAL_WORKSPACE_HOST (set by devcontainer.json).")
    path_type = PureWindowsPath if PureWindowsPath(host_root).drive else PurePosixPath
    git_dir = path_type(marker.removeprefix("gitdir: "))
    if not git_dir.is_absolute():
        git_dir = path_type(host_root) / git_dir
    if git_dir.parent.name != "worktrees":
        raise SystemExit("Nonstandard Git metadata. Use a regular clone for this Dev Container.")
    # Linked worktrees use <common Git dir>/worktrees/<name>, commondir ../..
    common_git = git_dir.parent.parent
    workspace.update({
        "volumes": [{"type": "bind", "source": str(common_git), "target": "/workspace-git"}],
        "environment": {
            "GIT_DIR": f"/workspace-git/worktrees/{git_dir.name}",
            "GIT_WORK_TREE": "/workspaces/lib-management",
        },
    })
configuration = {"services": {"workspace": workspace}}
generated = folder / "workspace.generated.json"
generated.write_text(json.dumps(configuration, indent=2) + "\n")
if os.geteuid() == 0:
    owner = folder.stat()
    os.chown(generated, owner.st_uid, owner.st_gid)
print("Prepared local DB environment; workspace path is /workspaces/lib-management.")
