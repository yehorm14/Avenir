"""No test in this folder may reach a language model: model settings are cleared and HTTP posts are blocked."""

import pytest
import requests

MODEL_ENV = ("ANTHROPIC_API_KEY", "LLM_ENABLED", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def _blocked_post(*args, **kwargs):
    raise AssertionError("tests must not make network calls; monkeypatch requests.post in the test")


@pytest.fixture(autouse=True)
def no_model_and_no_network(monkeypatch):
    for name in MODEL_ENV:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(requests, "post", _blocked_post)
