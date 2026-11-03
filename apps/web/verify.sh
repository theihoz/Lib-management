#!/usr/bin/env bash
# Full frontend verification. Needs Node 24 + npm (Dev Container). Run from apps/web.
set -euo pipefail
npm ci
npm run gen:api                 # regenerates schema.d.ts from docs/design/openapi.json
npm run format                  # new files were written without running prettier
npm run lint
npm run typecheck
npm test
npm run build
# Production bundle must not contain design fixtures or sample data.
if grep -rIl --include='*.js' -e 'minh họa' -e 'DesignBrowser' -e 'fixtureFor' dist; then
  echo "FAIL: demo markers found in dist" >&2; exit 1
fi
echo "OK"
