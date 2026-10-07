"""Prepare local-only credentials and host mounts, including Git worktrees."""
import json
from pathlib import Path
import secrets
import subprocess

root = Path(__file__).resolve().parent.parent
directory = root / ".devcontainer"
credentials = directory / ".env"
if not credentials.exists():
    password = secrets.token_hex(24)
    with credentials.open("x") as stream:
        stream.write(f"POSTGRES_PASSWORD={password}\nDB_PASSWORD={password}\n")
    credentials.chmod(0o600)
mounts = [{"type": "bind", "source": str(root), "target": str(root)}]
git_common = Path(subprocess.check_output(
    ["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
    text=True,
).strip())
if not git_common.is_relative_to(root):
    mounts.append({"type": "bind", "source": str(git_common), "target": str(git_common)})
configuration = {"services": {"workspace": {
    "working_dir": str(root), "volumes": mounts,
}}}
(directory / "workspace.generated.json").write_text(json.dumps(configuration, indent=2) + "\n")
print("Prepared project/Git mounts and local Dev Container environment.")
