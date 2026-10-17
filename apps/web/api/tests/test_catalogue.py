"""The complete occupation catalogue is browsable without widening matching."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


def test_catalogue_lists_every_official_occupation_with_exact_lightweight_metrics(client):
    from pathfinder_ml import ML

    response = client.get("/api/catalogue")
    assert response.status_code == 200
    catalogue = response.json()
    occupations = ML().occupations()
    assert len(catalogue) == len(occupations) == 412
    assert len({career["soc"] for career in catalogue}) == 412
    by_soc = {career["soc"]: career for career in catalogue}
    for occupation in occupations:
        career = by_soc[occupation["soc2020"]]
        assert set(career) == {"soc", "title", "sector", "pay", "jobs", "match_supported"}
        assert career["pay"] == occupation["metrics"]["pay_median"]
        current_jobs = occupation["metrics"]["jobs"]
        available = [point for point in ML().history(occupation["soc2020"]) if point["jobs_k"] is not None]
        if current_jobs["value"] is not None or not available:
            assert career["jobs"] == current_jobs
        else:
            latest = max(available, key=lambda point: point["year"])
            assert career["jobs"]["value"] == latest["jobs_k"]
            assert career["jobs"]["as_of"] == str(latest["year"])
            assert career["jobs"]["source"] == current_jobs["source"]
            assert career["jobs"]["confidence"] == current_jobs["confidence"]
            assert "historical_observation" in career["jobs"]["flags"]
            assert "historical observation" in career["jobs"]["note"]
        assert career["match_supported"] == occupation["in_demo_set"]
    assert by_soc["1111"]["title"] == ML().occupation("1111")["title"]
    assert by_soc["1111"]["sector"] == "Managers, directors and senior officials"
    assert by_soc["5315"]["title"] == "Plumber"
    assert sum(career["match_supported"] for career in catalogue) == 20
    assert "history" not in response.text
    assert len(response.content) < 650_000


@pytest.mark.parametrize("soc", ["1111", "5315", "2134", "9259"])
def test_full_profile_keeps_exact_metrics_history_and_top_five_hedges(client, soc):
    from pathfinder_ml import ML

    evidence = ML()
    response = client.get(f"/api/careers/{soc}")
    assert response.status_code == 200
    career = response.json()
    occupation = evidence.occupation(soc)
    assert career["soc"] == soc
    assert career["metrics"] == occupation["metrics"]
    assert career["history"] == evidence.history(soc)
    assert career["hedges"] == evidence.hedges(soc, k=5)
    source_ids = {measure["source"] for measure in occupation["metrics"].values()} | {"ons_cpih"}
    assert career["sources"] == [evidence.sources()[key] for key in sorted(source_ids) if key in evidence.sources()]
    assert career["match_supported"] == occupation["in_demo_set"]
    if not occupation["in_demo_set"] and soc != "5315":
        assert career["title"] == occupation["title"]
        assert career["skills"] == []
        assert career["family"] == "explore"
        assert career["pathway_available"] is False
        assert "not been added" in career["summary"]


@pytest.mark.parametrize("endpoint", ["careers", "path"])
def test_soc_inputs_are_validated_and_unknown_codes_return_404(client, endpoint):
    assert client.get(f"/api/{endpoint}/123").status_code == 422
    assert client.get(f"/api/{endpoint}/abcd").status_code == 422
    assert client.get(f"/api/{endpoint}/9999").status_code == 404


def test_ordinary_catalogue_role_has_honest_guidance_and_no_borrowed_path(client):
    assert client.get("/api/path/1111").status_code == 404
    for message in ("Which skills should I learn?", "Which course or degree?", "Tell me about the work"):
        response = client.post("/api/guide", json={"soc": "1111", "message": message})
        assert response.status_code == 200
        assert "not been added" in response.json()["text"]
        assert "20" in response.json()["text"]


@pytest.mark.parametrize("soc", ["1111", "1112"])
def test_demand_guide_uses_employee_job_trend_and_preserves_supplied_note(client, soc):
    from pathfinder_ml import ML

    response = client.post("/api/guide", json={"soc": soc, "message": "Explain demand"})
    assert response.status_code == 200
    text = response.json()["text"]
    assert "employee-job trend" in text
    assert "observed full-time employee job trend" not in text
    assert ML().occupation(soc)["metrics"]["demand_trend"]["note"] in text
    if soc == "1112":
        assert "estimated from the wider occupation group" in text


def test_catalogue_uses_last_available_jobs_observation_without_relabelling_the_year(client):
    from pathfinder_ml import ML

    evidence = ML()
    catalogue = {career["soc"]: career for career in client.get("/api/catalogue").json()}
    occupation = evidence.occupation("1133")
    last = next(point for point in reversed(evidence.history("1133")) if point["jobs_k"] is not None)
    summary = catalogue["1133"]["jobs"]
    assert summary["value"] == last["jobs_k"]
    assert summary["as_of"] == str(last["year"])
    assert summary["source"] == occupation["metrics"]["jobs"]["source"]
    assert "suppressed" not in summary["flags"]
    assert ("provisional" in summary["flags"]) == ("provisional" in last["flags"])
    assert "historical_observation" in summary["flags"]
    assert "unavailable" in summary["note"]
    assert summary["confidence"] == occupation["metrics"]["jobs"]["confidence"]
    detail = client.get("/api/careers/1133").json()
    assert detail["metrics"]["jobs"] == occupation["metrics"]["jobs"]
    assert detail["jobs_observation"] == summary
