FROM node:20-bookworm-slim AS web-build
WORKDIR /build
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web/src ./src
COPY apps/web/public ./public
COPY apps/web/index.html apps/web/tsconfig.json apps/web/vite.config.ts ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    AVENIR_SNAPSHOT_DIR=/app/snapshots PATHFINDER_ML_DIR=/app/snapshots/ml
WORKDIR /app
COPY pyproject.toml ./
COPY packages ./packages
COPY services/api ./services/api
COPY snapshots ./snapshots
COPY apps/web/api ./apps/web/api
COPY prototypes/pathfinder-game/backend ./prototypes/pathfinder-game/backend
COPY --from=web-build /build/dist ./apps/web/dist
RUN pip install --no-cache-dir -e . && useradd --create-home avenir
USER avenir
WORKDIR /app/apps/web
EXPOSE 4175
ENV PORT=4175
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT', '4175'), timeout=3)"
CMD ["sh", "-c", "exec uvicorn api.application:app --host 0.0.0.0 --port ${PORT}"]
