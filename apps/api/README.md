# API scaffold

Requires Python 3.13. Dependencies were locked with uv 0.12.21.
Start PostgreSQL first: from the repository root, set `POSTGRES_PASSWORD` in
`.env` and run `docker compose up -d db`. From this directory run `uv sync --locked`,
then set `DB_USER=lib_dev`, `DB_NAME=lib_management`, and `DB_PASSWORD` to the
same password. Set `DB_PORT` to `POSTGRES_PORT` if overriding the default 5432.
Start `uv run --locked uvicorn lib_management.main:create_app --factory`
(host API port 8000; use `--port` to override).

Configuration reads `DB_HOST` (default `127.0.0.1`), `DB_PORT` (default `5432`),
`DB_USER` (default `postgres`), `DB_NAME` (default `lib_management`), and
`DB_PASSWORD` (required, non-empty). No `.env` file is automatically loaded.
The password uses Pydantic SecretStr and SQLAlchemy URL.create.

`/health/live` returns 200 with `{"status":"ok"}` without querying PostgreSQL.
`/health/ready` probes SELECT 1 and returns 200 with `{"status":"ready"}` or
503 with `{"status":"not_ready"}`. Readiness proves connection availability;
there is no business schema or migration in this scaffold. Readiness uses dedicated
async connections with a two-second deadline (including admission and network
reads), closes timed-out connections before cancellation, and allows at most
four active probes. It does not wait for the SQLAlchemy business pool.

Quality checks: `uv run --locked ruff check .`, `uv run --locked ruff format
--check .`, `uv run --locked mypy src`, `uv run --locked pytest -q`, and
`uv build --no-sources`. To intentionally update dependencies, edit the manifest
and run `uv lock`; review the lock diff before syncing.

Docker development runs from the repository root with `docker compose up --build`.
It mounts only this package's `src` directory, keeping container dependencies
in `/opt/venv`, and enables reload. Production builds install the wheel
noneditable and run one Uvicorn worker as UID/GID 10001. See
[container operations](../../docs/operations/containers-ci.md).
