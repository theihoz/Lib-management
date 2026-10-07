#!/usr/bin/env bash
set -euo pipefail
# Trust only this explicitly mounted repository, never every directory.
repository_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
git config --global --add safe.directory "$repository_root"
cd "$repository_root/apps/api"
uv sync --locked --group dev
