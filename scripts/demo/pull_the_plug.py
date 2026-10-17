#!/usr/bin/env python
"""Pull-the-plug rehearsal harness for Avenir.

Talks to a RUNNING API over HTTP only (no avenir_api import), so it works against any server:

    uvicorn avenir_api.app:app --port 8000
    python scripts/demo/pull_the_plug.py [--base-url URL] [--warm-only] [--no-toggle] [--timeout 5] [--freeze]

It only reads what the API returns; nothing is invented. Exit codes: 0 ok (warnings allowed),
1 a FAIL line, 2 API unreachable. See scripts/demo/README.md.
"""
from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from typing import Any, Protocol

import requests

HEALTH = "/health"
SOURCES = "/api/v1/sources"
CAREERS = "/api/v1/careers"
TAGS = "/api/v1/tags"
RECS = "/api/v1/recommendations"
DEMO_LIVE = "/api/v1/demo/live"
UNPLUG_SOC = "2451"  # architects: Amira's first idea
AMIRA_TAGS = ("maths", "art_drawing", "design", "building_spaces")
STATES = {"live", "snapshot", "mock", "missing"}
UNAVAILABLE = (404, 405)
NOT_YET = "not available yet (Nazar Task 13)"
NO_SNAPSHOT = "no Adzuna snapshot: ads show 'missing' (run scripts/fetch/adzuna_snapshot.py with keys)"


class Client(Protocol):
    def get(self, path: str) -> tuple[int, Any]: ...

    def post(self, path: str, json: Any = None) -> tuple[int, Any]: ...


class RequestsClient:
    """The CLI's client: `requests` with a timeout. Body is None when the response is not JSON."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _unpack(r: requests.Response) -> tuple[int, Any]:
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, None

    def get(self, path: str) -> tuple[int, Any]:
        return self._unpack(requests.get(self.base_url + path, timeout=self.timeout))

    def post(self, path: str, json: Any = None) -> tuple[int, Any]:
        return self._unpack(requests.post(self.base_url + path, json=json, timeout=self.timeout))


# ---------- pure helpers ----------

def table(headers: list[str], rows: list[list[str]]) -> list[str]:
    widths = [max(len(str(x)) for x in col) for col in zip(headers, *rows, strict=True)]
    fmt = "  " + " | ".join(f"{{:<{w}}}" for w in widths)
    rule = "  " + "-+-".join("-" * w for w in widths)
    return [fmt.format(*headers).rstrip(), rule, *(fmt.format(*[str(c) for c in r]).rstrip() for r in rows)]


def envelope_problems(body: Any) -> list[str]:
    """What is wrong with this envelope (empty list = valid). Extra keys are tolerated."""
    if not isinstance(body, dict):
        return ["body is not a JSON object"]
    problems = [] if "ok" in body else ["missing ok"]
    meta = body.get("meta")
    if not isinstance(meta, dict):
        return [*problems, "missing meta"]
    for key in ("request_id", "as_of"):
        if not meta.get(key):
            problems.append(f"missing meta.{key}")
    for s in meta.get("sources") or []:
        if not isinstance(s, dict) or not s.get("name") or s.get("status") not in STATES:
            problems.append(f"bad meta.sources entry {s!r}")
    return problems


def source_statuses(body: Any) -> list[dict]:
    """Source status entries of an envelope's meta."""
    meta = (body or {}).get("meta") if isinstance(body, dict) else None
    return [s for s in (meta or {}).get("sources") or [] if isinstance(s, dict)]


def ads_state(card: Any) -> tuple[str, Any]:
    """(state, value) for a career card envelope. State comes from the `adzuna` entry of meta.sources
    (the last one wins: the API appends the live status), else from the ads_now Metric."""
    data = (card or {}).get("data") if isinstance(card, dict) else None
    metric = ((data or {}).get("metrics") or {}).get("ads_now") if isinstance(data, dict) else None
    value = metric.get("value") if isinstance(metric, dict) else None
    named = [s for s in source_statuses(card) if s.get("name") == "adzuna"]
    if named:
        return named[-1]["status"], value
    if not isinstance(metric, dict):
        return "missing", None
    if value is None:
        return "missing", None
    if metric.get("status") == "mock" or metric.get("source") == "MOCK":
        return "mock", value
    return f"unknown ({metric.get('status')}/{metric.get('source')})", value


def fmt_value(value: Any) -> str:
    if value is None:
        return "missing"
    return f"{value:g}" if isinstance(value, int | float) else str(value)


# ---------- the run ----------

class Run:
    def __init__(self, client: Client, out: Callable[[str], Any], freeze: bool = False) -> None:
        self.client, self.out, self.freeze = client, out, freeze
        self.passes: list[str] = []
        self.warns: list[str] = []
        self.fails: list[str] = []
        self.bad_envelopes: list[str] = []
        self.mock_names: set[str] = set()
        self.total_ms = 0.0
        self.ads_states: list[str] = []
        self.ads_by_soc: dict[str, str] = {}
        self.statuses_before: dict[str, str] = {}
        self.ads_after: str | None = None

    def say(self, *lines: str) -> None:
        for line in lines:
            self.out(line)

    def section(self, title: str) -> None:
        self.say("", f"== {title} ==")

    def call(self, method: str, path: str, json: Any = None, check: bool = True) -> tuple[int | None, Any, float]:
        """One HTTP call: (status, body, ms). A network error is recorded as a FAIL and returns (None, None, ms)."""
        t0 = time.perf_counter()
        try:
            status, body = self.client.get(path) if method == "GET" else self.client.post(path, json=json)
        except requests.RequestException as exc:
            ms = (time.perf_counter() - t0) * 1000
            self.total_ms += ms
            self.fails.append(f"{method} {path} failed: {type(exc).__name__}")
            self.say(f"  {method} {path}: request failed ({type(exc).__name__})")
            return None, None, ms
        ms = (time.perf_counter() - t0) * 1000
        self.total_ms += ms
        if check and status not in UNAVAILABLE:
            for problem in envelope_problems(body):
                self.bad_envelopes.append(f"{method} {path}: {problem}")
        self.note_mock(body)
        return status, body, ms

    def note_mock(self, body: Any) -> None:
        for s in source_statuses(body):
            if s.get("status") == "mock":
                self.mock_names.add(str(s.get("name")))

    # 1
    def health(self) -> bool:
        self.section("1. Health")
        t0 = time.perf_counter()
        try:
            status, body = self.client.get(HEALTH)  # RequestException is handled by the caller (exit 2)
        finally:
            self.total_ms += (time.perf_counter() - t0) * 1000
        data = (body or {}).get("data") if isinstance(body, dict) else None
        data = data if isinstance(data, dict) else {}
        for problem in envelope_problems(body):
            self.bad_envelopes.append(f"GET {HEALTH}: {problem}")
        self.note_mock(body)
        self.say(f"  HTTP {status}   status: {data.get('status', '?')}   ml_mode: {data.get('ml_mode', '?')}")
        up = status == 200
        (self.passes if up else self.fails).append("API up" if up else f"API unhealthy (HTTP {status})")
        return up

    # 2
    def badges(self, title: str = "2. Badges before") -> dict[str, str]:
        self.section(title)
        status, body, _ = self.call("GET", SOURCES)
        data = (body or {}).get("data") if isinstance(body, dict) else None
        statuses = [s for s in (data or {}).get("statuses") or [] if isinstance(s, dict)] if isinstance(data, dict) else []
        if status != 200 or not statuses:
            self.say(f"  sources: no statuses returned (HTTP {status})")
            if status is not None:  # a network error was already recorded as a FAIL by call()
                self.fails.append(f"sources: HTTP {status}" if status != 200 else "sources: no statuses returned")
            return {}
        rows = [[str(s.get("name")), str(s.get("status")), str(s.get("quality") or "-"), str(s.get("as_of") or "-")]
                for s in statuses]
        self.say(*table(["source", "status", "quality", "as_of"], rows))
        counts: dict[str, int] = {}
        for s in statuses:
            counts[str(s.get("status"))] = counts.get(str(s.get("status")), 0) + 1
        self.say("  counts: " + "  ".join(f"{k} {v}" for k, v in sorted(counts.items())))
        for s in statuses:
            if s.get("status") == "mock":
                self.mock_names.add(str(s.get("name")))
        return {str(s.get("name")): str(s.get("status")) for s in statuses}

    # 3
    def warm(self) -> dict[str, tuple[str, Any]]:
        self.section("3. Warm the cache")
        status, body, ms = self.call("GET", CAREERS)
        data = (body or {}).get("data") if isinstance(body, dict) else None
        if status != 200 or not isinstance(data, list):
            self.say(f"  careers: no list returned (HTTP {status})")
            if status is not None:
                self.fails.append(f"careers: HTTP {status}" if status != 200 else "careers: response is not a list")
            return {}
        socs = [str(c.get("soc2020")) for c in data if isinstance(c, dict) and c.get("soc2020")]
        if not socs:
            self.say("  careers: the list is empty")
            self.fails.append("careers: empty list (the API has no data)")
            return {}
        self.say(f"  careers list: {len(socs)} careers, {ms:.0f} ms")
        titles = {str(c.get("soc2020")): str(c.get("title")) for c in data if isinstance(c, dict)}
        rows: list[list[str]] = []
        cards: dict[str, tuple[str, Any]] = {}
        for soc in socs:
            st, card, ms = self.call("GET", f"{CAREERS}/{soc}")
            if st != 200:
                rows.append([soc, titles.get(soc, "?"), "-", f"error HTTP {st}", f"{ms:.0f}"])
                if st is not None:  # a network error was already recorded as a FAIL by call()
                    self.fails.append(f"career card {soc}: HTTP {st}")
                continue
            card_data = card.get("data") if isinstance(card, dict) else None
            title = str((card_data or {}).get("title") or titles.get(soc, "?")) if isinstance(card_data, dict) else "?"
            state, value = ads_state(card)
            cards[soc] = (state, value)
            self.ads_states.append(state)
            self.ads_by_soc[soc] = state
            rows.append([soc, title, fmt_value(value), state, f"{ms:.0f}"])
        if rows:
            self.say(*table(["soc", "title", "ads_now", "ads status", "ms"], rows))
        self.say(f"  total so far: {self.total_ms:.0f} ms over {len(socs) + 1} calls")
        return cards

    # 4
    def amira(self) -> None:
        self.section("4. Amira flow")
        st, body, _ = self.call("GET", TAGS)
        tags = (body or {}).get("data") if isinstance(body, dict) else None
        ids = {t.get("id") for t in tags or [] if isinstance(t, dict)} if st == 200 else set()
        interests = [t for t in AMIRA_TAGS if t in ids]
        profile = {"interests": interests, "nation": "scotland", "location": "Glasgow", "automation_worry": 0.5}
        self.say(f"  profile: interests {interests or 'none found'}, scotland, Glasgow, automation_worry 0.5")
        self.say("  first idea: architect")
        st, body, ms = self.call("POST", RECS, {"profile": profile, "first_idea": "architect"})
        if st in UNAVAILABLE:
            self.say(f"  recommendations: {NOT_YET}")
            return
        data = (body or {}).get("data") if isinstance(body, dict) else None
        if st is None:  # network error, already recorded as a FAIL by call()
            return
        if st != 200 or not isinstance(data, dict):
            message = ((body or {}).get("error") or {}).get("message") if isinstance(body, dict) else None
            line = f"recommendations: HTTP {st}" + (f": {message}" if message else "")
            self.say(f"  {line}")
            (self.fails if st >= 500 else self.warns).append(line)  # 5xx breaks Amira's main flow
            return
        self.say(f"  recommendations: HTTP 200, {ms:.0f} ms")
        for p in data.get("picks") or []:
            career = p.get("career") or {}
            self.say(f"  {p.get('tier')}: {career.get('title')}")
        hedge = (data.get("hedge") or {}).get("career") or {}
        self.say(f"  hedge: {hedge.get('title') or 'none'}")
        self.say(f"  notices: {len(data.get('notices') or [])}")
        self.say(f"  explanation.ai_written: {(data.get('explanation') or {}).get('ai_written')}")

    # 5
    def unplug(self, before_statuses: dict[str, str], before_card: tuple[str, Any] | None) -> None:
        self.section("5. Pull the plug")
        if before_card is None:
            _, card, _ = self.call("GET", f"{CAREERS}/{UNPLUG_SOC}")
            before_card = ads_state(card)
        st, body, _ = self.call("POST", DEMO_LIVE, {"enabled": False})
        if st in UNAVAILABLE:
            self.say(f"  pull the plug: {NOT_YET}")
            return
        try:
            live = ((body or {}).get("data") or {}).get("live") if isinstance(body, dict) else None
            self.say(f"  plug pulled: HTTP {st}, live={live}")
            if st != 200:
                self.fails.append(f"demo/live disable returned HTTP {st}")
                return
            _, card, ms = self.call("GET", f"{CAREERS}/{UNPLUG_SOC}")
            after_card = ads_state(card) if card is not None else None
            after_statuses = self.badges("5b. Badges after")
            if after_card is None:
                self.say(f"  career {UNPLUG_SOC}: could not be re-fetched")
                return
            self.ads_after = after_card[0]
            rows = [["adzuna (career card)", before_card[0], after_card[0]],
                    [f"ads_now value, career {UNPLUG_SOC}", fmt_value(before_card[1]), fmt_value(after_card[1])]]
            for name, now in after_statuses.items():
                was = before_statuses.get(name)
                if was is not None and was != now and name != "adzuna":
                    rows.append([name, was, now])
            self.say("", f"  before / after (career {UNPLUG_SOC} re-fetched in {ms:.0f} ms)")
            self.say(*table(["item", "before", "after"], rows))
            for item, was, now in rows:
                if was != now:
                    self.say(f"  {item}: {was} -> {now}")
        finally:
            rst, rbody, _ = self.call("POST", DEMO_LIVE, {"enabled": True})
            restored = ((rbody or {}).get("data") or {}).get("live") if isinstance(rbody, dict) else None
            self.say(f"  plug restored: HTTP {rst}, live={restored}")
            if rst != 200 or restored is not True:
                self.fails.append(f"could not restore live mode (HTTP {rst}); POST {DEMO_LIVE} {{\"enabled\": true}} by hand")

    # 6
    def summary(self, toggled: bool) -> int:
        self.section("6. Summary")
        if self.bad_envelopes:
            self.fails.append("invalid envelope: " + "; ".join(self.bad_envelopes))
        else:
            self.passes.append("every response is a valid envelope (ok, meta.request_id, meta.as_of)")
        if self.mock_names:
            msg = "mock status on: " + ", ".join(sorted(self.mock_names))
            (self.fails if self.freeze else self.warns).append(msg + (" (--freeze)" if self.freeze else ""))
        else:
            self.passes.append("no mock status")
        states = set(self.ads_states)
        missing = [soc for soc, st in self.ads_by_soc.items() if st == "missing"]
        if missing and len(missing) == len(self.ads_by_soc):
            self.warns.append(NO_SNAPSHOT)
        elif missing:
            self.warns.append(f"ads missing for {len(missing)} of {len(self.ads_by_soc)} careers: " + ", ".join(missing))
        if states - {"missing"}:
            self.passes.append("ads status: " + ", ".join(sorted(states - {"missing"})))
        if self.ads_after is not None:
            if self.ads_after == "live":
                self.fails.append("ads still live after the plug was pulled")
            else:
                self.passes.append(f"ads after unplug: {self.ads_after} (not live)")
        elif toggled:
            self.warns.append("pull the plug could not be checked")
        for label, items in (("PASS", self.passes), ("WARN", self.warns), ("FAIL", self.fails)):
            for item in items:
                self.say(f"  {label}  {item}")
        self.say(f"  total request time: {self.total_ms:.0f} ms")
        return 1 if self.fails else 0


def run(client: Client, args: argparse.Namespace, out: Callable[[str], Any]) -> int:
    r = Run(client, out, freeze=args.freeze)
    try:
        r.health()
    except requests.RequestException:
        out(f"API not reachable at {args.base_url}; start it with: uvicorn avenir_api.app:app --port 8000")
        return 2
    before = r.badges()
    cards = r.warm()
    if args.warm_only:
        return r.summary(toggled=False)
    r.amira()
    toggled = not args.no_toggle
    if toggled:
        r.unplug(before, cards.get(UNPLUG_SOC))
    return r.summary(toggled=toggled)


def parse(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Avenir pull-the-plug rehearsal against a running API.")
    p.add_argument("--base-url", default="http://127.0.0.1:8000")
    p.add_argument("--warm-only", action="store_true", help="stop after warming the cache")
    p.add_argument("--no-toggle", action="store_true", help="do not pull the plug")
    p.add_argument("--timeout", type=float, default=5.0, help="seconds per request")
    p.add_argument("--freeze", action="store_true", help="any mock status is a FAIL (exit 1)")
    return p.parse_args(argv)


def main(argv: list[str] | None = None, client: Client | None = None,
         out: Callable[[str], Any] = print) -> int:
    args = parse(argv)
    return run(client or RequestsClient(args.base_url, args.timeout), args, out)


if __name__ == "__main__":
    sys.exit(main())
