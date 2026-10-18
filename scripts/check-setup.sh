#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

if ! command -v node >/dev/null 2>&1 || [[ ! -x .venv/bin/python ]] || [[ ! -d apps/web/node_modules ]] || [[ ! -f apps/web/dist/index.html ]]; then
  printf 'Setup is incomplete. Run: bash scripts/setup.sh\n' >&2
  exit 1
fi
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) { console.error("Node 20 or newer is required."); process.exit(1); } console.log(`Node ${process.versions.node}: ready`);'
node --check scripts/run-app.mjs
.venv/bin/python - <<'PY'
import sys
from pathlib import Path

assert sys.version_info >= (3, 12), "Python 3.12 or newer is required"
sys.path.insert(0, str(Path.cwd() / "apps/web"))
from api.application import app
from pathfinder_ml import ML

paths = set(app.openapi()["paths"])
required = {"/health", "/api/bootstrap", "/api/catalogue", "/api/discovery", "/api/v1/recommendations"}
assert required <= paths, f"Missing application routes: {sorted(required - paths)}"
evidence = ML()
occupations = evidence.occupations()
assert occupations, "Occupation evidence is missing"
assert len(evidence.occupations(demo_only=True)) > 0, "Matching evidence is missing"
assert evidence.status()["mode"] == "real", "Expected the committed real evidence, not a fallback"
print(f"Python {sys.version.split()[0]}: application imports and both API layers ready")
print(f"Evidence: {len(occupations)} occupations; built frontend present")
PY
printf 'Setup check passed. No server started or external provider contacted.\n'
