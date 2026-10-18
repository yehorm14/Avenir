"""Employer outreach drafts: never sent by the server, addressed only to a verified careers route."""

import copy
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BELL, NUL, ESC, RLO, ZWSP = chr(7), chr(0), chr(27), chr(0x202E), chr(0x200B)
VERIFIED_FORM = "https://flows.beamery.com/blackrock/earlycareers"


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


@pytest.fixture
def email_contact(monkeypatch):
    """BlackRock publishes no enquiry email, so the email branch is tested with a reserved example domain."""
    import api.main
    from api.outreach import employer_record

    record = copy.deepcopy(employer_record("blackrock"))
    record["contact"] = dict(record["contact"], type="email", value="careers.team+uk@example.com")
    monkeypatch.setattr(api.main, "employer_record", lambda employer: record)
    return record["contact"]["value"]


def _draft(client, **body):
    return client.post("/api/outreach/draft", json={"soc": "2134", "employer": "blackrock", **body})


def test_committed_blackrock_contact_is_the_verified_official_form():
    from api.outreach import employer_record

    contact = employer_record("blackrock")["contact"]
    assert contact["type"] == "form"
    assert contact["value"] == VERIFIED_FORM
    assert contact["url"] == "https://careers.blackrock.com/"
    assert contact["checked"] == "2026-10-18"
    assert "Disability.Assistance" not in contact["value"]


def test_draft_from_template_uses_the_role_and_the_alumni_kit(client):
    from app.data import get_store

    response = _draft(client)
    assert response.status_code == 200
    data = response.json()
    title = client.get("/api/careers/2134").json()["title"]
    assert data["subject"] == f"Question from a school student about {title} at BlackRock"
    assert data["body"].startswith("Hello BlackRock careers team,")
    assert title.lower() in data["body"]
    assert get_store().pathways["common"]["alumni"]["questions"][0] in data["body"]
    assert "{" not in data["body"] and "}" not in data["body"]
    assert "[Your name]" in data["body"]

    apprenticeship = _draft(client, route="apprenticeship", name="Amira").json()["body"]
    assert "apprenticeship route" in apprenticeship
    assert apprenticeship.endswith("Amira")


def test_form_fallback_has_no_mailto_and_opens_the_official_form(client):
    data = _draft(client, message="Hello, what does a first year look like?").json()
    assert data["to"] is None
    assert data["mailto"] is None
    assert data["form_url"] == VERIFIED_FORM
    assert data["employer_contact"]["checked"] == "2026-10-18"
    assert data["employer_contact"]["url"] == "https://careers.blackrock.com/"
    assert "Nothing is sent until you submit it yourself." in data["note"]


def test_draft_from_edited_message_strips_control_characters_and_signs(client):
    message = f"Hello team,{BELL}\r\nI am in S6{NUL} and like maths.{ESC}\n\nThanks,\n[Your name]{RLO}{ZWSP}"
    data = _draft(client, message=message, name=f"  Amira{BELL}\nK  ").json()
    assert data["body"] == "Hello team,\nI am in S6 and like maths.\n\nThanks,\nAmira K"
    assert not any(ch in data["body"] for ch in (BELL, NUL, ESC, RLO, ZWSP, "\r"))


def test_mailto_starts_with_the_contact_and_encodes_newlines_and_specials(client, email_contact):
    message = "Hi & hello?\nIs 100% = enough #1, a+b; c/d?\n\n[Your name]"
    data = _draft(client, message=message, name="Amira").json()
    assert data["to"] == email_contact
    assert data["form_url"] is None
    assert data["note"] == "Opens in your own email app; nothing is sent until you press send."
    mailto = data["mailto"]
    assert mailto.startswith("mailto:careers.team%2Buk@example.com?subject=")
    assert "%0D%0A" in mailto and "\n" not in mailto and "\r" not in mailto
    assert " " not in mailto and "+" not in mailto and "%20" in mailto
    query = mailto.split("?", 1)[1]
    subject, body = query.split("&body=")
    assert "&" not in body and "#" not in body and "=" not in body
    assert unquote(subject.removeprefix("subject=")) == data["subject"]
    assert unquote(body) == data["body"].replace("\n", "\r\n")
    assert "%26" in body and "%3F" in body and "%25" in body and "%23" in body


@pytest.mark.parametrize(
    "body",
    [
        {"soc": "21", "employer": "blackrock"},
        {"soc": "2134", "employer": "acme"},
        {"soc": "2134"},
        {"soc": "2134", "employer": "blackrock", "message": "x" * 2001},
        {"soc": "2134", "employer": "blackrock", "message": f" {BELL}\n\t "},
        {"soc": "2134", "employer": "blackrock", "name": "n" * 81},
        {"soc": "2134", "employer": "blackrock", "route": "college"},
        {"soc": "2134", "employer": "blackrock", "to": "someone@example.com"},
    ],
)
def test_bad_input_is_rejected(client, body):
    assert client.post("/api/outreach/draft", json=body).status_code == 422


def test_unknown_occupation_is_not_found_and_message_cap_holds(client):
    assert _draft(client, soc="0000").status_code == 404
    long = _draft(client, message="y" * 1995, name="Amira Khan").json()["body"]
    assert len(long) <= 2000


def test_envelope_app_serves_the_endpoint():
    from api.application import app

    response = TestClient(app).post("/api/outreach/draft", json={"soc": "2134", "employer": "blackrock"})
    assert response.status_code == 200
    assert response.json()["data"]["form_url"] == VERIFIED_FORM
