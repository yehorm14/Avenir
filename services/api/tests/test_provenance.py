from fastapi.testclient import TestClient

from avenir_api.app import create_app

AMIRA = {
    "interests": ["maths", "art_drawing", "design", "building_spaces"],
    "qualifications": [{"subject": "maths", "level": "higher"}, {"subject": "art", "level": "higher"}],
    "nation": "scotland",
    "automation_worry": 0.5,
}


def _metrics(node, path="$"):
    if isinstance(node, dict):
        if "unit" in node:
            yield path, node
        for k, v in node.items():
            yield from _metrics(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _metrics(v, f"{path}[{i}]")


def test_every_metric_has_provenance(data):
    client = TestClient(create_app(data=data))
    r = client.post("/api/v1/recommendations", json={"profile": AMIRA, "first_idea": "architect"})
    assert r.status_code == 200, r.text
    found = list(_metrics(r.json()))
    assert found, "no metric dicts found; test would be vacuous"
    for path, m in found:
        assert m.get("source"), path
        assert m.get("confidence"), path
        assert m.get("status"), path
        assert isinstance(m.get("flags"), list), path
