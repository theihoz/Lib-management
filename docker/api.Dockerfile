# Build context: repository root. Digests are multi-platform OCI indexes.
FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv
FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641 AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /app

FROM base AS deps
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY apps/api/pyproject.toml apps/api/uv.lock ./
# Cache runtime dependencies before adding the package source.
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-install-project

FROM deps AS build
COPY apps/api/src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev --no-editable && uv build --wheel --no-sources

FROM deps AS dev
COPY apps/api/src ./src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --no-dev
USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "lib_management.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app/src"]

FROM deps AS runtime-deps
COPY --from=build /app/dist /tmp/dist
RUN uv pip install --python /opt/venv/bin/python --no-deps /tmp/dist/*.whl

FROM base AS production
COPY --from=runtime-deps /opt/venv /opt/venv
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=2.5)"
CMD ["uvicorn", "lib_management.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
