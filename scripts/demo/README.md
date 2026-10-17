# Pull-the-plug rehearsal

`pull_the_plug.py` is the presenter's rehearsal tool. It talks to a running Avenir API over HTTP, prints which numbers
are `live`, `snapshot`, `mock` or `missing`, then pulls the plug on live data and shows what changed. It only reads what
the API returns; it never invents a value.

## Rehearse

```
uvicorn avenir_api.app:app --port 8000                 # terminal 1
python scripts/demo/pull_the_plug.py                   # terminal 2
```

Flags: `--base-url URL`, `--warm-only` (stop after warming the cache), `--no-toggle` (do not pull the plug),
`--timeout 5` (seconds per request), `--freeze` (any `mock` status becomes a FAIL, exit 1).

Exit codes: `0` ok (warnings allowed), `1` a FAIL line, `2` API not reachable.

On Windows, `localhost` can add about 2 s to every call (it tries IPv6 first while uvicorn listens on IPv4). If the
timings look slow, use `--base-url http://127.0.0.1:8000`.

## Run it once about 5 minutes before the pitch

That warms the API (data loaded, every career card fetched) so nothing is cold on stage. Use `--warm-only` if you
just want the warm-up and the badge table.

## What each section means for the pitch

1. **Health**: the API is up and `ml_mode` says whether the ML numbers are real, mock or mixed.
2. **Badges before**: one row per data source with its badge. This is the provenance story: "every number says where
   it came from and how fresh it is".
3. **Warm the cache**: the 20 demo careers with their live job ads count and the ads badge. Per-call timings show the
   app is quick.
4. **Amira flow**: Amira (Glasgow, maths and art, first idea architect) gets three picks, a hedge, the honesty
   notices, and whether the explanation was written by AI (`ai_written`).
5. **Pull the plug**: live data is switched off, the architect card and the badge table are fetched again, and a
   before/after table shows the change. This is the moment to say "this badge flips from live to snapshot when I pull
   the plug, and the app keeps working". Live mode is always switched back on afterwards, even if something fails.
6. **Summary**: PASS, WARN and FAIL lines. A clean rehearsal has no FAIL.

If an endpoint is not built yet, the section says "not available yet" and the run continues.

## If ads show `missing`

That is the honest answer when there is no Adzuna key and no snapshot yet. The summary says:
"no Adzuna snapshot: ads show 'missing' (run scripts/fetch/adzuna_snapshot.py with keys)".
What to say on stage: "Live job ads need an Adzuna key, so that one number shows as missing. Every other number is
from published UK data." If keys and a snapshot appear later, the same script shows `live`, then `snapshot` after the
plug is pulled, with no change to the script.
