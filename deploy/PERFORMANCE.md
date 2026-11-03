# Performance and deployment runbook

## Implemented behavior and limits

SQLAlchemy already supplied connection pooling; it now has explicit bounded
limits, a checkout deadline, stale-connection checks and recycling. API responses
of at least 1024 bytes use gzip when accepted. Business API responses carry
`Cache-Control: private, no-store` because every business route requires RBAC.

`PublicReadCache` is an optional process-local TTL/LRU memoizer for **public,
non-PII computations**. It bounds entry count, copies mutable results, leaves
failures uncached, and invalidates in-flight writes. It is deliberately unused
by authenticated endpoints. Do not cache reader records, loans, sessions,
permission checks or authorization-dependent catalog results. It does not
coordinate invalidation across replicas. Callers must also bound value size.

The standalone configuration prepares two API replicas behind Nginx, one
migration job, a worker and an isolated PostgreSQL service. It uses its own
Compose project/volume; the root `compose.yaml` is unchanged. Only the web proxy
binds a host port, on `127.0.0.1:8088` by default. PostgreSQL has no host port and
uses an internal network. APIs also join the edge network to fetch OIDC keys.

These files prepare a **local deployment preview**. They do not provision a
cloud CDN, domain, TLS certificate, managed database or production load balancer.
Nginx provides passive failure detection. Compose readiness checks gate startup,
but do not actively remove a running-but-unready replica from Nginx. One proxy
on one host is not highly available.

## Start the preview on a Docker-equipped host

Requires Docker Engine with Compose v2 and an OIDC issuer reachable from both
the browser and API containers. Set `POSTGRES_PASSWORD` and `OIDC_ISSUER` in the
root `.env`. `OIDC_JWKS_URL` is optional with the existing Keycloak URL convention.
Configure the identity client to allow `http://localhost:8088` as its web origin
and appropriate redirect URLs. `localhost` inside an API container is that
container, so use a reachable identity hostname for API issuer/JWKS settings.

Copy `deploy/runtime-config.example.json` to `deploy/runtime-config.local.json`
and set its public OIDC settings to match the identity client. Keep `apiBaseUrl`
empty for same-origin requests and `mock` false. This JSON never holds secrets.
Run from the repository root:

```sh
export RUNTIME_CONFIG_FILE=./runtime-config.local.json
docker compose --env-file .env -f deploy/compose.performance.yaml config --quiet
docker compose --env-file .env -f deploy/compose.performance.yaml build
docker compose --env-file .env -f deploy/compose.performance.yaml run --rm --no-deps web nginx -t
docker compose --env-file .env -f deploy/compose.performance.yaml up -d
docker compose --env-file .env -f deploy/compose.performance.yaml ps
curl --fail http://localhost:8088/health/live
curl --fail http://localhost:8088/health/ready
```

Migrations run once before API/worker startup, never independently per replica.
Preview data persists in the preview project's volume when containers stop.
This is a preview stack, not a migration procedure for an existing database.

The web image uses Node 24 and Nginx 1.28. Release CI should record approved
image digests before a production rollout; the existing API and PostgreSQL
images are already digest pinned.

## Connection budget

| Variable | Default | Effect per API/worker process |
| --- | --- | --- |
| `DB_POOL_SIZE` | `5` | Retained connections, opened lazily |
| `DB_POOL_MAX_OVERFLOW` | `5` | Additional transient connections |
| `DB_POOL_TIMEOUT_SECONDS` | `2` | Maximum connection checkout wait |
| `DB_POOL_RECYCLE_SECONDS` | `1800` | Replace old connections on checkout |

Configuration rejects SQLAlchemy's unlimited values (`pool_size=0`, negative
overflow), nonpositive deadlines and nonfinite timeouts. Pre-ping and LIFO reuse
handle stale idle connections. Existing two-second connect and SQL statement
deadlines remain in force. Budget for every process:

```text
sum(processes × (pool size + overflow))
+ readiness-probe connections + migration/admin headroom
< PostgreSQL available connection capacity
```

Two single-worker APIs and one worker allow up to 30 pooled connections at these
defaults. Each API readiness probe separately allows up to four unpooled checks;
reserve up to eight more connections plus operational headroom. More Uvicorn
workers multiply pools. Include other database clients in the budget.

Inspect `pg_stat_activity`, checkout wait, database CPU and request p95/p99 under
representative concurrent load before raising limits. Pool exhaustion should
fail within the configured checkout deadline. More connections do not fix slow
SQL. Validate query/index choices with `EXPLAIN (ANALYZE, BUFFERS)` on disposable
or approved staging data before attributing a speedup to an index.

## Cache/CDN and proxy policy

| URL/data | Policy |
| --- | --- |
| Existing content-hashed `/assets/*-<hash>.*` | `public, max-age=31536000, immutable` for configured JS/CSS/font/image types |
| Missing hashed asset | Real 404 without immutable header |
| Unhashed assets and HTML/navigation | `no-cache`, revalidate |
| `/config.json` | `no-store` |
| `/api`, `/api/*`, `/health/*`, `/openapi.json` through proxy | `private, no-store`; proxy cache off |
| Public server computations | Explicit helper with bounded TTL; no business consumer |

After a provider/account, domain and deployment target are selected, put a CDN
in front of content-hashed assets. Preserve origin cache headers and
`Vary: Accept-Encoding`. Explicitly bypass shared caching for API, health,
config, authorization and cookie-bearing traffic. Retain old hashed assets during
rollouts so already-open pages can still load older lazy chunks. HTML/config
must reflect new releases promptly.

Nginx compresses static text; the API compresses API responses. Nginx uses
least-connections balancing, connection keepalive, Docker DNS re-resolution and
passive failure windows. Retry mode for non-idempotent requests stays disabled.
On a disposable preview, stop one API replica after warmup, verify liveness and
an authorized read still succeed, then restart it. Check real authenticated
mutation behavior separately.

Before public hosting, select TLS termination, trusted forwarding headers, real
identity URLs, backups and a multi-host availability plan. The proxy currently
reports its own HTTP scheme; an external TLS edge needs a deliberate trusted
forwarded-header setup. No cloud service was created by these changes.

## Measure, then compare

Audit production builds with identical datasets, viewport, network/CPU throttle
and auth state. A logged-out shell or mock-mode audit does not measure the
complete authenticated backend flow. Record that state beside every report.

```sh
cd apps/web
npm ci
npm run build
npm run preview -- --host 127.0.0.1
# Separate terminal; Chrome/Chromium must be available to Lighthouse.
npx lighthouse http://127.0.0.1:4173/catalog \
  --output=html --output=json --output-path=/tmp/lib-management-lighthouse \
  --chrome-flags='--headless --no-sandbox'
```

Review LCP, CLS, INP/TBT, transfer size, unused JS/CSS, lazy chunks and blocking
resources. Compare at least three equivalent runs and report medians. A single
local run is a snapshot, not a production SLA. Inspect browser Network requests
for query-cache reuse, search debouncing, mutation invalidation and session
isolation. Measure API p95 and pool checkout pressure separately from asset load.

## Verification status

Executable Python regressions cover pool exhaustion/release, settings validation,
compression/private API headers, TTL/LRU eviction, defensive copies, failed
computations and invalidation during in-flight work. Authenticated business
responses remain uncached.

Nginx 1.28 syntax validation passed using an official temporary Debian ARM64
binary. A real local proxy smoke test with two disposable HTTP fixture backends
verified asset gzip/Vary, immutable hash caching, missing-asset 404s, HTML/config
policy, API/OpenAPI no-store, balancing across both replicas and GET failover
after stopping one backend. Only listen/root/upstream paths were adapted for
that fixture; no Docker stack or production database was involved.

The Docker preview must run through the commands above on a Docker-equipped
host before it can be called deployed or load-tested. A CDN rollout, replica soak
test and production database query plans require an actual environment and
representative data.

References: [SQLAlchemy pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html),
[Nginx upstream DNS/balancing](https://nginx.org/en/docs/http/ngx_http_upstream_module.html),
[Nginx passive health checks](https://nginx.org/en/docs/http/load_balancing.html),
[Nginx proxy cache](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).

## Lighthouse

Chưa chạy. Kết quả chỉ được ghi vào đây sau khi chạy trên `vite preview` của bản build
production, kèm URL, thiết bị, phiên bản Lighthouse và ngày chạy. Không ghi số ước lượng.
