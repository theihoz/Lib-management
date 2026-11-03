# Spec M0 — Nền tảng backend, hợp đồng API và xác thực

**Trạng thái:** In review (nhánh `feature/m0-backend`) · **Ngày:** 2026-11-03 · **Task:** BE00, INT00 (.1/.3), BE01 (.1/.2) · **Chức năng:** F16 (nền cho F01–F20)

Spec này gom các quyết định đã có thành một bản đủ cụ thể để code. Nó **không** thay nguồn chuẩn: tên bảng/cột lấy từ [thiết kế DB](../design/database-design.md), quyền từ [ma trận quyền](../design/permission-matrix.md), schema HTTP từ [openapi.json](../design/openapi.json), quy tắc từ [decisions](../plan/decisions.md). Khi spec mâu thuẫn với nguồn chuẩn, nguồn chuẩn thắng và spec phải được sửa trong cùng PR.

Phạm vi sản phẩm theo [quyết định 03/11/2026](../plan/decisions.md#quyết-định-03112026--phạm-vi-lõi-10-tuần): lõi 10 tuần F01–F09, F11–F14, F16, F18–F20.

## 1. Phạm vi

**Trong M0**

- Alembic và 9 bảng: `account`, `role`, `permission`, `account_role`, `role_permission`, `audit_log`, `idempotency_record`, `outbox_event`, `job`.
- Session đồng bộ mỗi request, Unit of Work (UoW) do service sở hữu.
- Lỗi chuẩn `ErrorResponse`, request ID, pagination cursor, helper idempotency, helper audit, helper outbox.
- Worker riêng: dispatch outbox → job, lease/retry/DEAD.
- Keycloak local cho Dev Container; xác thực JWT; guard Account ACTIVE + permission DB.
- `GET /api/v1/auth/me`.
- CLI `seed-rbac` và `bootstrap-admin`.
- Kiểm tra drift giữa runtime OpenAPI và `docs/design/openapi.json` cho các operation đã triển khai.

**Ngoài M0**

- `/accounts`, `/roles`, `/accounts/{id}/roles`, `/roles/{id}/permissions`, reader-provisioning: thuộc F21 (phase 2). Trong M0 gán role bằng CLI.
- Frontend (FE00/FE01), Redis rate limit, mọi module nghiệp vụ (BE02+), ChargeAssessment (chờ D01).

## 2. Cấu trúc package

Modular monolith trong `apps/api/src/lib_management/`:

```
main.py              create_app(): middleware, exception handlers, include router /api/v1
config.py            Settings (thêm biến ở mục 3)
db.py                giữ DatabaseProbe (+ kiểm revision); thêm create_session_factory()
models.py            DeclarativeBase + naming convention
migrate.py           Alembic qua code (script nằm trong wheel)
migrations/          env.py, versions/0001_identity.py, 0002_platform.py
cli.py               migrate, downgrade, seed-rbac, bootstrap-admin
core/
  errors.py          AppError + subclass, exception handlers → ErrorResponse
  request_id.py      middleware X-Request-ID, contextvar
  uow.py             UnitOfWork (context manager sở hữu Session/commit/rollback)
  pagination.py      encode/decode cursor, Page[T]
  idempotency.py     begin/complete theo idempotency_record
  audit.py           record(session, ...) ghi audit_log
  outbox.py          publish(session, ...) ghi outbox_event
platform/
  models.py          AuditLog, IdempotencyRecord, OutboxEvent, Job
identity/
  models.py          Account, Role, Permission, AccountRole, RolePermission
  repository.py      truy vấn account/permission, không commit
  rbac_seed.py       39 permission + 5 role mặc định
  service.py         seed_rbac, bootstrap_account (dùng bởi CLI)
  auth.py            JwtVerifier, dependency current_account / require_permission
  schemas.py         AccountView, AuthContext (Pydantic)
  router.py          GET /auth/me
worker/
  __main__.py        vòng lặp chính (python -m lib_management.worker)
  dispatcher.py      outbox → job
  runner.py          claim/lease/retry
  registry.py        allowlist consumer + handler
apps/api/alembic.ini  (lối vào dev: `uv run --locked alembic …`)
```

Quy tắc bắt buộc (theo [kiến trúc](../design/system-architecture.md)):

- Route có DB dùng `def` (sync). Không gọi DB đồng bộ trong `async def`. Health probe giữ đường async riêng.
- Router → service → repository. Service mở **một** UoW cho cả lệnh, commit một lần; lỗi thì rollback toàn bộ. Repository không bao giờ `commit()`.
- Module khác gọi service/query công khai của module sở hữu, không sửa bảng của module khác.
- Không `Base.metadata.create_all()` ở bất kỳ đâu ngoài test.

## 3. Cấu hình và dependency

Thêm vào `Settings` (env, không prefix, giống biến DB hiện có):

| Biến | Mặc định | Ghi chú |
| --- | --- | --- |
| `OIDC_ISSUER` | trống | VD local `http://localhost:8080/realms/lib-management`. Trống thì route cần token trả 503 `SERVICE_UNAVAILABLE` (fail closed); health vẫn chạy |
| `OIDC_AUDIENCE` | `lib-management-api` | |
| `OIDC_JWKS_URL` | `{OIDC_ISSUER}/protocol/openid-connect/certs` | |
| `OIDC_CLOCK_SKEW_SECONDS` | `30` | |
| `IDEMPOTENCY_TTL_HOURS` | `24` | Mặc định kế hoạch, có thể đổi |
| `WORKER_LEASE_SECONDS` | `60` | |
| `WORKER_MAX_ATTEMPTS` | `5` | |

Dependency mới (khóa bằng `uv.lock`, cập nhật trong PR đầu dùng tới): `alembic`, `pyjwt[crypto]`. Test sinh khóa RSA bằng `cryptography` (đi kèm `pyjwt[crypto]`); không thêm thư viện mock HTTP — JWKS giả được inject qua constructor `JwtVerifier`.

Không ghi secret vào `.env.example`; chỉ thêm tên biến với giá trị mẫu không nhạy cảm.

## 4. Schema và migration

Cột, kiểu, NULL, UQ đúng như [database-design.md](../design/database-design.md) mục 12–16 và 31–33, 35. Bảng snake_case số ít; UUID sinh phía server (`uuid.uuid4()` ở Python, không cần extension); `created_at timestamptz NOT NULL DEFAULT now()`. Enum lưu `varchar` + `CHECK (... IN (...))`, không dùng PG ENUM. FK mặc định `RESTRICT`, không cascade.

| Revision | Nội dung |
| --- | --- |
| `0001_identity` | `account` (UQ `issuer,subject`; `reader_id uuid NULL UNIQUE`; CHECK status ACTIVE/LOCKED/DISABLED; `auth_version integer NOT NULL DEFAULT 1`), `role` (UQ code), `permission` (UQ code), `account_role` (PK ghép, FK `granted_by` → account), `role_permission` (PK ghép) |
| `0002_platform` | `audit_log` (CHECK actor_type USER/SYSTEM/ANONYMOUS, outcome SUCCESS/DENIED/FAILED; index `(target_type,target_id,created_at)`), `idempotency_record` (UQ `actor_id,operation,key`; CHECK state PENDING/COMPLETED; `payload_hash char(64)`), `outbox_event` (partial index `created_at` WHERE `processed_at IS NULL`), `job` (UQ `dedupe_key`; CHECK status QUEUED/RUNNING/SUCCEEDED/FAILED/DEAD; CHECK `attempt >= 0`; index `(status,next_attempt_at,lease_until)`) |

Lưu ý:

- **`account.reader_id` chưa có FK** vì bảng `reader` thuộc BE04. Migration đầu tiên của BE04 thêm `FOREIGN KEY (reader_id) REFERENCES reader(id)`. Ghi chú này vào docstring migration 0001.
- `audit_log` append-only: service chỉ INSERT. Quyền DB riêng cho bảng này thuộc việc tách DB role production (chưa làm ở M0).
- Mỗi migration có `downgrade()` chạy được trên DB trống.
- Readiness: ngoài `SELECT 1`, so `SELECT version_num FROM alembic_version` với head của script directory (đọc lúc startup). Lệch hoặc chưa có bảng → 503 `{"status":"not_ready"}`. Không thay đổi schema phản hồi health.
- Script migration nằm trong package (`lib_management/migrations`) để image production chạy được `python -m lib_management.cli migrate`. Dev dùng thêm `alembic.ini` ở `apps/api`.
- Compose (`compose.yaml`): service one-shot `migrate` chạy `python -m lib_management.cli migrate`; `api` và `worker` `depends_on: migrate: condition: service_completed_successfully`. Dev Container: chạy tay `uv run --locked alembic upgrade head`.
- `alembic check` (CI) bảo đảm model ORM khớp migration.

## 5. Hợp đồng HTTP chung

### 5.1 Tiền tố và đặt tên

- Route nghiệp vụ dưới `/api/v1`. Health giữ `/health/*`.
- `operation_id` của route phải trùng `operationId` trong `openapi.json` (VD `get_auth_me`).
- Request command camelCase; response entity snake_case (theo [api-contract](../design/api-contract.md)). Datetime UTC RFC3339. Tiền là chuỗi số nguyên (áp dụng từ BE05).

### 5.2 Lỗi

Mọi lỗi trả `ErrorResponse`:

```json
{"code": "PERMISSION_DENIED", "message": "Thiếu quyền catalog.write", "details": [], "request_id": "…"}
```

| HTTP | `code` (M0) | Khi nào |
| --- | --- | --- |
| 401 | `INVALID_TOKEN` | Thiếu/sai Bearer, chữ ký, iss, aud, exp, nbf, kid |
| 403 | `ACCOUNT_NOT_LINKED` | Token hợp lệ nhưng không có Account (issuer, subject); không JIT |
| 403 | `ACCOUNT_INACTIVE` | Account LOCKED/DISABLED |
| 403 | `PERMISSION_DENIED` | Thiếu permission |
| 404 | `NOT_FOUND` | Route/tài nguyên không có hoặc ngoài scope |
| 409 | `CONFLICT`, `IDEMPOTENCY_MISMATCH`, `IDEMPOTENCY_IN_PROGRESS` | Trùng/phiên bản/idempotency |
| 422 | `VALIDATION_ERROR` | `RequestValidationError`; `details` = `[{"loc":…, "msg":…, "type":…}]` |
| 500 | `INTERNAL_ERROR` | Lỗi không lường trước; log server có traceback, response thì không |
| 503 | `SERVICE_UNAVAILABLE` | DB/provider không sẵn sàng |

`AppError(status, code, message, details=None, headers=None)` là lớp gốc; module tự thêm `code` nghiệp vụ (VD `ELIGIBILITY_FAILED`) nhưng giữ đúng mã HTTP ở bảng trên.

### 5.3 Request ID

Middleware đọc `X-Request-ID`; chấp nhận nếu khớp `^[A-Za-z0-9-]{8,100}$`, ngược lại sinh UUID4. Lưu trong `contextvar`, trả lại ở header response, đưa vào mọi `ErrorResponse`, `audit_log.request_id` và envelope outbox.

### 5.4 Pagination

- Query: `cursor` (opaque), `limit` (default 20, min 1, max 100; ngoài khoảng → 422).
- Response: `{"data": [...], "nextCursor": "…" | null}`.
- Cursor = base64url của JSON `{"k": [<giá trị sort>…], "id": "<uuid>"}`; mặc định sort `(created_at, id)`. Cursor sai định dạng → 422 `VALIDATION_ERROR`. Truy vấn dùng keyset (`WHERE (created_at, id) > (:c, :id)`), không OFFSET.

### 5.5 Idempotency

Header `Idempotency-Key` (1–128 ký tự) cho lệnh được đánh dấu idempotent (mượn, trả, thu, duyệt… — dùng từ BE05+; M0 cung cấp helper và test).

```python
result = idempotency.begin(uow.session, actor_id, operation, key, payload)
if result.replay:            # đã COMPLETED, cùng hash
    return result.response
... # làm nghiệp vụ trong cùng UoW
idempotency.complete(uow.session, result.record, status_code, body)
uow.commit()
```

- `payload_hash` = SHA-256 hex của `json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`.
- `begin` INSERT `PENDING` với `expires_at = now + IDEMPOTENCY_TTL_HOURS`. Va chạm UQ → đọc bản ghi:
  - khác hash → 409 `IDEMPOTENCY_MISMATCH`;
  - cùng hash, `COMPLETED` → replay `response_status`/`response_body`;
  - cùng hash, `PENDING` → 409 `IDEMPOTENCY_IN_PROGRESS` + `Retry-After: 1`.
- Bản ghi `PENDING` commit cùng kết quả nghiệp vụ; nếu lệnh lỗi, rollback xóa luôn bản ghi nên client retry được.
- `response_body` phải đã redaction (không token/PII thừa). Bản ghi hết hạn được dọn bằng job định kỳ (phase sau); M0 coi bản ghi hết hạn như không tồn tại.

### 5.6 Audit

`audit.record(session, actor, action, target_type, target_id, outcome, permission_code=None, metadata={})` — ghi trong UoW của lệnh. `metadata` là before/after đã redaction. Lần từ chối quyền (`DENIED`) ghi bằng session riêng commit ngay, vì transaction chính không chạy.

## 6. Xác thực và phân quyền (F16)

### 6.1 Keycloak local

- Service `keycloak` trong `.devcontainer/compose.yaml`: `quay.io/keycloak/keycloak:26.8.0` pin digest, lệnh `start-dev --import-realm --hostname=http://localhost:8080 --hostname-backchannel-dynamic=true`, cổng `127.0.0.1:8080`, dữ liệu dev trong volume riêng. Mật khẩu admin do `prepare.py` sinh vào `.devcontainer/.env`. API trong workspace dùng `OIDC_ISSUER=http://localhost:8080/...` (khớp `iss` trình duyệt thấy) và `OIDC_JWKS_URL=http://keycloak:8080/...` (mạng nội bộ). Keycloak dùng storage riêng, không dùng credential DB ứng dụng. Đây chỉ là môi trường phát triển.
- Realm import `.devcontainer/keycloak/lib-management-realm.json`:
  - realm `lib-management`; `registrationAllowed=false`;
  - public client `lib-management-web`: standard flow, PKCE `S256`, tắt implicit và direct access grant, redirect/origin chính xác `http://localhost:5173/*` (không wildcard rộng hơn);
  - audience mapper thêm `lib-management-api` vào `aud` của access token;
  - access token lifespan 300s;
  - client `lib-management-dev-cli` (**chỉ realm dev**): public, chỉ bật direct access grant để lấy token thử khi chưa có frontend.
- Script `.devcontainer/keycloak/create_dev_users.py` tạo user thử (`librarian.dev`, `manager.dev`, `admin.dev`, `ops.dev`, `reader.dev`) qua Admin REST API, mật khẩu đọc từ `.devcontainer/.env` (`KEYCLOAK_DEV_USER_PASSWORD`); `--link` gọi `bootstrap-admin` để tạo Account + role tương ứng. Không commit mật khẩu, không đưa user vào realm JSON.
- Cách lấy token thử ghi trong `.devcontainer/README.md`.

### 6.2 Kiểm tra JWT

`JwtVerifier(issuer, audience, jwks_client, leeway)`:

1. Header `Authorization: Bearer <jwt>`; thiếu → 401.
2. Lấy key theo `kid` từ JWKS (cache trong process). `kid` lạ → refresh JWKS **một lần**; vẫn không có → 401.
3. `jwt.decode(algorithms=["RS256"], issuer=…, audience=…, leeway=30, options={"require": ["exp", "iat", "iss", "sub", "aud"]})`. Không thử issuer khác.
4. Trả `TokenClaims(issuer, subject)`; không đọc `realm_access`/role trong token.

### 6.3 Account và permission

- `current_account` (dependency FastAPI): verify token → `SELECT account WHERE issuer=:iss AND subject=:sub` → không có: 403 `ACCOUNT_NOT_LINKED`; `status != 'ACTIVE'`: 403 `ACCOUNT_INACTIVE`. Kiểm tra mỗi request (khóa Account có hiệu lực ngay cả khi JWT còn hạn).
- `require_permission(code)` → dependency trả `Principal(account, permissions: frozenset[str])`. Permission tính mỗi request:

  ```sql
  SELECT DISTINCT p.code FROM account_role ar
  JOIN role_permission rp ON rp.role_id = ar.role_id
  JOIN permission p ON p.id = rp.permission_id
  WHERE ar.account_id = :account_id
  ```

  Thiếu → 403 `PERMISSION_DENIED`, audit `DENIED`. Không cache quyền qua request ở M0 (thu hồi role phản ánh ngay).
- Scope "own" (độc giả chỉ xem dữ liệu của mình) **không** phải permission; service module sẽ lọc theo `account.reader_id` và trả 404 khi ngoài scope.

### 6.4 `GET /api/v1/auth/me`

- `operationId: get_auth_me`; chỉ cần Bearer hợp lệ + Account ACTIVE (`x-account-guard=ACTIVE`), không cần permission.
- 200 → `AuthContext`:

  ```json
  {"account": {"id": "…", "reader_id": null, "display_name": "Thủ thư A", "status": "ACTIVE"},
   "permissions": ["catalog.read", "catalog.write", "loan.checkout"]}
  ```

  `permissions` sắp xếp tăng dần, không trùng. Không trả issuer/subject/auth_version.
- Lỗi: 401/403 như mục 5.2.

### 6.5 Seed RBAC và bootstrap

`python -m lib_management.cli seed-rbac` — idempotent (upsert theo `code`), chạy trong một transaction, in diff. Không chạy tự động trong startup/migration. Bảng dưới lấy các ô mặc định "Có/Own/Có giới hạn" của [ma trận quyền](../design/permission-matrix.md); ô "cấp thêm rõ"/"không mặc định" **không** gán.

| Role code | Tên | Permission |
| --- | --- | --- |
| `READER` | Độc giả | catalog.read, reader.read, eligibility.read, reservation.read, reservation.create, reservation.cancel, finance.read, notification.read, preference.write |
| `LIBRARIAN` | Thủ thư | catalog.read, catalog.write, media.write, reader.read, reader.write, card.issue, eligibility.read, loan.checkout, return.create, loan.renew, reservation.read, reservation.create, reservation.cancel, reservation.pickup, finance.read, assessment.propose, payment.collect, report.read, overdue.read, account.provision_reader, acquisition.write |
| `MANAGER` | Quản lý | catalog.read, reader.read, eligibility.read, finance.read, assessment.decide, charge.waive, ledger.reverse, report.read, overdue.read, export.create, export.download, policy.write, policy.approve, acquisition.approve, copy.dispose |
| `SYSTEM_ADMIN` | Admin hệ thống | catalog.read, account.provision_reader, account.manage, role.manage |
| `OPS_ADMIN` | Admin vận hành | catalog.read, backup.create, restore.request, restore.approve, job.read, job.replay |

Toàn bộ 39 permission code trong ma trận đều được tạo (kể cả mã chưa gán role). Danh sách code được giữ ở một hằng số Python duy nhất (`identity/rbac_seed.py`) và có test so khớp với tập `x-permission` trong `openapi.json` + `assessment.propose`.

`python -m lib_management.cli bootstrap-admin --issuer … --subject … --display-name … --role SYSTEM_ADMIN` (lặp `--role` được): tạo/cập nhật Account ACTIVE và gán role; `granted_by` = chính account đó cho lần đầu; audit `actor_type=SYSTEM`. Lệnh vận hành, không có endpoint tương ứng.

## 7. Outbox và worker

### 7.1 Ghi sự kiện

`outbox.publish(session, aggregate_type, aggregate_id, event_type, data) -> UUID` ghi `outbox_event` trong UoW nghiệp vụ, `payload` là envelope v1 theo [event-job-contracts](../design/event-job-contracts.md):

```json
{"schemaVersion": 1, "eventId": "<outbox_event.id>", "eventType": "loan.item.returned.v1",
 "occurredAt": "2026-11-03T02:00:00Z", "requestId": "…", "aggregateType": "loan_item",
 "aggregateId": "…", "data": {…}}
```

Không ghi email/secret/raw CSV vào payload.

### 7.2 Process worker

`python -m lib_management.worker` (service `worker` trong Compose dev, cùng image API), vòng lặp poll 1s, dừng sạch khi SIGTERM.

**Dispatcher** (mỗi vòng, batch ≤ 50):

```sql
SELECT … FROM outbox_event WHERE processed_at IS NULL
ORDER BY created_at, id FOR UPDATE SKIP LOCKED LIMIT 50
```

Với mỗi event, mỗi consumer khai báo trong `registry.py` cho `event_type` đó: `INSERT INTO job (…, dedupe_key='<eventId>:<consumer>', status='QUEUED') ON CONFLICT (dedupe_key) DO NOTHING`; rồi `processed_at = now()`; commit. `processed_at` nghĩa là đã tạo job, không phải đã gửi.

**Runner**:

1. Claim (transaction ngắn):

   ```sql
   SELECT … FROM job
   WHERE (status = 'QUEUED' AND (next_attempt_at IS NULL OR next_attempt_at <= now()))
      OR (status = 'RUNNING' AND lease_until < now())
   ORDER BY created_at, id FOR UPDATE SKIP LOCKED LIMIT 1
   ```

   → `status='RUNNING', lease_owner=<hostname:pid>, lease_until=now()+60s, attempt=attempt+1`; commit.
2. Chạy handler **ngoài** transaction (không giữ khóa khi gọi mạng). Job dài gia hạn lease mỗi 20s.
3. Kết quả (transaction mới, chỉ cập nhật khi `lease_owner` còn là mình):
   - thành công → `SUCCEEDED`, xóa lease;
   - lỗi tạm và `attempt < 5` → `QUEUED`, `next_attempt_at = now() + min(2^(attempt-1), 60)s + jitter(0–25%)`, `last_error_code`;
   - lỗi tạm và `attempt >= 5`, hoặc lỗi vĩnh viễn → `DEAD` + audit `FAILED` actor_type SYSTEM.
   `last_error_code` là mã ngắn, không chứa secret/stacktrace.

`registry.py` là allowlist: `job_type` không có handler → `DEAD` với `UNKNOWN_JOB_TYPE`. M0 chỉ đăng ký `noop.v1` (cho test) — handler thật thêm ở module sau. Trạng thái `FAILED` để dành cho lỗi terminal có quyền replay (phase 2, F23/F24).

## 8. Kế hoạch PR

Mỗi PR: nhánh `feature/<task-id>-<tên>`, Conventional Commit, mô tả nêu task ID, phụ thuộc, thay đổi schema/API, ca kiểm thử, giới hạn xác minh ([quy trình team](../operations/team-development.md)).

| PR | Task | Nội dung | Nghiệm thu (test tự động) |
| --- | --- | --- | --- |
| 1 | BE00.2, INT00.1 | `core/errors`, `request_id`, `uow`, session factory, router `/api/v1` rỗng; Alembic init (chưa bảng); readiness kiểm revision; service `migrate` | 404 route lạ và 422 query sai trả `ErrorResponse` có `request_id` trùng header; X-Request-ID hợp lệ được giữ, không hợp lệ bị thay; UoW lỗi giữa lệnh → không dòng nào được ghi (PG); readiness 503 khi revision lệch |
| 2 | BE00.1 | Model + migration `0001_identity`, `0002_platform` | `upgrade head → downgrade base → upgrade head` trên DB trống; UQ/CHECK từ chối dữ liệu sai (issuer+subject trùng, status lạ, attempt âm, dedupe_key trùng) |
| 3 | BE00.3 | `idempotency`, `audit`, `outbox`, `worker` | cùng key cùng payload → replay đúng body; khác payload → 409 MISMATCH; đang PENDING → 409 + Retry-After; lệnh lỗi → không còn bản ghi idempotency; dispatcher chạy 2 lần không tạo job trùng; 2 runner song song không claim trùng job; lease hết hạn được nhận lại; job lỗi 5 lần → DEAD; job_type lạ → DEAD |
| 4 | BE01.1 | Keycloak dev + realm + script user; `JwtVerifier`; `rbac_seed.py`; CLI `seed-rbac`, `bootstrap-admin` | JWT ký bằng khóa test: hợp lệ → claims; sai iss, sai aud, hết hạn (> 30s), nbf tương lai, alg HS256/none, kid lạ (refresh 1 lần) → 401; seed chạy 2 lần không đổi dữ liệu; tập permission khớp OpenAPI |
| 5 | BE01.2, INT00.3 | `current_account`, `require_permission`, `GET /api/v1/auth/me`; test drift OpenAPI; đổi `x-status` của `/api/v1/auth/me` thành `implemented` trong `openapi.json` | không có Account → 403 ACCOUNT_NOT_LINKED (không tạo Account); LOCKED với JWT còn hạn → 403; gỡ role → request kế tiếp mất permission; `/auth/me` khớp schema `AuthContext`; drift: mọi operation `x-status=implemented` có trong runtime với cùng path/method/operationId/mã status 2xx |

PR 1–3 có thể làm song song với PR 4 (Keycloak/verifier không cần bảng). PR 5 cần PR 2 và PR 4.

## 9. Kiểm thử và CI

- Theo pattern hiện có ở `apps/api/tests/`: unit test không DB chạy mặc định; integration nằm ở `tests/integration/`, gated `RUN_DB_INTEGRATION=1` như `tests/test_db_integration.py`. Fixture PG tạo schema bằng migration (không `create_all`) và truncate giữa test.
- Test HTTP dùng `create_app(settings)` + `TestClient`, inject `JwtVerifier` giả qua `app.dependency_overrides` hoặc settings.
- CI (`.github/workflows/ci.yml`, job `quality`): thêm bước migration round-trip trước integration tests; tách tệp integration mới bằng marker hoặc thư mục `tests/integration/` và cập nhật lệnh `--ignore` tương ứng. Giữ ruff, ruff format, mypy strict.
- Sau PR 5: cập nhật AT16 trong [acceptance-matrix](../quality/acceptance-matrix.md) kèm link CI run; BE00/BE01/INT00 trong [mục lục kế hoạch](../plan/README.md) chỉ đổi trạng thái khi PR merge.

Kiểm tra local trong Dev Container (từ `apps/api`):

```bash
uv sync --locked --group dev
uv run --locked alembic upgrade head
uv run --locked ruff check . && uv run --locked ruff format --check . && uv run --locked mypy src
uv run --locked pytest
RUN_DB_INTEGRATION=1 uv run --locked pytest tests/test_db_integration.py tests/integration
uv run --locked python -m lib_management.cli seed-rbac
```

Smoke thủ công sau PR 5: lấy token từ Keycloak dev → `curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/v1/auth/me` → 200 sau `bootstrap-admin`, 403 `ACCOUNT_NOT_LINKED` trước đó.

## 10. Điểm mở

| Mã | Nội dung | Ảnh hưởng M0 |
| --- | --- | --- |
| D01 | SQL type/độ rộng ChargeAssessment.kind/status, NOT NULL version/created_at | Không; chặn BE05 |
| N03–N07 | Các điểm mở trong thiết kế (N05: APPROVED tiếp nhận) | Không |
| — | Version/digest Keycloak | Chọn khi làm PR 4 |
| — | Hosting production, DB role tách quyền ghi audit_log | Không; trước deployment |
| — | TTL idempotency 24h, lease 60s, retry 5 lần | Mặc định cấu hình; xem lại theo workload |

## 11. Kết quả triển khai

Ghi nhận ngày 2026-11-03 trên máy macOS, PostgreSQL 17 container tạm và Keycloak 26.8.0 container tạm. Đây là bằng chứng local; CI GitHub chưa chạy cho tới khi mở PR.

- Unit: 59 pass (ruff, ruff format, mypy strict sạch). Integration trên PostgreSQL 17: 43 pass.
- Migration round trip `upgrade head → downgrade base → upgrade head` và `alembic check` sạch; image production chạy `python -m lib_management.cli migrate` được.
- E2E với Keycloak thật: realm import, tạo 5 user dev, `--link` tạo Account; token qua `lib-management-dev-cli` có `aud=lib-management-api`; `GET /api/v1/auth/me` trả 200 với quyền từ DB; token bị sửa → 401; client `lib-management-web` từ chối password grant.
- Worker chạy job `noop.v1` → SUCCEEDED và dừng sạch khi nhận SIGTERM.
