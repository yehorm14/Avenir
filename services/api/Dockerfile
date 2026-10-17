# Build from the repo root: docker build -f services/api/Dockerfile .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    AVENIR_SNAPSHOT_DIR=/app/snapshots \
    PATHFINDER_ML_DIR=/app/snapshots/ml

WORKDIR /app

COPY pyproject.toml ./
COPY packages/contracts packages/contracts
COPY packages/decision packages/decision
COPY packages/adapters packages/adapters
COPY packages/etl packages/etl
COPY packages/ml packages/ml
COPY services/api services/api

# Non-editable install. Snapshots are not baked in; compose mounts them read-only.
RUN pip install --no-cache-dir .

# pathfinder_ml falls back to <site-packages>/../../snapshots/ml/mock for its mock files
# when installed; point that location at the mounted snapshots so mock mode still works.
RUN python -c "import pathlib, pathfinder_ml.api as a; a._REPO_ROOT.joinpath('snapshots').symlink_to('/app/snapshots')"

EXPOSE 8000
CMD ["uvicorn", "avenir_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
