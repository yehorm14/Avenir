import pytest
from aventir.ingest import normalise_occupation, normalise_series


def test_occupation_retains_official_identity_and_real_skill_relations():
    raw = {
        "uri": "http://data.europa.eu/esco/occupation/abc",
        "title": "software developer",
        "code": "2512.1",
        "description": {"en": {"literal": "Builds software."}},
        "_links": {
            "hasEssentialSkill": [
                {
                    "uri": "skill/a",
                    "title": "programming",
                    "skillType": "http://data.europa.eu/esco/skill-type/skill",
                }
            ],
            "hasOptionalSkill": [
                {
                    "uri": "skill/b",
                    "title": "project management",
                    "skillType": "http://data.europa.eu/esco/skill-type/knowledge",
                }
            ],
        },
    }
    c = normalise_occupation(raw)
    assert c["id"] == "abc"
    assert c["essential"][0]["title"] == "programming"
    assert c["optional"][0]["kind"] == "knowledge"
    assert c["salary"] is None
    assert c["source_url"] == raw["uri"]


def test_time_series_sorts_real_observations_and_excludes_missing_cells():
    data = {
        "description": {"title": "UK Job Vacancies (thousands) - Manufacturing"},
        "months": [
            {"date": "2025 FEB", "value": "42"},
            {"date": "2025 JAN", "value": "40"},
            {"date": "2025 MAR", "value": ""},
        ],
    }
    rows = normalise_series(data)
    assert rows == [{"time": "2025-01-01", "value": 40000.0}, {"time": "2025-02-01", "value": 42000.0}]


def test_occupation_without_identity_is_rejected():
    with pytest.raises(ValueError):
        normalise_occupation({"title": "unknown"})


def test_missing_skill_relationships_are_marked_unavailable_not_zero_requirements():
    career = normalise_occupation(
        {"uri": "http://data.europa.eu/esco/occupation/compact", "title": "compact profile", "_links": {}}
    )
    assert career["skills_available"] is False
    assert career["salary"] is None


def test_non_finite_source_values_never_enter_a_chart():
    assert (
        normalise_series(
            {"months": [{"date": "2025 JAN", "value": "NaN"}, {"date": "2025 FEB", "value": "inf"}]}
        )
        == []
    )
