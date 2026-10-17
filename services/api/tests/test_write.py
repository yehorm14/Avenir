from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from avenir_api.app import create_app
from avenir_contracts import Metric, SourceStatus

AMIRA = {
    "interests": ["maths", "art_drawing", "design", "building_spaces"],
    "qualifications": [{"subject": "maths", "level": "higher"}, {"subject": "art", "level": "higher"}],
    "nation": "scotland",
    "automation_worry": 0.5,
}
P = "/api/v1/profile"
R = "/api/v1/recommendations"


@pytest.fixture(scope="module")
def client(data):
    return TestClient(create_app(data=data))


def _ok(r):
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    return body["data"]


def _err(r, status, code):
    assert r.status_code == status, r.text
    body = r.json()
    assert body["ok"] is False
    assert body["error"]["code"] == code
    return body["error"]


class StubAds:
    def __init__(self):
        self.live = False

    def set_live(self, enabled):
        self.live = enabled

    def ads_now(self, career, region):
        v = 1000.0 + int(career.soc2020)
        m = Metric(value=v, unit="count", source="adzuna", confidence="high")
        st = SourceStatus(name="adzuna", status="live" if self.live else "snapshot")
        return m, st


def test_amira_flow(client):
    prof = _ok(client.post(P, json=AMIRA))
    assert prof["interests"][:4] == AMIRA["interests"]
    assert prof["tag_source"] == "keyword"
    rec = _ok(client.post(R, json={"profile": AMIRA, "first_idea": "architect"}))
    assert rec["first_idea"]["soc2020"] == "2451"
    assert [p["career"]["soc2020"] for p in rec["picks"]] == ["2141", "2452", "2453"]
    assert rec["hedge"]["career"]["soc2020"] == "2123"
    assert rec["notices"]
    assert rec["explanation"]["text"]
    assert rec["roadmap"]


@pytest.mark.parametrize("worry", [0.0, 1.0])
def test_slider_extremes(client, worry):
    rec = _ok(client.post(R, json={"profile": {**AMIRA, "automation_worry": worry}, "first_idea": "architect"}))
    assert rec["picks"]


def test_unknown_interest_422(client):
    e = _err(client.post(P, json={"interests": ["juggling"]}), 422, "VALIDATION_ERROR")
    assert "juggling" in str(e["details"])
    assert e["details"][0]["field"] == "interests"
    e = _err(client.post(R, json={"profile": {"interests": ["juggling"]}, "first_idea": "architect"}), 422, "VALIDATION_ERROR")
    assert "juggling" in str(e["details"])
    assert e["details"][0]["field"] == "profile.interests"


def test_empty_first_idea_422(client):
    e = _err(client.post(R, json={"profile": AMIRA, "first_idea": ""}), 422, "VALIDATION_ERROR")
    assert e["details"][0]["field"].endswith("first_idea")


def test_empty_data_503(data):
    empty = replace(data, careers={})
    c = TestClient(create_app(data=empty))
    _err(c.post(R, json={"profile": AMIRA, "first_idea": "architect"}), 503, "UPSTREAM_UNAVAILABLE")
    _err(c.get("/api/v1/careers/2451/hedge"), 503, "UPSTREAM_UNAVAILABLE")


def test_demo_live_false_not_live(data):
    ads = StubAds()
    c = TestClient(create_app(data=data, ads=ads))
    assert _ok(c.post("/api/v1/demo/live", json={"enabled": True})) == {"live": True}
    r = c.post(R, json={"profile": AMIRA, "first_idea": "architect"})
    adz = [s for s in r.json()["meta"]["sources"] if s["name"] == "adzuna"]
    assert [s["status"] for s in adz] == ["live"]
    assert _ok(c.post("/api/v1/demo/live", json={"enabled": False})) == {"live": False}
    r = c.post(R, json={"profile": AMIRA, "first_idea": "architect"})
    adz = [s for s in r.json()["meta"]["sources"] if s["name"] == "adzuna"]
    assert [s["status"] for s in adz] == ["snapshot"]
    _err(c.post("/api/v1/demo/live", json={"enabled": "x", "z": 1}), 422, "VALIDATION_ERROR")


def test_ads_overlay_on_every_career(data):
    c = TestClient(create_app(data=data, ads=StubAds()))
    rec = _ok(c.post(R, json={"profile": AMIRA, "first_idea": "architect"}))
    careers = [p["career"] for p in rec["picks"]] + [rec["first_idea"], rec["hedge"]["career"]]
    assert len(careers) == 5
    for car in careers:
        assert car["metrics"]["ads_now"]["value"] == 1000.0 + int(car["soc2020"])
    assert data.careers["2141"].metrics.get("ads_now") != c.app.state.ads.ads_now(data.careers["2141"], "UK")[0]


def test_hedge_endpoint(client):
    h = _ok(client.get("/api/v1/careers/2141/hedge"))
    assert h["for_soc"] == "2141"
    assert h["career"]["soc2020"] == "2123"
    _err(client.get("/api/v1/careers/9999/hedge"), 404, "NOT_FOUND")


def test_suggester_failure_degrades(data):
    class Boom:
        name = "llm"

        def suggest(self, text):
            raise RuntimeError("down")

    c = TestClient(create_app(data=data, suggester=Boom()))
    out = _ok(c.post(P, json={"interests": ["maths"], "free_text": "I like drawing"}))
    assert out["suggested"] == []
    assert out["tag_source"] == "none"
    assert out["interests"] == ["maths"]


def test_suggested_tags_appended(client):
    out = _ok(client.post(P, json={"interests": ["maths"], "free_text": "I love design and building"}))
    assert out["interests"][0] == "maths"
    assert len(out["interests"]) == len(set(out["interests"]))
    assert [m["tag"] for m in out["suggested"]]


@pytest.mark.parametrize("tag", ["science_health", "helping_people"])
def test_narrow_profile_gives_fewer_picks(client, tag):
    r = client.post(R, json={"profile": {"interests": [tag]}, "first_idea": "architect"})
    rec = _ok(r)
    assert 0 < len(rec["picks"]) < 3
    assert rec["explanation"]["text"]
    assert rec["hedge"] is None or rec["hedge"]["career"]["soc2020"]


def test_hedge_endpoint_overlays_ads(data):
    c = TestClient(create_app(data=data, ads=StubAds()))
    r = c.get("/api/v1/careers/2141/hedge")
    h = _ok(r)
    assert h["career"]["metrics"]["ads_now"]["value"] == 1000.0 + int(h["career"]["soc2020"])
    assert [s["name"] for s in r.json()["meta"]["sources"]].count("adzuna") == 1
    # a live switch shows through
    c.post("/api/v1/demo/live", json={"enabled": True})
    r = c.get("/api/v1/careers/2141/hedge")
    assert [s["status"] for s in r.json()["meta"]["sources"] if s["name"] == "adzuna"] == ["live"]
