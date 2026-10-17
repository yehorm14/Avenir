#!/usr/bin/env bash
# Copy data/raw/ (and snapshots/) from this machine to the cluster checkout.
# Needs rsync: on Windows run it from WSL or Git Bash with rsync installed.
# Set CLUSTER_HOST (an ssh alias from ~/.ssh/config) and CLUSTER_PATH in .env.
# Usage: scripts/sync_to_cluster.sh [--dry-run]
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && set -a && . ./.env && set +a
: "${CLUSTER_HOST:?set CLUSTER_HOST in .env}"
: "${CLUSTER_PATH:?set CLUSTER_PATH in .env}"
DRY=""; [ "${1:-}" = "--dry-run" ] && DRY="--dry-run"
rsync -avz --partial --progress $DRY --exclude '*.part' data/raw/ "${CLUSTER_HOST}:${CLUSTER_PATH}/data/raw/"
rsync -avz --partial --progress $DRY snapshots/ "${CLUSTER_HOST}:${CLUSTER_PATH}/snapshots/"
echo "Now run 'make data-check' on the cluster and compare data/manifest.lock.json."
