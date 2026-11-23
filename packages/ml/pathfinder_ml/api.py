"""Read-only interface to the Pathfinder ML artefacts. Standard library only.

Each artefact is looked up in PATHFINDER_ML_DIR (default snapshots/ml), then in
snapshots/ml/mock. The mock files have the final shape, so callers never
change when real artefacts replace them. See packages/ml/CONTRACTS.md.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import re
import threading
from pathlib import Path

ARTEFACTS = ("occupations", "history", "hedges", "fit", "backtest", "crises", "sources", "eval")
SUPPORTED_MAJOR = 1

FLAG_TEXT = {
    "bridged_soc2010": "Figures before 2021 are estimated from the older SOC 2010 occupation codes using the ONS crosswalk.",
    "recoded_2021": "Occupation codes changed in 2021, so job counts before and after 2021 are not directly comparable.",
    "provisional": "This year's figure is an ONS provisional estimate and may be revised.",
    "covid_year": "2020 figures are affected by the pandemic: low survey response and furlough.",
    "employees_only": "Covers employees only; self-employed and freelance workers are not included.",
    "suppressed": "This figure is withheld because the underlying data are too sparse or unreliable.",
    "cv_high": "This estimate has a sampling error above 10 percent; treat it with caution.",
    "multi_isco": "This occupation spans several international job codes; the score is their weighted average and the range shows how much they differ.",
    "imputed_parent": "No direct figure exists; this is estimated from the wider occupation group.",
    "pending_source": "The data source for this figure has not been loaded yet.",
    "mock": "This is sample data, not a real figure.",
    "category_level": "Measured for a broad job-advert category, not for this exact occupation.",
    "bridged_soc2000": "Figures before 2011 are estimated from the older SOC 2000 occupation codes using two ONS crosswalks.",
    "sources_disagree": "Two research estimates disagree for this job, so the range is wider.",
    "bridged_low_purity": "The older occupation code behind the figures before 2021 mixed several different jobs, so those figures may not describe this job well.",
    "partial_sources": "Part of the data behind this figure was missing, so it rests on only some of the job titles or older codes.",
    "ons_indicative_counts": "ONS says its job counts are indicative, not accurate estimates.",
    "fallback_all_employees": "Full-time figures were too sparse, so this uses all employees (full- and part-time).",
}

# Flags that any generated prose about the number must mention.
MUST_MENTION = frozenset({"bridged_soc2010", "bridged_soc2000", "recoded_2021", "covid_year", "employees_only",
                          "imputed_parent", "category_level", "sources_disagree", "mock", "bridged_low_purity",
                          "ons_indicative_counts"})

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REAL_STATUSES = {"final", "preliminary"}
_log = logging.getLogger(__name__)


def _keyword_pattern(kw: str) -> re.Pattern:
    """Keyword syntax used in fit.json tags: a trailing * means any word starting with the stem
    ("draw*" matches "drawing"); otherwise the whole word with an optional plural. Spaces match
    any run of spaces or hyphens ("hands on" matches "hands-on")."""
    stem = kw.endswith("*")
    words = [re.escape(w) for w in kw.rstrip("*").lower().split()]
    body = r"[\s\-]+".join(words)
    tail = r"[a-z]*" if stem else r"(?:s|es)?"
    return re.compile(r"(?<![a-z0-9])" + body + tail + r"(?![a-z0-9])")


class ML:
    """Loader for the ML artefacts. Instances cache files and are safe to share between threads;
    treat results as read-only copies."""

    def __init__(self, data_dir: str | os.PathLike | None = None, mock_dir: str | os.PathLike | None = None):
        default = os.environ.get("PATHFINDER_ML_DIR") or _REPO_ROOT / "snapshots" / "ml"
        self._data_dir = Path(data_dir) if data_dir else Path(default)
        self._mock_dir = Path(mock_dir) if mock_dir else _REPO_ROOT / "snapshots" / "ml" / "mock"
        self._cache: dict[str, tuple[dict, Path]] = {}
        self._lock = threading.Lock()
        self._patterns: dict[str, re.Pattern] = {}

    # Loading -------------------------------------------------------------
    def _load_with_path(self, name: str) -> tuple[dict, Path]:
        with self._lock:
            if name in self._cache:
                return self._cache[name]
            for folder in (self._data_dir, self._mock_dir):
                path = folder / f"{name}.json"
                if path.is_file():
                    data = json.loads(path.read_text(encoding="utf-8-sig"))
                    if not isinstance(data, dict):
                        raise ValueError(f"{path} is not a JSON object")
                    major = str(data.get("schema_version", "1")).split(".")[0]
                    if major.isdigit() and int(major) > SUPPORTED_MAJOR:
                        raise ValueError(f"{path} has schema_version {data.get('schema_version')}; this loader supports {SUPPORTED_MAJOR}.x")
                    if folder == self._mock_dir and self._data_dir != self._mock_dir:
                        _log.warning("pathfinder_ml: %s.json not in %s; using the mock file", name, self._data_dir)
                    self._cache[name] = (data, path)
                    return self._cache[name]
        raise FileNotFoundError(f"{name}.json not found in {self._data_dir} or {self._mock_dir}")

    def _load(self, name: str) -> dict:
        return self._load_with_path(name)[0]

    def status(self) -> dict:
        """Per-artefact status, origin ("real" = loaded from the data dir, "mock" = from the mock dir)
        and path, plus an overall mode: "real" when every artefact came from the data dir with a real
        status, "mock" when every artefact came from the mock dir, otherwise "mixed". Never raises:
        an unreadable file is reported with status "invalid"."""
        artefacts = {}
        for name in ARTEFACTS:
            try:
                data, path = self._load_with_path(name)
                origin = "mock" if path.parent.resolve() == self._mock_dir.resolve() else "real"
                artefacts[name] = {"status": data.get("status", "unknown"), "origin": origin, "path": str(path)}
            except FileNotFoundError:
                artefacts[name] = {"status": "missing", "origin": None, "path": None}
            except Exception as ex:  # noqa: BLE001  (status() must never raise)
                artefacts[name] = {"status": "invalid", "origin": None, "path": None, "error": f"{type(ex).__name__}: {ex}"[:200]}
        origins = {a["origin"] for a in artefacts.values()}
        statuses = {a["status"] for a in artefacts.values()}
        if origins == {"real"} and statuses <= _REAL_STATUSES:
            mode = "real"
        elif origins <= {"mock", None} and "invalid" not in statuses:
            mode = "mock"
        else:
            mode = "mixed"
        return {"mode": mode, "artefacts": artefacts}

    # Occupations ---------------------------------------------------------
    def occupations(self, demo_only: bool = False) -> list[dict]:
        occ = self._load("occupations")["occupations"]
        chosen = [o for o in occ if o.get("in_demo_set")] if demo_only else occ
        return copy.deepcopy(chosen)

    def occupation(self, soc2020: str) -> dict | None:
        for o in self._load("occupations")["occupations"]:
            if o["soc2020"] == str(soc2020):
                return copy.deepcopy(o)
        return None

    def history(self, soc2020: str) -> list[dict]:
        return copy.deepcopy(self._load("history")["occupations"].get(str(soc2020), []))

    def hedges(self, soc2020: str, k: int = 3) -> list[dict]:
        if k < 0:
            raise ValueError("k must be >= 0")
        return copy.deepcopy(self._load("hedges")["occupations"].get(str(soc2020), [])[:k])

    # Interests and fit ---------------------------------------------------
    def tags(self) -> list[dict]:
        return copy.deepcopy(self._load("fit")["tags"])

    def match_tags(self, text: str, top_k: int = 5) -> list[dict]:
        """Deterministic keyword baseline: free text -> interest tags with a 0-1 score.
        Score = n / (n + 1) where n is the number of the tag's keywords found in the text."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not isinstance(top_k, int) or top_k < 0:
            raise ValueError("top_k must be a non-negative integer")
        text = text.lower()
        if not text.strip():
            return []
        results = []
        for tag in self._load("fit")["tags"]:
            matched = []
            for kw in tag["keywords"]:
                pat = self._patterns.get(kw) or self._patterns.setdefault(kw, _keyword_pattern(kw))
                if pat.search(text):
                    matched.append(kw)
            if matched:
                results.append({"tag": tag["id"], "score": round(len(matched) / (len(matched) + 1), 4), "matched": matched})
        results.sort(key=lambda r: (-r["score"], r["tag"]))
        return results[:top_k]

    def fit_scores(self, tag_ids: list[str]) -> dict[str, float]:
        """Mean affinity over the selected tags, for every occupation (0 when absent)."""
        affinity = self._load("fit")["affinity"]
        unknown = sorted(set(tag_ids) - set(affinity))
        if unknown:
            raise ValueError(f"unknown tag ids: {unknown}")
        if not tag_ids:
            return {}
        socs = [o["soc2020"] for o in self._load("occupations")["occupations"]]
        return {soc: round(sum(affinity[t].get(soc, 0.0) for t in tag_ids) / len(tag_ids), 4) for soc in socs}

    def affinity(self) -> dict[str, dict[str, float]]:
        """The whole tag -> {soc2020: affinity} table from fit.json (a missing entry means 0)."""
        return copy.deepcopy(self._load("fit")["affinity"])

    # Whole-artefact and metadata accessors (copies; raise FileNotFoundError when absent) -------
    def fit(self) -> dict:
        """The whole fit artefact (status, method, evaluation, tags, affinity)."""
        return copy.deepcopy(self._load("fit"))

    def backtest_artefact(self) -> dict:
        """The whole backtest artefact (status, caveats, windows)."""
        return copy.deepcopy(self._load("backtest"))

    def hedges_status(self) -> str:
        """Status declared by the hedges artefact."""
        return copy.deepcopy(self._load("hedges")["status"])

    def occupations_meta(self) -> dict:
        """File-level metadata of the occupations artefact: schema_version and price_base ("" when absent)."""
        data = self._load("occupations")
        return {"schema_version": data.get("schema_version", ""), "price_base": data.get("price_base", "")}

    def career_text(self, soc2020: str) -> dict | None:
        """The career_texts entry for one occupation, or None when the role has no entry. This
        optional artefact is not in ARTEFACTS; raises FileNotFoundError when the file is absent."""
        return copy.deepcopy(self._load("career_texts").get(soc2020))

    # Track record, crises, provenance -------------------------------------
    def backtest_years(self) -> list[int]:
        """Base years that have a backtest window, oldest first."""
        return sorted(w["base_year"] for w in self._load("backtest")["windows"])

    def backtest(self, base_year: int | None = None) -> dict:
        """One window. With no year: the latest window whose job counts are comparable (falls back
        to the latest window of any kind)."""
        windows = self._load("backtest")["windows"]
        if base_year is None:
            comparable = [w for w in windows if w.get("jobs_comparable")]
            return copy.deepcopy(max(comparable or windows, key=lambda w: w["base_year"]))
        for w in windows:
            if w["base_year"] == int(base_year):
                return copy.deepcopy(w)
        raise KeyError(f"no backtest window for base year {base_year}; available: {sorted(w['base_year'] for w in windows)}")

    def backtest_status(self) -> str:
        """Status of the backtest artefact ("unknown" when the file does not declare one)."""
        return str(self._load("backtest").get("status", "unknown"))

    def backtest_caveats(self) -> list[str]:
        return list(self._load("backtest").get("caveats", []))

    def crises(self) -> list[dict]:
        return copy.deepcopy(self._load("crises")["crises"])

    def sources(self) -> dict:
        return copy.deepcopy(self._load("sources")["sources"])

    def evaluation(self) -> dict:
        return copy.deepcopy(self._load("eval")["checks"])
