"""Discovery: "describe what you enjoy, in your own words".

The plan's target is a fine-tuned interest matcher fed by practitioner clips.
Until clips are licensed and advisers have labelled training data, this TF-IDF
matcher over each occupation's description, tasks and skills stands in for it.
It is graded against plain keyword search over job titles on a held-out set,
so any future model has a baseline it must beat.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from functools import lru_cache

from .data import DATA_DIR, Store, get_store
from .models import DiscoverEval, DiscoverHit, DiscoverResponse, EvalResult

STOP = set(
    "a an and are as at be but by for from has have i i'd i'm in into is it its like love enjoy my me of on or our "
    "so that the their them they this to want was we with would you your always often really very am do people "
    "every good get ask help make making work working sort out".split()
)


def stem(w: str) -> str:
    for suf in ("ing", "ers", "er", "ies", "es", "ed", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z]+", text.lower()):
        if w in STOP:
            continue
        out.append(stem(w))
    return out


def occupation_text(occ) -> str:
    parts = [occ.title, occ.soc_title, occ.summary, occ.study_level, " ".join(occ.skills_build), " ".join(occ.skills_have),
             " ".join(occ.subjects), " ".join(t["task"] for t in occ.ai_tasks), occ.sector or ""]
    return " ".join(parts)


class TfIdf:
    def __init__(self, store: Store) -> None:
        self.socs = list(store.occupations)
        docs = [Counter(tokens(occupation_text(store.occupations[s]))) for s in self.socs]
        df = Counter(t for d in docs for t in d)
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
        self.vecs = [self._vec(d) for d in docs]

    def _vec(self, counts: Counter) -> dict[str, float]:
        v = {t: (1 + math.log(c)) * self.idf.get(t, 0.0) for t, c in counts.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {t: x / norm for t, x in v.items()}

    def rank(self, text: str) -> list[tuple[str, float, list[str]]]:
        q = self._vec(Counter(tokens(text)))
        out = []
        for soc, d in zip(self.socs, self.vecs):
            shared = [t for t in q if t in d]
            out.append((soc, sum(q[t] * d[t] for t in shared), sorted(shared, key=lambda t: -q[t] * d[t])))
        out.sort(key=lambda r: (-r[1], r[0]))
        return out


def keyword_rank(store: Store, text: str) -> list[tuple[str, float]]:
    """Baseline: count of query words found in the job title (what a title search does)."""
    q = set(re.findall(r"[a-z]+", text.lower())) - STOP
    out = []
    for soc, occ in store.occupations.items():
        title = set(re.findall(r"[a-z]+", f"{occ.title} {occ.soc_title}".lower()))
        out.append((soc, float(len(q & title))))
    out.sort(key=lambda r: (-r[1], r[0]))
    return out


@lru_cache(maxsize=1)
def _model() -> TfIdf:
    return TfIdf(get_store())


def discover(store: Store, text: str) -> DiscoverResponse:
    model = _model()
    hits = [
        DiscoverHit(soc=s, title=store.occupations[s].title, score=round(sc, 3), matched=m[:4])
        for s, sc, m in model.rank(text)[:5]
        if sc > 0
    ]
    return DiscoverResponse(method="TF-IDF over job descriptions, tasks and skills (stand-in for the fine-tuned matcher)", hits=hits)


def evaluate(store: Store) -> DiscoverEval:
    with open(DATA_DIR / "discovery_eval.json", encoding="utf-8") as f:
        ex = json.load(f)["examples"]
    model = _model()

    def score(name: str, ranker) -> EvalResult:
        a1 = a3 = 0
        for e in ex:
            ranked = ranker(e["text"])
            if ranked and ranked[0][1] > 0 and ranked[0][0] == e["soc"]:
                a1 += 1
            if e["soc"] in [r[0] for r in ranked[:3] if r[1] > 0]:
                a3 += 1
        return EvalResult(name=name, n=len(ex), accuracy_at_1=round(a1 / len(ex), 3), accuracy_at_3=round(a3 / len(ex), 3))

    return DiscoverEval(
        note="Held-out pupil-style descriptions, never used for tuning. The same team wrote the job descriptions and these examples, so the scores are optimistic. Next step: have careers advisers label real pupil text. A fine-tuned matcher must beat both rows before it replaces this one.",
        results=[
            score("Keyword search over job titles (baseline)", lambda t: keyword_rank(store, t)),
            score("TF-IDF matcher (current)", lambda t: [(s, sc) for s, sc, _ in model.rank(t)]),
        ],
    )
