"""Guide reply cache: keyed on every inference input, safe under concurrency and a broken directory."""

import sys
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api import guide_cache  # noqa: E402
from test_guide_tools import TOOL_REPLY, _call, _final, _openai_env, _scripted_post, _tools_turn  # noqa: E402


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


BASE = {"soc": "2134", "message": "How does pay compare at BlackRock?"}


def _replies(monkeypatch, count):
    _openai_env(monkeypatch)
    tools = _tools_turn(_call("c1", "get_role_stats", {"soc": "2134"}), _call("c2", "get_employer", {}))
    return _scripted_post(monkeypatch, [tools, _final(TOOL_REPLY)] * count)  # two model calls per fresh reply


def test_different_follow_up_history_is_a_different_key(client, monkeypatch):
    calls = _replies(monkeypatch, 2)
    a = {**BASE, "history": [{"role": "user", "content": "Tell me about pay"}]}
    b = {**BASE, "history": [{"role": "user", "content": "Tell me about skills"}]}
    assert client.post("/api/guide", json=a).json()["cached"] is False
    assert client.post("/api/guide", json=b).json()["cached"] is False
    assert len(calls) == 4
    # the same follow-up context is replayed deterministically, without a model call
    assert client.post("/api/guide", json=a).json()["cached"] is True
    assert len(calls) == 4


def test_history_is_sent_to_the_model_for_each_context(client, monkeypatch):
    calls = _replies(monkeypatch, 2)
    a = {**BASE, "history": [{"role": "user", "content": "Tell me about pay"}]}
    b = {**BASE, "history": [{"role": "user", "content": "Tell me about skills"}]}
    client.post("/api/guide", json=a)
    client.post("/api/guide", json=b)
    sent = [str(calls[0]["payload"]["messages"]), str(calls[2]["payload"]["messages"])]
    assert "about pay" in sent[0] and "about skills" not in sent[0]
    assert "about skills" in sent[1]


def test_changed_message_profile_or_model_invalidates(client, monkeypatch):
    calls = _replies(monkeypatch, 4)
    assert client.post("/api/guide", json=BASE).json()["cached"] is False
    assert client.post("/api/guide", json=BASE).json()["cached"] is True
    assert client.post("/api/guide", json={**BASE, "message": "And pay?"}).json()["cached"] is False
    assert client.post("/api/guide", json={**BASE, "profile": {"tags": ["art"]}}).json()["cached"] is False
    monkeypatch.setenv("LLM_MODEL", "other-model")
    assert client.post("/api/guide", json=BASE).json()["cached"] is False
    assert len(calls) == 8


def test_changed_evidence_invalidates(client, monkeypatch):
    calls = _replies(monkeypatch, 2)
    assert client.post("/api/guide", json=BASE).json()["cached"] is False
    real = guide_cache.evidence_digest
    monkeypatch.setattr(guide_cache, "evidence_digest", lambda *parts: real(*parts, "new snapshot"))
    assert client.post("/api/guide", json=BASE).json()["cached"] is False
    assert len(calls) == 4


def test_key_covers_history_and_evidence():
    base = guide_cache.cache_key("2134", "m", None, "x")
    assert base == guide_cache.cache_key("2134", "m", None, "x")
    assert base != guide_cache.cache_key("2134", "m", None, "x", history=[{"role": "user", "content": "q"}])
    assert base != guide_cache.cache_key("2134", "m", None, "x", evidence="v2")
    assert guide_cache.evidence_digest({"a": 1}) != guide_cache.evidence_digest({"a": 2})


def test_concurrent_saves_leave_one_valid_entry_and_no_temp_files(tmp_path, monkeypatch):
    monkeypatch.setenv("GUIDE_CACHE_DIR", str(tmp_path / "c"))
    key = guide_cache.cache_key("2134", "m", None, "x")
    errors: list[Exception] = []

    def work(i):
        try:
            for _ in range(20):
                guide_cache.save(key, {"text": f"reply {i}", "model": "x", "tools_used": [], "checks": "passed"})
                entry = guide_cache.load(key)
                assert entry is None or entry["text"].startswith("reply ")
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=work, args=(i,)) for i in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors
    assert guide_cache.load(key)["text"].startswith("reply ")
    assert sorted(p.suffix for p in (tmp_path / "c").iterdir()) == [".json"]


def test_missing_directory_is_created(tmp_path, monkeypatch):
    target = tmp_path / "a" / "b"
    monkeypatch.setenv("GUIDE_CACHE_DIR", str(target))
    guide_cache.save("k", {"text": "t", "model": "x", "tools_used": [], "checks": "passed"})
    assert guide_cache.load("k")["text"] == "t"


def test_unwritable_directory_never_breaks_the_guide(client, monkeypatch, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("not a directory")
    monkeypatch.setenv("GUIDE_CACHE_DIR", str(blocker / "sub"))  # cannot be created
    guide_cache.save("k", {"text": "t", "model": "x", "tools_used": [], "checks": "passed"})
    assert guide_cache.load("k") is None
    calls = _replies(monkeypatch, 2)
    first = client.post("/api/guide", json=BASE).json()
    second = client.post("/api/guide", json=BASE).json()
    assert first["mode"] == second["mode"] == "llm_grounded" and not first["cached"] and not second["cached"]
    assert len(calls) == 4


def test_opt_out_and_key_free_fallback_do_not_use_the_cache(client, monkeypatch, tmp_path):
    folder = tmp_path / "guide-cache"
    answer = client.post("/api/guide", json=BASE).json()  # no model configured
    assert answer["mode"] == "prepared_demo" and answer["cached"] is False
    assert client.post("/api/guide", json=BASE).json()["text"] == answer["text"]  # deterministic
    assert not folder.exists()
    monkeypatch.setenv("GUIDE_CACHE", "0")
    _replies(monkeypatch, 2)
    client.post("/api/guide", json=BASE)
    assert client.post("/api/guide", json=BASE).json()["cached"] is False
    assert not folder.exists()
