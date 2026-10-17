#!/usr/bin/env bash
# Builds the frontend (if needed) and serves the whole app on http://localhost:8000
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$PWD/.conda/bin:$PATH"
if [ ! -d frontend/dist ] || [ -n "$(find frontend/src -newer frontend/dist -print -quit)" ]; then
  (cd frontend && npm install --no-audit --no-fund && npm run build)
fi
exec python -m uvicorn app.main:app --app-dir backend --port "${PORT:-8000}"
