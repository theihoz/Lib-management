# Bằng chứng kiểm tra hạ tầng — 07/10/2026

Đây là kết quả kiểm tra của mốc FastAPI trước lần bổ sung Dev Container; không phải kết quả mới sau mỗi commit. Hồ sơ agent được rút gọn vào tài liệu này trước khi dọn.

# Final fix wave report

Status: completed locally. Scope: final-review P2 readiness, both P3 items, and
Task 1 evidence correction. No staging, commits, pushes, hosted Actions execution,
registry publication, business routes/schema, or persistent-volume mutation.

## Changes

- Readiness uses `DatabaseProbe`, with dedicated async psycopg connections and
  four admission slots. Its two-second deadline covers admission, establishment,
  and response reads. It never checks out a SQLAlchemy pooled connection.
- Timeout and request cancellation close an established connection **before**
  cancelling/awaiting the query task. This releases its socket and prevents the
  driver's network cancellation handshake from extending a blackhole timeout.
  Pending async connection attempts and admission waits are cancelled and awaited.
  Every completed attempt releases its slot; no abandoned worker is left behind.
- Both health routes are async. Liveness remains independent of DB and synchronous
  workers. The original SQLAlchemy engine/state/disposal interface remains for
  future business work; health probes bypass its pool.
- Pin reviewed, already cached hatchling version 1.32.4 in build-system.requires.
  `uv lock --offline` confirms manifest consistency. Isolated build transitive
  dependencies remain resolved separately: this is a backend pin, not a claim of
  completely reproducible build dependency graphs or byte-identical wheels.
- API quickstart states the Compose DB prerequisite, lib_dev role, database,
  matching password, DB port override and host API port. Operations/spec document
  the health deadline and concurrency behavior.
- Correct Task 1 report's inaccurate concurrent Task 3 explanation; Task 3's
  report remains the historical integration evidence. Earlier Task 1 synchronous
  implementation prose describes that task's original snapshot, not final code.

## Regression coverage and final commands

Commands in apps/api (uv 0.12.21, local managed Python 3.13):

- `uv run --locked ruff check .`: All checks passed.
- `uv run --locked ruff format --check .`: 10 files already formatted.
- `uv run --locked mypy src`: Success, no issues in 4 source files.
- `DB_HOST=127.0.0.1 DB_PORT=25437 DB_USER=lib_dev DB_NAME=lib_management DB_PASSWORD=<disposable fixture> RUN_DB_INTEGRATION=1 uv run --locked pytest -q`:
  **15 passed in 4.72s**, no skipped integration tests.
- `uv build --no-sources`: successful sdist and wheel.

Regression evidence includes close-before-cancel on stalled reads, HTTP request
cancellation cleanup, forty concurrent stalled connection attempts with at most
four active connections, bounded admission waits and responsive liveness.
Actual PostgreSQL fixture tests cover SELECT/readiness success, wrong password,
closed port, and all fifteen business-engine pool slots occupied while health
still succeeds. No 30-second business-pool checkout can delay readiness.

A real asyncio TCP proxy authenticates against PostgreSQL and then drops SELECT
response bytes while keeping sockets established (no EOF). An initial healthy
probe succeeds; twelve concurrent subsequent requests all return 503 in under
2.5 seconds, four established reads stall, and liveness returns within 0.25
seconds. Disabling the blackhole restores readiness. This exercises actual
psycopg/libpq network reads rather than only a mocked deadline or clean DB stop.
The proxy is a response-loss fixture, not an OS packet-filter simulation.

Commands from repository root:

- `/tmp/task3-actionlint/actionlint .github/workflows/ci.yml .github/workflows/publish-images.yml`: exit 0, no findings.
- `docker build -f docker/api.Dockerfile --target production -t cnpm-api-final-fix:local .`: exit 0. Final local index digest
  `sha256:408b401b1d17c7dfa3d6838787498a4bd9efbdf2a5699511ab0e0c904fa9cb6c`.
- Production container against fixture: UID/GID **10001/10001**, live **200**,
  ready **200**, Docker health **healthy**, mounts **[]**, image architecture
  **arm64**, one-worker exec-form Uvicorn command.
- Stop disposable DB: production ready **503**, body
  `{"status":"not_ready"}`, measured **0.024s**; live **200**.

The PostgreSQL 17 pinned image fixture used unique loopback port 25437 and tmpfs
storage, with no named/bind volume. API used unique loopback port 28007. Both
`cnpm-final-fix-db-1007` and `cnpm-final-fix-api-1007` were removed after checks.
Existing project containers and volumes were preserved.

## Verification boundaries

Local arm64 build/runtime and actionlint establish only the checks above. No
amd64 execution, hosted runner, environment approval, branch protection,
GITHUB_TOKEN authorization, GHCR push, server deployment, or business migration
was attempted or proven. A local fixture timeout is not a hard real-time
scheduler guarantee under arbitrary process starvation. Health connection
creation uses async libpq; hostname resolution follows psycopg's async resolver.

## Dev Container

Ngày 07/10/2026: đã build và khởi động workspace, PostgreSQL healthy, toàn bộ worktree và Git metadata được mount. `uv sync --locked --group dev` đã cài 44 packages; `git status` hoạt động bên trong workspace. Chưa kiểm tra luồng Reopen in Container của VS Code.
