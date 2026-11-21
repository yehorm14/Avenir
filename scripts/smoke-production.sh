#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
image=avenir:production-smoke
docker build --file "$root/apps/web/Dockerfile" --tag "$image" "$root"

# Keep localhost inside the container available while blocking external sources.
container="$(docker run --detach --network none "$image")"
cleanup() {
  local status=$?
  if (( status != 0 )); then
    docker logs "$container" >&2 || true
  fi
  docker rm --force "$container" >/dev/null || true
}
trap cleanup EXIT

docker exec -i "$container" python -u - <<'PY'
import json
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

base = "http://127.0.0.1:4175"


def request(path, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    with urlopen(Request(base + path, data=body, headers=headers), timeout=5) as response:
        return response.read()


def api(path, payload=None):
    response = json.loads(request(path, payload))
    assert response["ok"] is True, (path, response["error"])
    return response["data"]


for attempt in range(30):
    try:
        health = api("/health")
        break
    except URLError:
        if attempt == 29:
            raise
        time.sleep(1)

assert health["status"] == "ok", health
print("PASS /health")

shell = request("/").decode()
assert 'id="root"' in shell, "The root page did not serve the React app shell"
asset = re.search(r'<script[^>]+src="(/assets/[^"]+\.js)"', shell)
assert asset and request(asset[1]), "The built JavaScript asset could not be loaded"
print("PASS app shell and JavaScript asset")

bootstrap = api("/api/bootstrap")
origins = bootstrap["data_status"]["origins"]
assert origins and set(origins.values()) == {"real"}, origins
socs = {"2134", "2133"}  # Software development and IT business analysis
careers = {career["soc"]: career for career in bootstrap["careers"]}
for soc in socs:
    pay = careers[soc]["metrics"]["pay_median"]
    assert pay["value"] > 0 and pay["as_of"] and pay["source"], (soc, pay)
print("PASS /api/bootstrap with bundled evidence")

comparison = api("/api/matches", {"tags": [], "weights": {"pay": 50, "interest": 0, "need": 50}})
ranked = {career["soc"]: career for career in comparison["results"]}
for soc in socs:
    assert ranked[soc]["score"] is not None, ranked[soc]
    assert ranked[soc]["metrics"]["pay_median"] == careers[soc]["metrics"]["pay_median"], soc
print("PASS /api/matches with no optional keys or external network")
PY
