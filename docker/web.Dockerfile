# syntax=docker/dockerfile:1
# Build context MUST be the repository root; apps/web has its own lockfile.
FROM node:24.21.0-bookworm-slim AS deps
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM deps AS dev
COPY --chown=node:node apps/web/ .
RUN chown -R node:node /app
USER node
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

FROM deps AS build
COPY apps/web/ .
# Public frontend configuration, never a secret. Proxy /api in production.
ENV VITE_API_BASE_URL=/api/v1
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.29-alpine AS production
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
USER 101
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 CMD wget -q -O /dev/null http://127.0.0.1:8080/health/live || exit 1
