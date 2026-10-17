"""AdzunaAds: live count, 3 s total deadline, snapshot fallback, cache. No network: requests.get is faked."""
from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
from pathlib import Path

import pytest
import requests

from avenir_adapters.adzuna import source as adzuna_source
from avenir_adapters.adzuna.source import AdzunaAds
from avenir_contracts import Career, Metric

FIXTURES = Path(__file__).parent / "fixtures"  # holds adzuna/*.json, as snapshots/ does in the repo
NOTE = "Jobs by Adzuna: live ads matching the job title."


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class FakeResponse:
    def __init__(self, status: int = 200, body=None) -> None:
        self.status_code = status
        self._body = body

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise requests.HTTPError(f"{self.status_code}")

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeGet:
    """Stands in for requests.get. `script` has one outcome per call (the last one repeats)."""

    def __init__(self, script, clock: Clock | None = None) -> None:
        self.script = script
        self.clock = clock
        self.calls: list[dict] = []

    def __call__(self, url, params=None, timeout=None, **kw):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        step = self.script[min(len(self.calls) - 1, len(self.script) - 1)]
        if isinstance(step, tuple) and step[0] == "timeout":  # ("timeout", seconds_spent)
            if self.clock is not None:
                self.clock.now += step[1]
            raise requests.Timeout("slow")
        if isinstance(step, Exception):
            raise step
        return step


def career(soc: str = "2134", title: str = "Software developer", ads: Metric | None = None) -> Career:
    metrics = {"ads_now": ads} if ads is not None else {}
    return Career(soc2020=soc, title=title, official_title=title, metrics=metrics)


def catalogue_ads(value: float | None = 77, status: str = "final", source: str = "adzuna") -> Metric:
    return Metric(value=value, unit="count", as_of="2026-08-01", source=source, granularity="estimate",
                  confidence="medium", status=status)


@pytest.fixture
def clock() -> Clock:
    return Clock()


@pytest.fixture
def no_network(monkeypatch):
    calls: list = []  # the adapter swallows errors, so assert on the record, not on a raised error
    monkeypatch.setattr(adzuna_source.requests, "get", lambda *a, **k: calls.append((a, k)))
    yield calls
    assert calls == [], "network must not be called"


def make(clock: Clock, snapshots: Path = FIXTURES, keys=("id", "key")) -> AdzunaAds:
    return AdzunaAds(keys[0], keys[1], snapshots, clock=clock)


def test_live_success(monkeypatch, clock):
    fake = FakeGet([FakeResponse(200, {"count": 987, "mean": 41000})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    metric, status = make(clock).ads_now(career(), "UK")
    assert (metric.value, metric.unit, metric.source) == (987, "count", "adzuna")
    assert (metric.granularity, metric.confidence, metric.status) == ("estimate", "medium", "final")
    assert metric.note == NOTE
    assert metric.as_of is not None and len(metric.as_of) == 10
    assert (status.name, status.status, status.region) == ("adzuna", "live", "UK")
    assert status.as_of == metric.as_of
    call = fake.calls[0]
    assert call["url"] == "https://api.adzuna.com/v1/api/jobs/gb/search/1"
    assert call["params"] == {"app_id": "id", "app_key": "key", "what": "Software developer",
                              "results_per_page": 1, "content-type": "application/json"}
    assert max(call["timeout"]) <= 3.0  # (connect, read), both within the budget


def test_timeout_falls_back_to_snapshot_within_deadline(monkeypatch, clock):
    fake = FakeGet([("timeout", 3.0)], clock)  # first attempt burns the whole 3 s budget
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    start = clock.now
    metric, status = make(clock).ads_now(career(), "UK")
    assert clock.now - start <= 3.0
    assert len(fake.calls) == 1  # no budget left, so no retry
    assert max(fake.calls[0]["timeout"]) <= 3.0
    assert status.status == "snapshot"
    assert metric.value == 4321  # latest file (2026-10-01) wins over 2026-09-01
    assert status.as_of == metric.as_of == "2026-10-01"
    assert metric.source == "adzuna" and metric.unit == "count"
    assert metric.granularity == "estimate" and metric.confidence == "medium"
    assert metric.status == "final" and metric.note == NOTE


def test_retry_gets_only_remaining_budget(monkeypatch, clock):
    fake = FakeGet([("timeout", 1.5), ("timeout", 1.5)], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    start = clock.now
    metric, status = make(clock).ads_now(career(), "UK")
    assert [c["timeout"] for c in fake.calls] == [(3.0, 3.0), (1.5, 1.5)]
    assert clock.now - start <= 3.0
    assert status.status == "snapshot" and metric.value == 4321


def test_no_retry_when_less_than_half_second_left(monkeypatch, clock):
    fake = FakeGet([("timeout", 2.6)], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    _, status = make(clock).ads_now(career(), "UK")
    assert len(fake.calls) == 1
    assert status.status == "snapshot"


def test_retry_can_succeed(monkeypatch, clock):
    fake = FakeGet([("timeout", 1.0), FakeResponse(200, {"count": 55})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    metric, status = make(clock).ads_now(career(), "UK")
    assert (metric.value, status.status) == (55, "live")
    assert len(fake.calls) == 2


def test_set_live_false_never_calls_network(no_network, clock):
    ads = make(clock)
    ads.set_live(False)
    metric, status = ads.ads_now(career(), "UK")
    assert (status.status, metric.value) == ("snapshot", 4321)


def test_set_live_true_without_keys_stays_offline(no_network, clock):
    ads = make(clock, keys=(None, None))
    assert ads.live is False
    ads.set_live(True)
    metric, status = ads.ads_now(career(), "UK")
    assert (status.status, metric.value) == ("snapshot", 4321)


def test_live_defaults_on_with_keys(clock):
    assert make(clock).live is True
    assert make(clock, keys=("id", None)).live is False


@pytest.mark.parametrize("response", [
    FakeResponse(429, {"count": 5}),
    FakeResponse(401, {}),
    FakeResponse(403, {}),
    FakeResponse(500, {}),
    FakeResponse(200, ValueError("bad json")),
    FakeResponse(200, {"mean": 3}),
    FakeResponse(200, {"count": "many"}),
    FakeResponse(200, ["not", "a", "dict"]),
    requests.ConnectionError("down"),
    RuntimeError("anything"),
])
def test_bad_live_outcomes_fall_back_to_snapshot(monkeypatch, clock, response):
    monkeypatch.setattr(adzuna_source.requests, "get", FakeGet([response], clock))
    metric, status = make(clock).ads_now(career(), "UK")
    assert (status.status, metric.value) == ("snapshot", 4321)


def test_snapshot_entry_without_count_is_absent_so_catalogue_is_used(no_network, clock):
    # SOC 2150 has "search": null in the latest fixture
    ads = make(clock)
    ads.set_live(False)
    metric, status = ads.ads_now(career("2150", ads=catalogue_ads(77)), "UK")
    assert (metric.value, status.status) == (77, "snapshot")
    assert status.as_of == "2026-08-01"


def test_no_snapshot_for_soc_uses_catalogue_metric(no_network, clock):
    ads = make(clock)
    ads.set_live(False)
    metric, status = ads.ads_now(career("9999", ads=catalogue_ads(77)), "UK")
    assert metric.value == 77 and status.status == "snapshot"


def test_catalogue_mock_metric_reports_mock(no_network, clock):
    ads = make(clock)
    ads.set_live(False)
    _, status = ads.ads_now(career("9999", ads=catalogue_ads(10, status="mock", source="MOCK")), "UK")
    assert status.status == "mock"


def test_nothing_anywhere_is_missing(no_network, clock, tmp_path):
    ads = make(clock, snapshots=tmp_path)  # no adzuna/ folder at all
    ads.set_live(False)
    metric, status = ads.ads_now(career("9999"), "UK")
    assert metric.is_missing and metric.unit == "count" and metric.source == "adzuna"
    assert metric.note
    assert (status.name, status.status, status.region) == ("adzuna", "missing", "UK")


def test_live_failure_and_nothing_else_is_missing(monkeypatch, clock, tmp_path):
    monkeypatch.setattr(adzuna_source.requests, "get", FakeGet([requests.Timeout()], clock))
    metric, status = make(clock, snapshots=tmp_path).ads_now(career("9999"), "UK")
    assert metric.is_missing and status.status == "missing"


def test_unreadable_snapshot_is_absent_not_an_error(no_network, clock, tmp_path):
    d = tmp_path / "adzuna"
    d.mkdir()
    (d / "2026-10-05.json").write_text("{not json", encoding="utf-8")
    ads = make(clock, snapshots=tmp_path)
    ads.set_live(False)
    metric, status = ads.ads_now(career("2134", ads=catalogue_ads(77)), "UK")
    assert (metric.value, status.status) == (77, "snapshot")


def test_file_names_that_are_not_dates_are_ignored(no_network, clock, tmp_path):
    d = tmp_path / "adzuna"
    d.mkdir()
    (d / "2026-10-05.json").write_text(json.dumps(
        {"retrieved": "2026-10-05", "occupations": {"2134": {"search": {"count": 5}}}}), encoding="utf-8")
    (d / "notes.json").write_text(json.dumps(  # sorts after the dated file; would win if not filtered
        {"retrieved": "2099-01-01", "occupations": {"2134": {"search": {"count": 99999}}}}), encoding="utf-8")
    ads = make(clock, snapshots=tmp_path)
    ads.set_live(False)
    metric, _ = ads.ads_now(career("2134"), "UK")
    assert metric.value == 5


def test_snapshot_walks_back_to_older_file_with_the_soc(no_network, clock):
    # SOC 3544 is only in the older fixture (2026-09-01); the newest file has no entry for it
    ads = make(clock)
    ads.set_live(False)
    metric, status = ads.ads_now(career("3544", "Data analyst"), "UK")
    assert (metric.value, status.status, status.as_of) == (2222, "snapshot", "2026-09-01")


def test_snapshot_skips_corrupt_newest_file(no_network, clock, tmp_path):
    d = tmp_path / "adzuna"
    shutil.copytree(FIXTURES / "adzuna", d)
    (d / "2026-10-05.json").write_text("{not json", encoding="utf-8")
    ads = make(clock, snapshots=tmp_path)
    ads.set_live(False)
    assert ads.ads_now(career("2134"), "UK")[0].value == 4321
    assert ads.ads_now(career("3544"), "UK")[0].value == 2222


def test_snapshot_files_are_parsed_once_until_they_change(no_network, clock, tmp_path, monkeypatch):
    d = tmp_path / "adzuna"
    shutil.copytree(FIXTURES / "adzuna", d)
    parsed: list = []
    real_loads = json.loads
    monkeypatch.setattr(adzuna_source.json, "loads", lambda s, *a, **k: parsed.append(1) or real_loads(s, *a, **k))
    ads = make(clock, snapshots=tmp_path)
    ads.set_live(False)
    for _ in range(3):
        ads.ads_now(career("2134"), "UK")
    assert len(parsed) == 1  # only the newest file was needed, and it was read once
    newest = d / "2026-10-01.json"
    text = newest.read_text(encoding="utf-8").replace("4321", "4322")
    newest.write_text(text, encoding="utf-8")
    later = newest.stat().st_mtime_ns + 5_000_000_000
    os.utime(newest, ns=(later, later))
    assert ads.ads_now(career("2134"), "UK")[0].value == 4322
    assert len(parsed) == 2


def test_snapshot_with_wrong_shape_is_absent(no_network, clock, tmp_path):
    d = tmp_path / "adzuna"
    d.mkdir()
    (d / "2026-10-05.json").write_text(json.dumps({"retrieved": "2026-10-05", "occupations": []}),
                                       encoding="utf-8")
    ads = make(clock, snapshots=tmp_path)
    ads.set_live(False)
    _, status = ads.ads_now(career("2134"), "UK")
    assert status.status == "missing"


def test_cache_hit_within_ten_minutes_makes_one_call(monkeypatch, clock):
    fake = FakeGet([FakeResponse(200, {"count": 10}), FakeResponse(200, {"count": 20})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    first, _ = ads.ads_now(career(), "UK")
    clock.now += 599
    second, status = ads.ads_now(career(), "UK")
    assert (first.value, second.value, status.status) == (10, 10, "live")
    assert len(fake.calls) == 1


def test_cache_expires_after_ten_minutes(monkeypatch, clock):
    fake = FakeGet([FakeResponse(200, {"count": 10}), FakeResponse(200, {"count": 20})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    ads.ads_now(career(), "UK")
    clock.now += 601
    second, _ = ads.ads_now(career(), "UK")
    assert second.value == 20
    assert len(fake.calls) == 2


def test_cache_is_per_soc(monkeypatch, clock):
    fake = FakeGet([FakeResponse(200, {"count": 10}), FakeResponse(200, {"count": 20})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    a, _ = ads.ads_now(career("2134"), "UK")
    b, _ = ads.ads_now(career("3544", "Data analyst"), "UK")
    assert (a.value, b.value) == (10, 20)
    assert fake.calls[1]["params"]["what"] == "Data analyst"


def test_failures_are_not_cached(monkeypatch, clock):
    fake = FakeGet([FakeResponse(500, {}), FakeResponse(500, {}), FakeResponse(200, {"count": 30})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    _, s1 = ads.ads_now(career(), "UK")  # 500 twice (one retry): no breaker, no cache
    m2, s2 = ads.ads_now(career(), "UK")
    assert (s1.status, s2.status, m2.value) == ("snapshot", "live", 30)


def test_no_retry_on_4xx(monkeypatch, clock):
    fake = FakeGet([FakeResponse(404, {}), FakeResponse(200, {"count": 1})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    _, status = make(clock).ads_now(career(), "UK")
    assert status.status == "snapshot"
    assert len(fake.calls) == 1


def test_retry_on_5xx_can_succeed(monkeypatch, clock):
    fake = FakeGet([FakeResponse(503, {}), FakeResponse(200, {"count": 8})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    metric, status = make(clock).ads_now(career(), "UK")
    assert (metric.value, status.status, len(fake.calls)) == (8, "live", 2)


def test_slow_server_is_cut_off_at_the_deadline_in_real_time(monkeypatch):
    release = threading.Event()

    def blocking_get(*a, **k):  # a server that never answers (and ignores the requests timeout)
        release.wait(5)
        return FakeResponse(200, {"count": 1})

    monkeypatch.setattr(adzuna_source.requests, "get", blocking_get)
    ads = AdzunaAds("id", "key", FIXTURES, deadline_s=0.3)
    try:
        start = time.monotonic()
        metric, status = ads.ads_now(career(), "UK")
        elapsed = time.monotonic() - start
    finally:
        release.set()
    assert elapsed < 0.3 + 0.5
    assert (status.status, metric.value) == ("snapshot", 4321)


@pytest.mark.parametrize(("failure", "attempts"), [(("timeout", 0.1), 2), (requests.ConnectionError("down"), 2),
                                     (FakeResponse(401, {}), 1), (FakeResponse(403, {}), 1), (FakeResponse(429, {}), 1)])
def test_breaker_skips_network_for_60s_then_retries(monkeypatch, clock, failure, attempts):
    fake = FakeGet([failure] * attempts + [FakeResponse(200, {"count": 12})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    _, first = ads.ads_now(career(), "UK")
    n = len(fake.calls)
    assert first.status == "snapshot" and n == attempts
    clock.now += 59
    _, second = ads.ads_now(career("3544", "Data analyst"), "UK")  # another SOC: breaker is adapter-wide
    assert second.status == "snapshot" and len(fake.calls) == n
    clock.now += 2  # 61 s after the trip
    metric, third = ads.ads_now(career(), "UK")
    assert (third.status, metric.value) == ("live", 12)
    assert len(fake.calls) == n + 1


def test_open_breaker_still_serves_a_warm_cache(monkeypatch, clock):
    fake = FakeGet([FakeResponse(200, {"count": 10}), FakeResponse(429, {})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    ads.ads_now(career("2134"), "UK")
    ads.ads_now(career("3544", "Data analyst"), "UK")  # 429: trips the breaker
    metric, status = ads.ads_now(career("2134"), "UK")
    assert (metric.value, status.status) == (10, "live")
    assert len(fake.calls) == 2


def test_failures_are_logged_without_secrets(monkeypatch, clock, caplog):
    secret = "SECRETKEY-9f3a"
    err = requests.ConnectionError(f"HTTPSConnectionPool: /search/1?app_id=APPID&app_key={secret}")
    monkeypatch.setattr(adzuna_source.requests, "get", FakeGet([err], clock))
    ads = AdzunaAds("APPID", secret, FIXTURES, clock=clock)
    with caplog.at_level(logging.INFO, logger=adzuna_source.log.name):
        ads.ads_now(career(), "UK")
    assert "ConnectionError" in caplog.text
    assert "paused" in caplog.text  # breaker trip is logged
    assert secret not in caplog.text and "APPID" not in caplog.text and "api.adzuna.com" not in caplog.text


def test_http_status_is_logged(monkeypatch, clock, caplog):
    monkeypatch.setattr(adzuna_source.requests, "get", FakeGet([FakeResponse(429, {})], clock))
    with caplog.at_level(logging.WARNING, logger=adzuna_source.log.name):
        make(clock).ads_now(career(), "UK")
    assert "HTTP 429" in caplog.text


def test_set_live_false_ignores_warm_cache(monkeypatch, clock):
    fake = FakeGet([FakeResponse(200, {"count": 10})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    ads.ads_now(career(), "UK")
    ads.set_live(False)  # pull the plug: show the snapshot at once, not a cached live value
    _, status = ads.ads_now(career(), "UK")
    assert status.status == "snapshot"
    assert len(fake.calls) == 1


def test_set_live_true_closes_an_open_breaker(monkeypatch, clock):
    fake = FakeGet([FakeResponse(429, {}), FakeResponse(200, {"count": 12})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    assert ads.ads_now(career(), "UK")[1].status == "snapshot"  # 429 trips the breaker
    ads.set_live(False)
    ads.set_live(True)  # explicit switch-on: no 60 s wait
    metric, status = ads.ads_now(career(), "UK")
    assert (status.status, metric.value) == ("live", 12)


def test_timeout_then_5xx_still_opens_breaker(monkeypatch, clock):
    fake = FakeGet([("timeout", 0.1), FakeResponse(503, {}), FakeResponse(200, {"count": 12})], clock)
    monkeypatch.setattr(adzuna_source.requests, "get", fake)
    ads = make(clock)
    assert ads.ads_now(career(), "UK")[1].status == "snapshot"
    assert len(fake.calls) == 2
    assert ads.ads_now(career(), "UK")[1].status == "snapshot"
    assert len(fake.calls) == 2  # breaker open


def test_plug_pulled_during_a_live_call_returns_the_snapshot(monkeypatch, clock):
    holder: dict = {}

    def get_then_unplug(*a, **k):
        holder["ads"].set_live(False)  # the presenter pulls the plug while the request is in flight
        return FakeResponse(200, {"count": 999})
    monkeypatch.setattr(adzuna_source.requests, "get", get_then_unplug)
    ads = holder["ads"] = make(clock)
    metric, status = ads.ads_now(career(), "UK")
    assert (status.status, metric.value) == ("snapshot", 4321)
