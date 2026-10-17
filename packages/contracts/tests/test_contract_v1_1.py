"""ML contract v1.1 additions (packages/ml/CONTRACTS.md "Changes in v1.1"): test-only values, v1.1 shapes."""
from avenir_contracts import ML_METRICS, Career, Crisis, Hedge, HedgeCandidate, Metric
from avenir_contracts.data import join_career


def _metric(**kw):
    return {"value": 0.2, "unit": "fraction", "source": "s", "confidence": "medium", **kw}


def test_young_worker_share_is_an_ml_metric():
    assert "young_worker_share" in ML_METRICS
    assert ML_METRICS[-1] == "young_worker_share"
    assert len(ML_METRICS) == 14
    assert ML_METRICS[:-1] == (  # the v1.0 keys, order unchanged
        "pay_median", "pay_p10", "pay_p90", "real_pay_change_10y", "jobs", "demand_trend",
        "demand_trend_2011_19", "exposure", "exposure_uk", "resilience_covid",
        "resilience_cost_of_living", "resilience_tech_slump", "resilience_2008",
    )


def test_hedge_candidate_keeps_evidence():
    h = HedgeCandidate.model_validate({
        "soc2020": "2134", "title": "T", "similarity": 0.5, "shared_skills": ["a"],
        "evidence": "estimate", "why": "w", "status": "preliminary"})
    assert h.evidence == "estimate"
    assert HedgeCandidate.model_validate({"soc2020": "2134", "title": "T", "similarity": 0.5}).evidence is None


def test_hedge_accepts_evidence_and_defaults_to_none():
    career = Career(soc2020="2134", title="t", official_title="t", metrics={})
    kw = dict(for_soc="2451", career=career, similarity=0.5, shared_skills=[], why=None, risk_delta=-1.0,
              status="preliminary")
    assert Hedge(**kw, evidence="title").evidence == "title"
    assert Hedge(**kw).evidence is None


def test_crisis_keeps_baseline_real_pay_median():
    c = Crisis.model_validate({
        "key": "gfc_2008", "label": "2008", "window": "2008-2009", "measure": "m",
        "baseline_median": -0.01, "baseline_real_pay_median": -0.02, "status": "preliminary"})
    assert c.baseline_real_pay_median == -0.02
    assert Crisis.model_validate({"key": "k", "label": "l", "window": "w", "measure": "m"}).baseline_real_pay_median is None


def test_join_career_keeps_v1_1_metric_and_flags():
    occ = {
        "soc2020": "2134", "title": "Programmers", "short_title": "Software developer",
        "metrics": {
            "young_worker_share": _metric(flags=["bridged_soc2000"]),
            "resilience_tech_slump": _metric(
                flags=["category_level", "sources_disagree"], extra={"adverts_category": "IT"},
                future_field={"x": 1}),
        },
    }
    career = join_career(occ, None)
    assert career.metrics["young_worker_share"].value == 0.2
    assert career.metrics["young_worker_share"].flags == ["bridged_soc2000"]
    slump = career.metrics["resilience_tech_slump"]
    assert slump.flags == ["category_level", "sources_disagree"]
    assert slump.extra["adverts_category"] == "IT"
    assert not hasattr(slump, "future_field")


def test_unknown_future_metric_field_ignored():
    m = Metric.model_validate(_metric(brand_new=1))
    assert m.value == 0.2
