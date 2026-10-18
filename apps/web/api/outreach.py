"""Employer outreach drafts: the student's own message, addressed to an employer's verified careers route.

The server never sends anything (no SMTP, no form posts). It returns a draft plus a link the student opens
and sends themselves: a ``mailto:`` URL when the employer publishes an email, or the official form URL.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

EMPLOYERS_DIR = Path(__file__).resolve().parents[1] / "public" / "employers"
EMPLOYER_FILES = {"blackrock": "blackrock.json"}
MESSAGE_MAX = 2000
NAME_MAX = 80
EMAIL_NOTE = "Opens in your own email app; nothing is sent until you press send."
FORM_NOTE = (
    "{employer} publishes no general careers enquiry email, so this opens its official form in your browser. "
    "The form may have no box for a message, so keep a copy of yours. Nothing is sent until you submit it yourself."
)

# C0/C1 controls except tab and newline (handled first), zero-width and bidi-override characters, BOM.
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_text(text: str, limit: int, *, single_line: bool = False) -> str:
    """Normalise line endings, drop control characters, trim, and cap at ``limit`` characters."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    if single_line:
        text = text.replace("\n", " ")
    text = _CONTROL.sub("", text)
    if single_line:
        text = " ".join(text.split())
    else:
        text = "\n".join(line.rstrip() for line in text.split("\n")).strip()
    return text[:limit].rstrip()


def mailto_url(address: str, subject: str, body: str) -> str:
    """RFC 6068 ``mailto:`` URL: every reserved character percent-encoded, spaces as %20, newlines as %0D%0A."""
    if not _EMAIL.match(address):
        raise ValueError("contact email is not a valid address")
    crlf_body = body.replace("\r\n", "\n").replace("\n", "\r\n")
    return f"mailto:{quote(address, safe='@')}?subject={quote(subject, safe='')}&body={quote(crlf_body, safe='')}"


@lru_cache(maxsize=8)
def employer_record(employer: str) -> dict:
    """The committed employer file (read once); raises KeyError for an employer we have no file for."""
    with (EMPLOYERS_DIR / EMPLOYER_FILES[employer]).open(encoding="utf-8") as handle:
        return json.load(handle)


def template_body(template: str, *, role: str, employer: str, question: str) -> str:
    """Fill the alumni-kit template with what the API knows; unknown details stay as [brackets] to edit."""
    return (
        template.replace("{their_name}", f"{employer} careers team")
        .replace("{field}", role.lower())
        .replace("{question}", question)
        .replace("{degree}", "[degree]")
        .replace("{uni}", "[university]")
    )


def sign(body: str, name: str | None) -> str:
    """Put the student's name in place of the [Your name] placeholder, or under the message if it is missing."""
    if not name:
        return body
    if "[Your name]" in body:
        return body.replace("[Your name]", name)
    return body if name in body else f"{body}\n\n{name}"


def build_draft(record: dict, *, role: str, template: str, question: str, message: str | None, name: str | None) -> dict:
    """The draft and the link to open it with. ``message`` and ``name`` must already be cleaned."""
    employer = record["employer"]
    contact = record["contact"]
    if message:
        body = message
    else:
        body = template_body(template, role=role, employer=employer, question=question)
    body = clean_text(sign(body, name), MESSAGE_MAX)
    subject = clean_text(f"Question from a school student about {role} at {employer}", 200, single_line=True)
    is_email = contact["type"] == "email"
    return {
        "to": contact["value"] if is_email else None,
        "subject": subject,
        "body": body,
        "mailto": mailto_url(contact["value"], subject, body) if is_email else None,
        "form_url": None if is_email else contact["value"],
        "employer_contact": dict(contact),
        "note": EMAIL_NOTE if is_email else FORM_NOTE.format(employer=employer),
    }
