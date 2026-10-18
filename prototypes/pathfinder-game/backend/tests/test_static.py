from urllib.parse import quote

import pytest
from app import main
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def frontend(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<main>Prototype</main>")
    (dist / "robots.txt").write_text("User-agent: *")
    outside = tmp_path / "private.txt"
    outside.write_text("outside frontend sentinel")
    monkeypatch.setattr(main, "DIST", dist)
    application = FastAPI()
    application.get("/{path:path}")(main.spa)
    with TestClient(application) as client:
        yield client, dist, outside


@pytest.mark.parametrize("path", ["/", "/career/2451", "/robots.txt"])
def test_frontend_files_and_spa_routes_remain_available(frontend, path):
    client, _, _ = frontend
    response = client.get(path)
    assert response.status_code == 200
    assert response.text == ("User-agent: *" if path == "/robots.txt" else "<main>Prototype</main>")


def test_encoded_absolute_path_cannot_read_outside_frontend(frontend):
    client, _, outside = frontend
    response = client.get("/" + quote(str(outside), safe=""))
    assert response.status_code == 404
    assert "outside frontend sentinel" not in response.text


def test_encoded_parent_path_cannot_read_outside_frontend(frontend):
    client, _, _ = frontend
    response = client.get("/%2e%2e/private.txt")
    assert response.status_code == 404
    assert "outside frontend sentinel" not in response.text


def test_symlink_cannot_read_outside_frontend(frontend):
    client, dist, outside = frontend
    (dist / "linked.txt").symlink_to(outside)
    response = client.get("/linked.txt")
    assert response.status_code == 404
    assert "outside frontend sentinel" not in response.text


def test_spa_fallback_cannot_follow_outside_index_symlink(frontend):
    client, dist, outside = frontend
    (dist / "index.html").unlink()
    (dist / "index.html").symlink_to(outside)
    response = client.get("/career/2451")
    assert response.status_code == 404
    assert "outside frontend sentinel" not in response.text
