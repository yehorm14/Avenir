"""Read-only interface to the Pathfinder ML artefacts. Standard library only.

Each artefact is looked up in PATHFINDER_ML_DIR (default snapshots/ml), then in
snapshots/ml/mock. The mock files have the final shape, so callers never
change when real artefacts replace them. See packages/ml/CONTRACTS.md.
"""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path

ARTEFACTS = ("occupations", "history", "hedges", "fit", "backtest", "crises", "sources", "eval")

FLAG_TEXT = {
    "bridged_soc2010": "Figures before 2021 are estimated from the older SOC 2010 occupation codes using the ONS crosswalk.",
    "recoded_2021": "Occupation codes changed in 2021, so job counts before and after 2021 are not directly comparable.",
    "provisional": "This year's figure is an ONS provisional estimate and may be revised.",
    "covid_year": "2020 figures are affected by the pandemic: low survey response and furlough.",
    "employees_only": "Covers employees only; self-employed and freelance workers are not included.",
    "suppressed": "ONS withheld this estimate because it was too unreliable.",
    "cv_high": "This estimate has a sampling error of 10 to 20 percent; treat it with caution.",
    "multi_isco": "This occupation spans several international job codes; the score is their weighted average and the range shows how much they differ.",
    "imputed_parent": "No direct figure exists; this is estimated from the wider occupation group.",
    "pending_source": "The data source for this figure has not been loaded yet.",
    "mock": "This is sample data, not a real figure.",
    "category_level": "Measured for a broad job-advert category, not for this exact occupation.",
    "bridged_soc2000": "Figures before 2011 are estimated from the older SOC 2000 occupation codes using two ONS crosswalks.",
    "sources_disagree": "Two independent research estimates disagree for this job, so the range is wider.",
}

# Flags that any generated prose about the number must mention.
MUST_MENTION = frozenset({"bridged_soc2010", "bridged_soc2000", "recoded_2021", "covid_year", "employees_only",
                          "imputed_parent", "category_level", "sources_disagree", "mock"})

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REAL_STATUSES = {"final", "preliminary"}


class ML:
    """Loader for the ML artefacts. Instances cache files; treat results as read-only."""

    def __init__(self, data_dir: str | os.PathLike | None = None, mock_dir: str | os.PathLike | None = None):
        default = os.environ.get("PATHFINDER_ML_DIR") or _REPO_ROOT / "snapshots" / "ml"
        self._data_dir = Path(data_dir) if data_dir else Path(default)
        self._mock_dir = Path(mock_dir) if mock_dir else _REPO_ROOT / "snapshots" / "ml" / "mock"
        self._cache: dict[str, dict] = {}
        self._paths: dict[str, Path] = {}

    # Loading -------------------------------------------------------------
    def _load(self, name: str) -> dict:
        if name in self._cache:
            return self._cache[name]
        for folder in (self._data_dir, self._mock_dir):
            path = folder / f"{name}.json"
            if path.is_file():
                data = json.loads(path.read_text(encoding="utf-8"))
                self._cache[name] = data
                self._paths[name] = path
                return data
        raise FileNotFoundError(f"{name}.json not found in {self._data_dir} or {self._mock_dir}")

    def status(self) -> dict:
        """Per-artefact status, origin ("real" = loaded from the data dir, "mock" = from the mock dir)
        and path, plus an overall mode: "real" when every artefact came from the data dir with a real
        status, "mock" when every artefact came from the mock dir, otherwise "mixed"."""
        artefacts = {}
        for name in ARTEFACTS:
            try:
                data = self._load(name)
                path = self._paths[name]
                origin = "mock" if path.parent.resolve() == self._mock_dir.resolve() else "real"
                artefacts[name] = {"status": data.get("status", "unknown"), "origin": origin, "path": str(path)}
            except FileNotFoundError:
                artefacts[name] = {"status": "missing", "origin": None, "path": None}
        origins = {a["origin"] for a in artefacts.values()}
        statuses = {a["status"] for a in artefacts.values()}
        if origins == {"real"} and statuses <= _REAL_STATUSES:
            mode = "real"
        elif origins <= {"mock", None}:
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
        """Deterministic keyword baseline: free text -> interest tags with a 0-1 score."""
        text = (text or "").lower()
        if not text.strip():
            return []
        results = []
        for tag in self._load("fit")["tags"]:
            matched = [kw for kw in tag["keywords"] if re.search(r"\b" + re.escape(kw.lower()), text)]
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

    # Track record, crises, provenance -------------------------------------
    def backtest(self, base_year: int | None = None) -> dict:
        windows = self._load("backtest")["windows"]
        if base_year is None:
            return copy.deepcopy(max(windows, key=lambda w: w["base_year"]))
        for w in windows:
            if w["base_year"] == int(base_year):
                return copy.deepcopy(w)
        raise KeyError(f"no backtest window for base year {base_year}; available: {sorted(w['base_year'] for w in windows)}")

    def backtest_caveats(self) -> list[str]:
        return list(self._load("backtest").get("caveats", []))

    def crises(self) -> list[dict]:
        return copy.deepcopy(self._load("crises")["crises"])

    def sources(self) -> dict:
        return copy.deepcopy(self._load("sources")["sources"])

    def evaluation(self) -> dict:
        return copy.deepcopy(self._load("eval")["checks"])
