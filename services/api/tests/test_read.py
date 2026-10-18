import pytest
from fastapi.testclient import TestClient

from avenir_api.app import create_app
from avenir_contracts import AvenirData, Metric, SourceStatus


@pytest.fixture(scope="module")
def client(data):
    return TestClient(create_app(data=data))


def _ok(r):
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["meta"]["sources"]
    return body["data"]


def _err(r, status, code):
    assert r.status_code == status
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == code


def test_tags(client, data):
    out = _ok(client.get("/api/v1/tags"))
    assert [t["id"] for t in out] == [t.id for t in data.tags]
    assert out


def test_sources(client, data):
    out = _ok(client.get("/api/v1/sources"))
    assert len(out["statuses"]) == len(data.statuses)
    assert set(out["registry"]) == set(data.sources)


def test_careers_list(client, data):
    out = _ok(client.get("/api/v1/careers"))
    assert len(out) == len(data.careers) == 20
    assert {c["soc2020"] for c in out} == set(data.careers)


def test_career_detail_overlays_ads_now_from_ads_source(data):
    class StubAds:
        def ads_now(self, career, region):
            return (
                Metric(value=12345, unit="ads", source="stub", confidence="high"),
                SourceStatus(name="adzuna", status="live"),
            )

        def set_live(self, enabled):
            pass

    r = TestClient(create_app(data=data, ads=StubAds())).get("/api/v1/careers/2451")
    out = _ok(r)
    assert out["metrics"]["ads_now"]["value"] == 12345
    names = [s["name"] for s in r.json()["meta"]["sources"]]
    assert names[: len(data.statuses)] == [s.name for s in data.statuses]
    assert names[-1] == "adzuna"


def test_career_unknown_404(client):
    _err(client.get("/api/v1/careers/9999"), 404, "NOT_FOUND")


def test_history(client, data):
    out = _ok(client.get("/api/v1/careers/2451/history"))
    assert len(out) == len(data.history["2451"])
    _err(client.get("/api/v1/careers/9999/history"), 404, "NOT_FOUND")


def test_crises(client):
    assert len(_ok(client.get("/api/v1/crises"))) == 4


def test_backtest_years_sorted(client):
    assert _ok(client.get("/api/v1/backtest/years")) == [2013, 2014, 2015, 2019]


def test_backtest_latest_by_default(client, data):
    out = _ok(client.get("/api/v1/backtest"))
    assert out["window"]["base_year"] == 2019
    assert out["caveats"] == data.backtest_caveats
    assert out["status"] == data.backtest_status


def test_backtest_year(client):
    assert _ok(client.get("/api/v1/backtest?year=2013"))["window"]["base_year"] == 2013


def test_backtest_unknown_year_404(client):
    _err(client.get("/api/v1/backtest?year=1999"), 404, "NOT_FOUND")


def test_backtest_no_data_no_year_503():
    r = TestClient(create_app(data=AvenirData())).get("/api/v1/backtest")
    _err(r, 503, "UPSTREAM_UNAVAILABLE")


def test_backtest_no_data_explicit_year_503():
    _err(TestClient(create_app(data=AvenirData())).get("/api/v1/backtest?year=2019"), 503, "UPSTREAM_UNAVAILABLE")


def test_backtest_bad_year_422(client):
    _err(client.get("/api/v1/backtest?year=abc"), 422, "VALIDATION_ERROR")


def test_routes(client, data):
    soc = next(s for s, rs in data.routes.items() if rs)
    out = _ok(client.get(f"/api/v1/routes/{soc}"))
    assert out and all(r["nation"] == "scotland" for r in out)


def test_routes_other_nation_may_be_empty(client):
    assert _ok(client.get("/api/v1/routes/2451?nation=wales")) == []


def test_routes_unknown_soc_404(client):
    _err(client.get("/api/v1/routes/9999"), 404, "NOT_FOUND")


def test_routes_bad_nation_422(client):
    _err(client.get("/api/v1/routes/2451?nation=mars"), 422, "VALIDATION_ERROR")


SOC_PATHS = ["/api/v1/careers/{}", "/api/v1/careers/{}/history", "/api/v1/routes/{}", "/api/v1/careers/{}/hedge"]


@pytest.mark.parametrize("path", SOC_PATHS)
def test_malformed_soc_is_422_unknown_is_404(data, path):
    # docs/contracts.md: a malformed SOC (not 4 digits) is 422; a well-formed unknown SOC is 404
    c = TestClient(create_app(data=data))
    for bad in ("abc", "245", "24510", "24a1"):
        r = c.get(path.format(bad))
        assert r.status_code == 422, (path, bad)
        assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert c.get(path.format("9999")).status_code == 404
