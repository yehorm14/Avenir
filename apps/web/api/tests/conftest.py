"""No test in this folder may reach a language model: model settings are cleared and HTTP posts are blocked.
Each test also gets an empty guide reply cache, so a cached reply never leaks between tests."""

import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api import rate_limit  # noqa: E402

RATE_ENV = ("GUIDE_RATE_LIMIT", "TTS_RATE_LIMIT", "RATE_LIMIT_WINDOW_S", "TRUSTED_PROXY_HOPS")
MODEL_ENV = ("ANTHROPIC_API_KEY", "LLM_ENABLED", "LLM_BASE_URL", "LLM_API_KEY", "LLM_API_KEY_2", "LLM_MODEL", "GUIDE_CACHE")


def _blocked_post(*args, **kwargs):
    raise AssertionError("tests must not make network calls; monkeypatch requests.post in the test")


@pytest.fixture(autouse=True)
def no_model_and_no_network(monkeypatch, tmp_path):
    for name in MODEL_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in RATE_ENV:
        monkeypatch.delenv(name, raising=False)
    rate_limit.reset()
    rate_limit.set_clock(None)
    monkeypatch.setenv("GUIDE_CACHE_DIR", str(tmp_path / "guide-cache"))
    monkeypatch.setattr(requests, "post", _blocked_post)
