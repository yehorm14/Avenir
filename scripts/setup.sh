#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

for command_name in node npm; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Install Node 20 or newer, including npm, then run this script again.\n' >&2
    exit 1
  fi
done
node -e 'if (Number(process.versions.node.split(".")[0]) < 20) { console.error("Node 20 or newer is required."); process.exit(1); }'

if [[ ! -d .venv ]]; then
  setup_python="${AVENIR_SETUP_PYTHON:-}"
  if [[ -z "$setup_python" ]]; then
    for candidate in python3.14 python3.13 python3.12 python3; do
      if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 12))' 2>/dev/null; then
        setup_python="$candidate"
        break
      fi
    done
  fi
  if [[ -z "$setup_python" ]]; then
    printf 'Install Python 3.12 or newer, or set AVENIR_SETUP_PYTHON to its executable.\n' >&2
    exit 1
  fi
  "$setup_python" -m venv .venv
fi
venv_python=.venv/bin/python
[[ -x $venv_python ]] || venv_python=.venv/Scripts/python.exe
if [[ ! -x $venv_python ]]; then
  printf 'The existing .venv has no usable Python executable. See the manual setup in README.md.\n' >&2
  exit 1
fi
"$venv_python" -c 'import sys; assert sys.version_info >= (3, 12), "The existing .venv requires Python 3.12 or newer; see README.md."'
"$venv_python" -m pip install -e '.[dev]'
npm --prefix apps/web ci
npm --prefix apps/web run build
bash scripts/check-setup.sh
printf '\nStart Avenier: node scripts/run-app.mjs --production\n'
