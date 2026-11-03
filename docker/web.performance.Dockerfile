# Build context: repository root. Pin deployment image digests in release CI.
FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

# 1.28 supports open-source upstream DNS re-resolution (introduced in 1.27.3).
FROM nginx:1.28-alpine AS runtime
# compose.local.yaml swaps in the single-API configuration.
ARG NGINX_CONF=docker/nginx.performance.conf
COPY ${NGINX_CONF} /etc/nginx/nginx.conf
COPY --from=build /app/dist/ /usr/share/nginx/html/
USER nginx
EXPOSE 8080
# Skip the stock entrypoint scripts: configuration and root filesystem are read-only.
ENTRYPOINT []
CMD ["nginx", "-e", "stderr", "-g", "daemon off;"]
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/status || exit 1
