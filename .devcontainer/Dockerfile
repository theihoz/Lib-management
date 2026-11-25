FROM ghcr.io/astral-sh/uv:0.13.10@sha256:a3ea1357342c1a4bf9a0c53a3deb1b55379aefa037338d8113d5771efa01774f AS uv
FROM node:24-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS node
FROM python:3.13-slim-bookworm@sha256:a1165e272e578941b84abc79e4ab38a0305cd12803a5c4247979ac7655f4d641
ARG DEVELOPER_UID=10001
ARG DEVELOPER_GID=10001
# Chromium runtime libraries and fonts so `npm run e2e` (Playwright) runs in the container.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2 libdbus-1-3 \
    libdrm2 libgbm1 libglib2.0-0 libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 \
    libxcomposite1 libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 \
    fonts-liberation fonts-noto-core \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "$DEVELOPER_GID" developer \
    && useradd --uid "$DEVELOPER_UID" --gid "$DEVELOPER_GID" --create-home --shell /bin/bash developer
COPY --from=uv /uv /usr/local/bin/uv
# Node 24 LTS for apps/web (npm ci from the committed lockfile).
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx
ENV UV_PROJECT_ENVIRONMENT=/home/developer/.venv UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never \
    PATH="/home/developer/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER developer
CMD ["sleep", "infinity"]
