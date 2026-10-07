# FastAPI CI/CD và Docker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Chuẩn bị API Python/FastAPI chạy được cùng PostgreSQL local, container production và pipeline CI/publish image để bắt đầu code nghiệp vụ.

**Architecture:** Backend độc lập trong apps/api; Compose chạy API và PostgreSQL, tách health sống khỏi health kết nối DB. CI kiểm tra backend trực tiếp, không phụ thuộc web hoặc bỏ qua vì app chưa đủ. Workflow publish thủ công tái sử dụng CI cùng SHA trước khi đẩy image GHCR.

**Tech Stack:** Python 3.13, FastAPI, Uvicorn, Pydantic Settings, SQLAlchemy 2.x, psycopg 3.x, uv, Ruff, mypy, pytest, PostgreSQL 17, Docker Compose, GitHub Actions, GHCR.

**Spec:** [Đặc tả hạ tầng](../../operations/fastapi-infrastructure-spec.md), dựa trên lựa chọn stack của người dùng và [báo cáo thiết kế Lib-management](https://docs.google.com/document/d/15pEvPMM7t_oiO0zzggZ_9K-RyN3LqzC4hEaFk2rc1J8/edit).

## Global Constraints

- Python 3.13; requires-python = >=3.13,<3.14; .python-version = 3.13.
- Giữ PostgreSQL major 17 và volume hiện có; không xóa volume hoặc nâng major.
- Chỉ health endpoints; 38 bảng/288 trường, nghiệp vụ C01–C09, frontend và xác thực thuộc bước tiếp theo.
- Không khôi phục deleted docs; không stage thay đổi ngoài phạm vi.
- Không secret thật trong Git/build args/image/log/response; local ports bind 127.0.0.1.
- Chưa deploy máy chủ, thay GitHub settings hoặc push Git trong mốc này.
- Kế hoạch này thay kế hoạch NestJS cũ về backend; giữ file cũ như lịch sử, không coi checkbox cũ là tiến độ FastAPI.
- Không thêm hoặc chạy tests trong lượt lập kế hoạch này. Các bước tests bên dưới dành cho lượt triển khai được duyệt kèm xác minh.

## Review Focus

- Password có @, :, /, $: URL.create truyền nguyên giá trị cho driver, Compose không nội suy lần hai; Task 1/2.
- PostgreSQL chậm, mất kết nối hoặc sai credentials: live vẫn 200, ready 503 trong timeout giới hạn, không lộ lỗi DB; Task 1/2.
- Thiếu/stale uv.lock hoặc thiếu API source: CI fail, không skip hay dùng detector NestJS/web; Task 3.
- PR fork: CI không nhận secret và không có packages/write; Task 3/4.
- Publish nhánh khác hoặc quality fail: không có registry login/push; same-SHA image có digest và runtime nonroot; Task 2/4.

## File Structure

| File | Trách nhiệm |
| --- | --- |
| apps/api/pyproject.toml, uv.lock, .python-version | Package và dependency lock |
| apps/api/src/lib_management/__init__.py | Package entry |
| apps/api/src/lib_management/config.py | Settings, required password, DB connection values |
| apps/api/src/lib_management/db.py | Engine, bounded SELECT 1, dispose |
| apps/api/src/lib_management/main.py | Factory, lifespan, health routes |
| apps/api/tests/test_health.py, test_config.py, test_db_integration.py | Health/config và DB disposable |
| .python-version, compose.yaml, .env.example, .dockerignore, .gitignore | Runtime local, volumes, build context |
| docker/api.Dockerfile | dev/build/production stages |
| .github/workflows/ci.yml | Python quality, integration DB, image build |
| .github/workflows/publish-images.yml, .github/dependabot.yml | Publish API và dependency updates |
| README.md, docs/operations/containers-ci.md | Thay hướng dẫn NestJS đang hoạt động bằng FastAPI |
| PROJECT-CONTEXT.md | Bối cảnh chung đã được người dùng yêu cầu thêm vào kế hoạch |

Giữ docker/web.Dockerfile, docker/nginx.conf, .nvmrc và scripts/ci/app-contract.mjs nhưng bỏ mọi tham chiếu từ Compose/CI backend; ghi rõ chúng là template frontend cũ chưa hoạt động. Không thêm dependency Node cho backend.

### Task 1: API scaffold và health contract

**Files:** Create toàn bộ apps/api files ở bảng trên và root .python-version.

**Interfaces:** `Settings` có db_host:str, db_port:int, db_user:str, db_name:str, db_password:SecretStr. `create_engine_from_settings(settings: Settings) -> Engine`; `check_database(engine: Engine) -> bool`; `create_app(settings: Settings | None = None) -> FastAPI`. App tạo engine trong lifespan, expose app.state.engine, dispose khi shutdown. Uvicorn entry `lib_management.main:create_app --factory`.

- [x] **Step 1: Tạo manifest và khóa dependency.** Runtime FastAPI/Uvicorn/Pydantic Settings/SQLAlchemy/psycopg[binary]; dev Ruff/mypy/pytest/httpx/build; src layout, strict mypy, pytest tests/. Sinh uv.lock bằng uv lock; ghi phiên bản uv đã dùng trong hướng dẫn. Không viết schema nghiệp vụ.
- [x] **Step 2: Viết tests contract** trong test_config.py và test_health.py:

```python
def test_db_password_is_required():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, db_password="")

def test_password_special_characters_are_preserved():
    settings = Settings(db_password="local@:/$_fixture")
    engine = create_engine_from_settings(settings)
    assert engine.url.password == "local@:/$_fixture"
    engine.dispose()

def test_health_contract(client, db_probe):
    db_probe.return_value = True
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").status_code == 200
    assert client.get("/health/ready").json() == {"status": "ready"}
    db_probe.return_value = False
    assert client.get("/health/live").status_code == 200
    response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
```

Fixtures: client uses TestClient(create_app(settings)) context manager; db_probe patches lib_management.main.check_database. Integration tests call real check_database with CI DB settings; closed port and wrong password return False, not exception or credentials.

- [x] **Step 3: Chạy** `cd apps/api && uv run --locked pytest -q`; expected fail vì config/db/main chưa tồn tại.
- [x] **Step 4: Implement interfaces**: URL.create("postgresql+psycopg", ...) không ghép password; pool_pre_ping, connect_timeout 2 và statement_timeout 2000 ms; check_database catches SQLAlchemyError, SELECT 1, returns bool. Sync health route tránh blocking event loop. Liveness không gọi DB. Lifespan dispose engine, không chạy migrations.
- [x] **Step 5: Chạy** `uv run --locked ruff check .`, `uv run --locked ruff format --check .`, `uv run --locked mypy src`, `uv run --locked pytest -q`, `uv build --no-sources`; expected pass và wheel trong dist/.
- [ ] **Step 6: Commit riêng Task 1 khi được yêu cầu lưu Git**; chỉ stage apps/api và .python-version.

### Task 2: Docker và PostgreSQL local

**Files:** Modify compose.yaml, docker/api.Dockerfile, .env.example, .dockerignore, .gitignore; update docs/operations/containers-ci.md và README.md.

**Interfaces:** Consumes factory Task 1 và DB_* settings; produces api:8000, db:5432, production image lib-management-api:local. Context repo root. Không còn profile app cần web.

- [x] **Step 1: Chốt base image metadata** từ official registries: Python 3.13 slim-bookworm, PostgreSQL 17 bookworm và uv stable; pin digest trong Dockerfile/Compose, ghi tag gốc. Không dùng latest hoặc bịa digest.
- [x] **Step 2: Viết Dockerfile**: dependency cache layer từ pyproject/uv.lock, uv sync --locked khi full manifest có mặt; build wheel; production chỉ runtime dependencies + package noneditable trong /opt/venv, UID/GID 10001. Exec CMD Uvicorn factory, 0.0.0.0:8000, một worker, không reload. Dev có reload và bind ./apps/api/src:/app/src; .venv không bị bind mount host che mất.
- [x] **Step 3: Viết Compose**: mặc định api/db; giữ tên volume pgdata và project lib-management. DB healthy mới start API; password bắt buộc .env; healthcheck dùng $$POSTGRES_USER/$$POSTGRES_DB. API no-new-privileges, cap_drop ALL, tmpfs /tmp; không mở DB ra mọi interface. .dockerignore loại .env*, .git, .venv, __pycache__, docs; giữ files cần build.
- [x] **Step 4: Kiểm tra model và image**: `docker compose --env-file .env.example config --quiet` exit 0; bỏ password khỏi fixture env → config fail. `docker build --target production -f docker/api.Dockerfile -t lib-management-api:local .` thành công; inspect Config.User = 10001:10001 và không chứa password.
- [x] **Step 5: Kiểm tra runtime** trong project fixture riêng `lib-management-verify`: start DB/API, live/ready 200; stop DB → live 200/ready 503; restart → ready 200. Password fixture có @:/ $ được driver dùng nguyên giá trị. Ghi marker tạm trong DB, restart, đọc lại marker. Dọn fixture bằng down không -v; không chạm volume dự án chính.
- [x] **Step 6: Cập nhật hướng dẫn**: cp .env.example .env, sửa password, docker compose up --build; port8000 /docs; cách chạy uv local, cập nhật uv.lock, logs, dừng giữ dữ liệu. Nêu readiness chưa kiểm tra 38 bảng và production deployment chưa cấu hình.
- [ ] **Step 7: Commit riêng Task 2 khi được yêu cầu**; chỉ stage file đã sửa thuộc Task 2.

### Task 3: Python CI có PostgreSQL integration

**Files:** Modify .github/workflows/ci.yml, .github/dependabot.yml; Create apps/api/tests/test_db_integration.py; update hướng dẫn.

**Interfaces:** Consumes package/lock/tests Task 1; jobs configuration, quality, container và ci-result; produces required check ci-result. workflow_call không input require_app; backend là bắt buộc.

- [x] **Step 1: Thay detector/matrix Node** bằng direct required-file check apps/api/pyproject.toml, uv.lock, src/lib_management/main.py. PR, push main, workflow_dispatch/workflow_call; contents read, persist-credentials false, timeouts và concurrency cancel trên CI.
- [x] **Step 2: Pin action SHAs** từ upstream checkout/setup-python/setup-uv; Python version-file root .python-version; uv release version explicit. uv sync --locked với dev deps phải fail khi lock stale. Dependabot ecosystems uv, github-actions và docker; không cập nhật Node backend.
- [x] **Step 3: Thêm service PostgreSQL17 riêng CI** với credentials fixture, healthcheck và port5432. Quality run Ruff check/format, mypy, pytest gồm real SELECT 1/wrong-password/closed-port assertions; uv build wheel. Không dùng production secret, không migration fake, pytest không dùng pass-if-no-tests.
- [x] **Step 4: Container job** chỉ sau quality pass, build production image không push. ci-result always tổng hợp configuration/quality/container; chỉ pass khi cả ba success, skipped/cancelled/failure là fail.
- [x] **Step 5: Xác minh** workflow bằng actionlint; fixture thiếu source/uv.lock phải fail file check; sửa dependency nhưng không lock phải fail uv sync --locked. Fork event review xác nhận không secrets/permissions write, không pull_request_target.
- [ ] **Step 6: Commit riêng Task 3 khi được yêu cầu**; CI từ PR thật chỉ chạy sau khi có phép push/PR.

### Task 4: Publish API image thủ công và tài liệu bàn giao

**Files:** Modify .github/workflows/publish-images.yml, docs/operations/containers-ci.md, README.md; Create PROJECT-CONTEXT.md sau khi duyệt preview bên dưới.

**Interfaces:** Consumes reusable CI cùng github.sha, production Dockerfile; produces ghcr.io/<lowercase owner>/lib-management-api:sha-<full SHA> và digest trong job summary. Không build/publish web.

- [x] **Step 1: Branch gate** workflow_dispatch chỉ refs/heads/default_branch; tái sử dụng CI Task 3 cùng commit. Gate fail hoặc CI fail → publish không chạy.
- [x] **Step 2: Publish job** needs quality, environment image-publish, contents read/packages write chỉ ở job này; build image trước login, source/revision OCI labels, tag full SHA. GITHUB_TOKEN qua password-stdin, logout always; ghi RepoDigest vào summary. Không nhận input shell/ref tùy ý.
- [x] **Step 3: Xác minh tĩnh** actionlint pass; assert needs quality và branch gate tồn tại; workflow PR không có publish; test failure fixture không thể tới login/push. Chỉ trigger GHCR thật sau yêu cầu publish của người dùng.
- [x] **Step 4: Bàn giao** ghi rõ GitHub environment reviewers/branch protection cần maintainer bật, package publish không phải server deployment; thêm checklist chọn hosting, HTTPS, runtime secrets, DB role riêng, migrations và backup trước production.
- [x] **Step 4b: Tạo PROJECT-CONTEXT.md theo preview đã duyệt**: tên Lib-management; mục đích quản lý thư viện; stack Python 3.13/FastAPI/PostgreSQL17; giai đoạn chuẩn bị code nghiệp vụ; giữ C01–C09 và dữ liệu chuẩn DOCX, không secrets/khôi phục deleted docs; hoàn thành khi local API+DB, health, CI và publish contract được xác minh. Không coi hosting/frontend/auth provider là quyết định đã chốt.
- [ ] **Step 5: Commit đúng Task 4 khi được yêu cầu**, báo file thay đổi và các bước đã/chưa xác minh; không stage deleted docs hoặc các file ngoài phạm vi.

## Self-review

- Cả bốn nhiệm vụ có interfaces thống nhất, port8000/factory/DB vars/lock paths khớp.
- Năm Review Focus có check cụ thể ở Task 1–4.
- FastAPI là lựa chọn backend người dùng đã chốt; auth provider, frontend, schema và deployment destination chưa được suy diễn.
- PM/Arch/Dev/QA cùng đề nghị scaffold chạy được và ranh giới publish/deploy rõ. Chọn readiness kiểm tra DB ngay; schema revision được bổ sung khi có Alembic, tránh giả định 38 bảng đã tồn tại.
- Chưa triển khai và chưa chạy tests trong lượt lập kế hoạch.

## Execution status — 2026-10-07

Người dùng đã duyệt triển khai Subagent-driven và worktree riêng codex/fastapi-ci-docker. Task1/2 đã qua review; commit/push/publish chưa được yêu cầu. Bước kiểm thử trong lượt triển khai đã được duyệt cùng phương thức thực thi.
