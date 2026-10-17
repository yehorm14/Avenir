import copy

from fastapi.testclient import TestClient

from app import backtest
from app.data import get_store
from app.discover import evaluate
from app.explain import build_evidence, validate
from app.main import app
from app.models import MatchRequest, Weights
from app.scoring import FIT_THRESHOLD, match, normalise_weights, score_all
from app.trust import run_eval

client = TestClient(app)
INVESTIGATIVE_SOCIAL = {"R": 0.5, "I": 1.0, "A": 0.2, "S": 0.9, "E": 0.3, "C": 0.3}
REALISTIC = {"R": 1.0, "I": 0.4, "A": 0.1, "S": 0.2, "E": 0.3, "C": 0.5}


def test_low_fit_never_shown_even_with_all_weight_on_demand_and_pay():
    req = MatchRequest(profile=REALISTIC, weights=Weights(interest=0, demand_future=1, demand_now=1, pay=1, ai_resilience=0, head_start=0))
    res = match(req, get_store())
    assert res.results
    assert all(c.interest_fit >= FIT_THRESHOLD for c in res.results + res.more)
    assert res.hidden_low_fit > 0


def test_three_picks_by_default_each_with_full_analysis():
    res = match(MatchRequest(profile=INVESTIGATIVE_SOCIAL), get_store())
    assert len(res.results) == 3
    for c in res.results:
        assert c.stress and c.stress.total == 4
        assert c.confidence and c.confidence.level in ("High", "Medium", "Low")
        assert len(c.components) == 6


def test_ranking_is_deterministic():
    req = MatchRequest(profile=INVESTIGATIVE_SOCIAL, subjects=["Biology"], skills=["First aid"], region="Scotland")
    assert [c.soc for c in match(req, get_store()).results] == [c.soc for c in match(req, get_store()).results]


def test_missing_data_is_not_filled_in_and_weights_renormalise():
    # Environmental scientist has no 2035 projection; clinical psychologist has no pay figure.
    _, scored = score_all(MatchRequest(profile=INVESTIGATIVE_SOCIAL), get_store())
    for soc, key in (("2152", "demand_future"), ("2225", "pay")):
        c = next(x for x in scored if x.soc == soc)
        comp = next(x for x in c.components if x.key == key)
        assert comp.value is None and comp.effective_weight == 0 and comp.contribution == 0
        assert key in c.missing
        assert abs(sum(x.effective_weight for x in c.components) - 1) < 0.01
        assert abs(sum(x.contribution for x in c.components) - c.score) < 0.5


def test_score_matches_its_breakdown():
    res = match(MatchRequest(profile=REALISTIC, subjects=["Physics"]), get_store())
    for c in res.results:
        assert abs(sum(x.contribution for x in c.components) - c.score) < 0.5


def test_regional_lens_changes_demand_but_not_fit():
    store = get_store()
    uk = {c.soc: c for c in score_all(MatchRequest(profile=REALISTIC), store)[1]}
    ne = {c.soc: c for c in score_all(MatchRequest(profile=REALISTIC, region="North East"), store)[1]}
    assert uk["2123"].interest_fit == ne["2123"].interest_fit
    assert ne["2123"].figures.region_multiplier > 1  # clean energy over-indexes in the North East
    assert uk["2123"].figures.region_multiplier == 1


def test_hedge_is_a_different_career_that_still_fits_and_spreads_risk():
    res = match(MatchRequest(profile=INVESTIGATIVE_SOCIAL), get_store())
    picks = {c.soc for c in res.results}
    store = get_store()
    for c in res.results:
        h = c.hedge
        assert h is not None and h.soc not in picks
        assert h.interest_fit >= FIT_THRESHOLD
        assert h.diversifies
        if store.occupations[h.soc].sector == store.occupations[c.soc].sector:
            assert any("AI" in d for d in h.diversifies)


def test_interest_shift_scenario_can_hide_a_borderline_pick():
    res = match(MatchRequest(profile=INVESTIGATIVE_SOCIAL), get_store())
    for c in res.results:
        s = next(x for x in c.stress.scenarios if x.id == "interests_shift")
        if c.interest_fit - 0.15 < FIT_THRESHOLD:
            assert s.rank is None and not s.holds


def test_weights_normalise_and_zero_falls_back_to_default():
    w = normalise_weights(Weights(interest=1, demand_future=1, demand_now=1, pay=1, ai_resilience=1, head_start=1))
    assert abs(w.interest - 1 / 6) < 1e-9
    zero = Weights(interest=0, demand_future=0, demand_now=0, pay=0, ai_resilience=0, head_start=0)
    assert normalise_weights(zero) == Weights()


def test_flat_answers_show_nothing():
    store = get_store()
    answers = {item["id"]: 3 for item in store.quiz["items"]}
    res = match(MatchRequest(answers=answers), store)
    assert res.flat_profile and res.results == []


def test_validator_rejects_invented_numbers_and_fake_citations():
    store = get_store()
    _, scored = score_all(MatchRequest(profile=REALISTIC), store)
    ev = build_evidence(scored[0], store)
    assert validate("It pays £99,999 a year. [E1]", ev) is not None
    assert validate("It is a good fit. [E99]", ev) is not None
    assert validate("It is a good fit.", ev) is not None
    assert validate(f"{ev[0].text} [E1]", ev) is None


def test_ai_eval_set_passes_in_full():
    r = run_eval()
    assert r.validator_passed == r.validator_cases
    assert r.routing_passed == r.routing_cases


def test_backtest_has_no_look_ahead():
    store = get_store()
    y = backtest.years(store)[0]
    assert set(next(iter(backtest.inputs_for(store, y).values()))) == set(backtest.INPUT_FIELDS)
    before = backtest.signal(backtest.inputs_for(store, y))
    poisoned = copy.copy(store)
    poisoned.backtest = copy.deepcopy(store.backtest)
    for row in poisoned.backtest["years"][str(y)].values():
        row["employment_change_pct"] = 999.0
        row["pay_change_pct"] = -999.0
    assert backtest.signal(backtest.inputs_for(poisoned, y)) == before


def test_backtest_is_labelled_synthetic_and_bridge_toggle_drops_codes():
    store = get_store()
    s = backtest.summary(store)
    assert s.synthetic and s.verdict.startswith("SYNTHETIC")
    clean = backtest.summary(store, exclude_bridged=True)
    assert clean.pooled_n < s.pooled_n


def test_discovery_matcher_beats_keyword_baseline():
    baseline, current = evaluate(get_store()).results
    assert current.accuracy_at_3 > baseline.accuracy_at_3


def test_api_contract_endpoints():
    items = client.get("/api/quiz").json()["items"]
    assert len(items) == 30 and all(sum(i["type"] == t for i in items) == 5 for t in "RIASEC")
    assert client.get("/api/careers/0000").status_code == 404
    changes = client.get("/api/changes", params={"soc": ["5241", "2223"]}).json()
    by = {i["soc"]: i for i in changes["items"]}
    assert by["5241"]["direction"] == "up"
    assert by["2223"]["direction"] == "no data" and by["2223"]["delta"] is None
    r = client.post("/api/explain", json={"profile": REALISTIC, "soc": "5241", "question": "How much will I earn?"}).json()
    assert r["mode"] == "template" and r["cited"]
    assert client.get("/api/backtest/2015").json()["top"]
    assert client.get("/api/backtest/1999").status_code == 404
    assert len(client.get("/api/market", params={"region": "Wales"}).json()["rows"]) == 40
    assert client.post("/api/discover", json={"text": "I love fixing cars"}).json()["hits"][0]["soc"] == "5231"
    detail = client.get("/api/careers/2232").json()
    assert {r["nation"] for r in detail["routes"]} >= {"England", "Scotland", "Wales", "Northern Ireland"}


def test_every_career_has_a_complete_path_plan():
    from app.path import build_plan

    store = get_store()
    for soc, occ in store.occupations.items():
        plan = build_plan(store, soc, "Scotland")
        assert plan is not None, soc
        assert any(r.available for r in plan.routes), f"{occ.title} has no route"
        assert plan.hard_skills and plan.soft_skills and plan.societies and plan.competitions
        assert len(plan.timelines["university"]) >= 4 and len(plan.timelines["apprenticeship"]) >= 4
        # Every course the careers data lists has degree detail and example providers.
        assert [d.subject for d in plan.degrees] == [c["subject"] for c in occ.courses], soc
        for d in plan.degrees:
            assert d.universities and d.about and d.builds


def test_home_nation_universities_come_first_and_routes_are_nation_aware():
    from app.path import build_plan

    store = get_store()
    plan = build_plan(store, "2422", "Scotland")
    unis = plan.degrees[0].universities
    assert unis[0].home and unis[0].nation == "Scotland"
    homes = [u.home for u in unis]
    assert homes == sorted(homes, reverse=True)
    assert plan.funding.nation == "Scotland" and "saas" in plan.funding.url
    trade = build_plan(store, "5241", "Wales")
    assert trade.default_route == "apprenticeship" and trade.degrees == []
    assert trade.apprenticeship.routes[0].nation == "Wales"
    assert trade.apprenticeship.finders[0].nation == "Wales"


def test_degree_role_is_honest_about_regulated_careers():
    from app.path import build_plan

    store = get_store()
    for soc in ("2232", "2240", "2313", "2225"):
        assert build_plan(store, soc).degree_role.level == "required", soc
    for soc in ("5241", "3132", "6135"):
        assert build_plan(store, soc).degree_role.level == "optional", soc
    assert build_plan(store, "2225").apprenticeship is None  # no apprenticeship route to clinical psychology


def test_path_api_and_match_carry_degree_info():
    plan = client.get("/api/path/2422", params={"nation": "Scotland"}).json()
    assert plan["degree_role"]["level"] == "flexible"
    assert {"Finance", "Economics", "Business and management"} <= {d["subject"] for d in plan["degrees"]}
    assert client.get("/api/path/0000").status_code == 404
    res = client.post("/api/match", json={"profile": REALISTIC}).json()["results"][0]
    assert res["degree_role"] and isinstance(res["degrees"], list)


def test_events_also_score_the_backup_career():
    res = match(MatchRequest(profile=INVESTIGATIVE_SOCIAL), get_store())
    for c in res.results:
        assert c.hedge is not None and c.stress.hedge_baseline is not None
        assert all(s.hedge_score is not None for s in c.stress.scenarios)
        # The backup is scored with the same formula, so its baseline matches its own listed score.
        assert abs(c.stress.hedge_baseline - c.hedge.score) < 0.2


def test_arcade_round_is_deterministic_and_hides_outcomes():
    a = client.get("/api/game/round", params={"year": 2015, "seed": 3}).json()
    b = client.get("/api/game/round", params={"year": 2015, "seed": 3}).json()
    other = client.get("/api/game/round", params={"year": 2015, "seed": 4}).json()
    assert a == b and a["candidates"] != other["candidates"]
    assert len(a["candidates"]) == 10 and a["synthetic"]
    assert not ({"employment_change_pct", "pay_change_pct"} & set(a["candidates"][0]))
    assert client.get("/api/game/round", params={"year": 1999}).status_code == 404


def test_arcade_reveal_scores_fairly_and_rejects_bad_picks():
    rnd = client.get("/api/game/round", params={"year": 2013, "seed": 11}).json()
    socs = [c["soc"] for c in rnd["candidates"]]
    ok = client.post("/api/game/reveal", json={"year": 2013, "seed": 11, "picks": socs[:3]}).json()
    assert len(ok["rows"]) == 10 and sum(r["picked_by_you"] for r in ok["rows"]) == 3
    assert sum(r["picked_by_algorithm"] for r in ok["rows"]) == 3 and sum(r["best"] for r in ok["rows"]) == 3
    assert ok["best"]["avg_change"] >= ok["you"]["avg_change"] and ok["best"]["avg_change"] >= ok["algorithm"]["avg_change"]
    assert ok["verdict"] and ok["note"].startswith("SYNTHETIC")
    # The algorithm's picks are the top signals among the ten, whoever you chose.
    again = client.post("/api/game/reveal", json={"year": 2013, "seed": 11, "picks": socs[3:6]}).json()
    assert {r["soc"] for r in ok["rows"] if r["picked_by_algorithm"]} == {r["soc"] for r in again["rows"] if r["picked_by_algorithm"]}
    assert client.post("/api/game/reveal", json={"year": 2013, "seed": 11, "picks": [socs[0], socs[0], socs[1]]}).status_code == 422
    assert client.post("/api/game/reveal", json={"year": 2013, "seed": 11, "picks": ["0000", socs[0], socs[1]]}).status_code == 422


def test_radar_filters_by_field_stage_and_nation_and_never_invents_dates():
    from datetime import date

    from app.radar import radar

    store = get_store()
    cyber = radar(store, ["digital"], "school", "Scotland", date(2026, 10, 17))
    ids = {i.id for i in cyber.items}
    assert {"cyberfirst", "csc-uk"} <= ids
    assert "apprenticeships-sco" in ids and "apprenticeships-eng" not in ids  # nation-aware
    assert "gsoc" not in ids and "cfa-rc" not in ids  # university-only, and a different field
    assert all("school" in i.stage for i in cyber.items)
    # Status comes from typical months, and every item says its timing in words.
    by = {i.id: i.status for i in cyber.items}
    assert by["astro-pi"] == "open" and by["cyberfirst"] == "rolling"
    assert radar(store, ["digital"], "school", "Scotland", date(2026, 8, 1)).items[0].status in ("open", "soon", "rolling", "later")
    assert not cyber.live and "not connected" in cyber.note
    assert all(i.when and (i.url is None or i.url.startswith("https://")) for i in store.opportunities and cyber.items)


def test_radar_digest_counts_match_the_items_and_every_field_has_opportunities():
    from datetime import date

    from app.radar import radar

    store = get_store()
    d = radar(store, ["finance", "law"], "university", "England", date(2026, 9, 5))
    assert d.digest.open == sum(i.status == "open" for i in d.items)
    assert d.digest.soon == sum(i.status == "soon" for i in d.items)
    assert d.digest.highlights
    for fid in store.field_labels:
        assert fid in {f for fam in [store.pathways["families"]] for f in fam}, fid  # same field ids as the careers data
        for stage in ("school", "college", "university"):
            assert radar(store, [fid], stage, "England").items, f"{fid}/{stage} has nothing"


def test_every_opportunity_is_well_formed():
    store = get_store()
    ids = [o["id"] for o in store.opportunities]
    assert len(ids) == len(set(ids)) >= 50
    for o in store.opportunities:
        assert set(o["stage"]) <= {"school", "college", "university"}
        assert set(o["fields"]) <= set(store.field_labels) | {"all"}
        assert all(1 <= m <= 12 for m in o["open_months"])
        assert o["rolling"] or o["open_months"], o["id"]  # either year-round or has typical months


def test_safe_path_prefers_the_degree_that_keeps_more_doors_open():
    from app.path import build_plan

    store = get_store()
    cyber = build_plan(store, "2135")
    assert cyber.safe_path.most_direct.subject == "Cyber security" and cyber.safe_path.most_doors.subject == "Computer science"
    assert len(cyber.safe_path.most_doors.doors) > len(cyber.safe_path.most_direct.doors)
    # Single-route professions have nothing to compare.
    assert build_plan(store, "2232").safe_path is None or len(build_plan(store, "2232").degrees) > 1
    # Wherever a safe path is offered, it really is wider than the direct route.
    for soc in store.occupations:
        sp = build_plan(store, soc).safe_path
        if sp:
            assert len(sp.most_doors.doors) > len(sp.most_direct.doors)


def test_trend_check_counts_doors_from_our_data():
    trends = {t["id"]: t for t in client.get("/api/trends").json()}
    assert {"quantum", "ai", "cyber"} <= set(trends)
    q = trends["quantum"]
    doors = {s["subject"]: len(s["doors"]) for s in q["safer"]}
    assert doors["Mathematics"] >= 3 and doors["Physics"] >= 3
    assert q["specialist_doors"].startswith("Narrow") and "evidence_note" in q and "qualitative" in q["evidence_note"]
    assert all(r["soc"] for r in q["related"])
    assert client.get("/api/radar", params={"fields": ["digital"], "stage": "school", "nation": "Wales"}).status_code == 200


def test_radar_uses_exact_dates_when_a_live_feed_supplies_them_and_drops_expired_ones():
    from datetime import date

    from app.radar import radar

    store = copy.copy(get_store())
    base = {"title": "Dated hack day", "org": "Example", "kind": "hackathon", "stage": ["school"], "nations": ["UK"], "fields": ["digital"],
            "format": "In person", "cost": "Free", "when": "See organiser", "open_months": [], "rolling": False, "url": "https://example.org/", "why": "Test"}
    store.opportunities = [
        {**base, "id": "closing", "deadline": "2026-10-20"},
        {**base, "id": "expired", "deadline": "2026-10-01"},
        {**base, "id": "future", "opens": "2026-10-30", "deadline": "2026-12-01"},
        {**base, "id": "later", "opens": "2027-03-01"},
    ]
    r = {i.id: i for i in radar(store, ["digital"], "school", "England", date(2026, 10, 17)).items}
    assert "expired" not in r
    assert r["closing"].status == "open" and r["closing"].closing_soon
    assert r["future"].status == "soon" and not r["future"].closing_soon
    assert r["later"].status == "later"


def test_inflation_converts_money_between_years_correctly():
    r = client.get("/api/inflation", params={"amount": 50000, "from_year": 2015, "to_year": 2025}).json()
    assert r["equivalent"] == round(50000 * r["cpi_to"] / r["cpi_from"]) and r["equivalent"] > 50000
    assert "28% less" in r["sentence"]
    back = client.get("/api/inflation", params={"amount": r["equivalent"], "from_year": 2025, "to_year": 2015}).json()
    assert abs(back["equivalent"] - 50000) <= 1  # converting there and back returns the same money
    same = client.get("/api/inflation", params={"amount": 1000, "from_year": 2020, "to_year": 2020}).json()
    assert same["equivalent"] == 1000
    assert client.get("/api/inflation", params={"from_year": 1999}).status_code == 422
    assert client.get("/api/inflation", params={"amount": -5}).status_code == 422


def test_pay_series_is_consistent_real_in_base_year_equals_nominal_and_spread_is_ordered():
    d = client.get("/api/pay", params={"soc": ["2135", "5241", "2422"]}).json()
    assert d["synthetic"] and d["note"].startswith("SYNTHETIC") and d["base_year"] == d["last_year"] == 2025
    for c in d["careers"]:
        last = c["series"][-1]
        assert last["real"]["median"] == last["nominal"]["median"]  # base year: no adjustment
        for p in c["series"]:
            assert p["nominal"]["p25"] < p["nominal"]["median"] < p["nominal"]["p75"]
            assert p["real"]["p25"] < p["real"]["median"] < p["real"]["p75"]
            assert p["real"]["median"] >= p["nominal"]["median"]  # earlier pounds were worth more in today's money
        s = c["summary"]
        assert s["verdict"] == ("Beat inflation" if s["real_change_pct"] >= 3 else "Fell behind" if s["real_change_pct"] <= -3 else "Kept pace")
        assert abs(s["median_then_today"] - c["series"][0]["real"]["median"]) <= 1
    # Another base year changes real values but never the nominal ones.
    other = client.get("/api/pay", params={"soc": "2135", "base": 2015}).json()["careers"][0]["series"]
    assert other[0]["real"]["median"] == other[0]["nominal"]["median"]
    assert other[-1]["real"]["median"] < other[-1]["nominal"]["median"]


def test_pay_history_anchors_to_ashe_and_is_never_made_up_where_ons_publishes_nothing():
    store = get_store()
    series = store.pay_series["occupations"]
    for soc, occ in store.occupations.items():
        if occ.pay_median is None:
            assert soc not in series, f"{occ.title}: no ASHE figure, so no series"
        else:
            years = series[soc]["years"]
            assert len(years) == 11 and years["2025"]["median"] == occ.pay["median"] and years["2024"]["median"] == occ.pay["median_prev"]
    nodata = client.get("/api/pay", params={"soc": "2225"}).json()["careers"][0]
    assert nodata["series"] == [] and nodata["summary"] is None
    assert client.get("/api/pay", params={"soc": "0000"}).json()["careers"] == []
