FROM ghcr.io/astral-sh/uv:0.12.23@sha256:61d393e44e249f2e4b526b6c7ddcecce245946826e608e11c93ad4f5bba55b21 AS uv
FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641
ARG DEVELOPER_UID=10001
ARG DEVELOPER_GID=10001
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "$DEVELOPER_GID" developer \
    && useradd --uid "$DEVELOPER_UID" --gid "$DEVELOPER_GID" --create-home --shell /bin/bash developer
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/home/developer/.venv UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    PATH="/home/developer/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER developer
CMD ["sleep", "infinity"]
