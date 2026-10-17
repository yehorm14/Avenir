"""avenir_adapters.registry: the three live adapters the API imports. No env, no network, no import-time work."""
from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest
import requests

from avenir_adapters import registry
from avenir_adapters.adzuna.source import AdzunaAds
from avenir_adapters.llm.writer import LlmExplanation
from avenir_contracts import Career
from avenir_contracts.ports import (
    AdsSource,
    ExplanationWriter,
    KeywordSuggester,
    TagSuggester,
    TemplateExplanation,
)

FIXTURES = Path(__file__).parent / "fixtures"  # holds adzuna/*.json, as snapshots/ does in the repo
ENV_KEYS = (
    "ADZUNA_APP_ID", "ADZUNA_APP_KEY", "AVENIR_SNAPSHOT_DIR",
    "LLM_ENABLED", "LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL",
)


def career(soc: str = "2134", title: str = "Software developer") -> Career:
    return Career(soc2020=soc, title=title, official_title=title, metrics={})


class FakeResponse:
    def __init__(self, status: int = 200, body=None) -> None:
        self.status_code = status
        self._body = body

    def json(self):
        return self._body


@pytest.fixture(autouse=True)
def clean(monkeypatch, tmp_path):
    for key in ENV_KEYS:
        # set then delete: monkeypatch then restores the key's absence, even for keys the .env loader adds
        monkeypatch.setenv(key, "")
        monkeypatch.delenv(key)
    monkeypatch.setattr(registry, "ENV_FILE", tmp_path / "no-such.env")  # never read a developer's real .env
    registry.reset()
    yield
    registry.reset()


@pytest.fixture
def network(monkeypatch):
    """Records every requests.get / requests.post call; the test asserts on the record."""
    calls: list = []

    def record(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("network must not be called")

    monkeypatch.setattr(requests, "get", record)
    monkeypatch.setattr(requests, "post", record)
    return calls


def test_no_env_gives_protocol_objects_and_safe_defaults(network):
    suggester = registry.tag_suggester()
    ads = registry.ads_source()
    writer = registry.explanation_writer()

    assert isinstance(suggester, KeywordSuggester)
    assert isinstance(suggester, TagSuggester)
    assert isinstance(ads, AdzunaAds)
    assert isinstance(ads, AdsSource)
    assert ads.live is False
    assert type(writer) is TemplateExplanation
    assert isinstance(writer, ExplanationWriter)
    assert network == []


def test_ads_now_without_keys_uses_snapshot_path_and_makes_no_network_call(monkeypatch, tmp_path, network):
    monkeypatch.setenv("AVENIR_SNAPSHOT_DIR", str(tmp_path))  # empty root: no snapshot, no catalogue metric
    metric, status = registry.ads_source().ads_now(career(), "UK")

    assert network == []
    assert (status.name, status.status) == ("adzuna", "missing")
    assert metric.is_missing


def test_snapshot_dir_env_is_used_when_set(monkeypatch, network):
    monkeypatch.setenv("AVENIR_SNAPSHOT_DIR", str(FIXTURES))  # FIXTURES/adzuna/*.json, the snapshot layout
    metric, status = registry.ads_source().ads_now(career(), "UK")

    assert network == []
    # the newest fixture (2026-10-01) wins over 2026-09-01 (count 1111)
    assert (status.status, status.as_of, metric.value) == ("snapshot", "2026-10-01", 4321)


def test_each_factory_is_a_singleton_until_reset(network):
    for factory in (registry.tag_suggester, registry.ads_source, registry.explanation_writer):
        first = factory()
        assert factory() is first
        registry.reset()
        assert factory() is not first


def test_import_has_no_side_effects(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise AssertionError("no network at import")

    monkeypatch.setattr(requests, "get", boom)
    monkeypatch.setattr(requests, "post", boom)
    importlib.reload(registry)  # must not raise
    # reload reset ENV_FILE to the real .env; point it back at a missing file for the rest of the test
    monkeypatch.setattr(registry, "ENV_FILE", tmp_path / "no-such.env")
    registry.reset()


def test_dotenv_fills_missing_keys_and_never_overrides_real_env(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# a comment line\n"
        "\n"
        "ADZUNA_APP_ID=abc\n"
        'ADZUNA_APP_KEY="def"\n'
        "LLM_MODEL=from-file\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(registry, "ENV_FILE", env_file)
    monkeypatch.setenv("LLM_MODEL", "real-model")  # a real environment variable wins over the file

    calls: list = []

    def fake_get(url, params=None, timeout=None, **kwargs):
        calls.append(params)
        return FakeResponse(200, {"count": 5})

    monkeypatch.setattr(requests, "get", fake_get)
    metric, status = registry.ads_source().ads_now(career(), "UK")

    assert (status.status, metric.value) == ("live", 5)
    assert calls[0]["app_id"] == "abc"
    assert calls[0]["app_key"] == "def"
    assert os.environ["ADZUNA_APP_ID"] == "abc"
    assert os.environ["ADZUNA_APP_KEY"] == "def"
    assert os.environ["LLM_MODEL"] == "real-model"


def test_llm_env_gives_llm_writer(monkeypatch):
    monkeypatch.setenv("LLM_ENABLED", "true")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example/v1")
    monkeypatch.setenv("LLM_API_KEY", "key")
    monkeypatch.setenv("LLM_MODEL", "model")

    assert isinstance(registry.explanation_writer(), LlmExplanation)
