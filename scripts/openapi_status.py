"""Mark each design operation implemented/planned from what the API really serves.

Run from apps/api:  uv run --locked python ../../scripts/openapi_status.py [--check]
--check exits 1 instead of rewriting when docs/design/openapi.json is stale.
"""

import json
import sys
from pathlib import Path

from lib_management.config import Settings
from lib_management.main import create_app

DESIGN = Path(__file__).resolve().parents[1] / "docs" / "design" / "openapi.json"
METHODS = {"get", "put", "post", "patch", "delete"}


def served() -> set[tuple[str, str]]:
    schema = create_app(Settings(db_password="openapi-status")).openapi()
    return {
        (path, method)
        for path, item in schema["paths"].items()
        for method in item
        if method in METHODS
    }


def main() -> int:
    raw = DESIGN.read_text()
    design = json.loads(raw)
    runtime = served()
    changed = []
    for path, item in design["paths"].items():
        for method, operation in item.items():
            if method not in METHODS:
                continue
            status = "implemented" if (path, method) in runtime else "planned"
            if operation.get("x-status") != status:
                changed.append(f"{method.upper()} {path}: {status}")
                operation["x-status"] = status
    total = sum(1 for item in design["paths"].values() for m in item if m in METHODS)
    implemented = total - sum(
        1
        for item in design["paths"].values()
        for m, op in item.items()
        if m in METHODS and op["x-status"] == "planned"
    )
    print(f"{implemented}/{total} operations implemented; {len(changed)} changed")
    if "--check" in sys.argv:
        return 1 if changed else 0
    if changed:
        DESIGN.write_text(json.dumps(design, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
