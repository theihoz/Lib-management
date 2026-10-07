# syntax=docker/dockerfile:1
# Build context MUST be the repository root; apps/api has its own lockfile.
FROM node:24.21.0-bookworm-slim AS deps
WORKDIR /app
COPY apps/api/package.json apps/api/package-lock.json ./
RUN npm ci

FROM deps AS dev
COPY --chown=node:node apps/api/ .
RUN chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM deps AS build
COPY apps/api/ .
RUN npm run build

FROM node:24.21.0-bookworm-slim AS prod-deps
WORKDIR /app
COPY apps/api/package.json apps/api/package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force

FROM node:24.21.0-bookworm-slim AS production
WORKDIR /app
ENV NODE_ENV=production PORT=3000 TZ=Asia/Ho_Chi_Minh
COPY --from=prod-deps --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
COPY --from=prod-deps --chown=node:node /app/package.json ./package.json
USER node
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=3 CMD node -e "fetch('http://127.0.0.1:3000/health/ready',{signal:AbortSignal.timeout(2500)}).then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"
CMD ["node", "dist/main.js"]
