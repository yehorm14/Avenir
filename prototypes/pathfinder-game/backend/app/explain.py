"""'Ask about this result'. Answers only from evidence we hold, always cites it.

If an LLM endpoint is configured (any OpenAI-compatible server, for example an
open-weight model on our own GPUs via vLLM), it drafts the answer and a
validator checks it. If the model is unavailable or fails validation, we fall
back to a template answer, so the feature works fully without AI.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request

from .data import Store
from .models import CareerSummary, Evidence, ExplainRequest, ExplainResponse
from .scoring import analyse

CITE = re.compile(r"\[(E\d+)\]")
NUMBER = re.compile(r"\d+(?:\.\d+)?")

TOPIC_OF = {
    "interest": "fit", "head_start": "fit", "demand_future": "demand", "demand_now": "demand",
    "pay": "pay", "ai_resilience": "risk",
}


def build_evidence(career: CareerSummary, store: Store) -> list[Evidence]:
    occ = store.occupations[career.soc]
    ev: list[Evidence] = []

    def add(text: str, source_id: str, topic: str) -> None:
        ev.append(Evidence(id=f"E{len(ev) + 1}", text=text, source_id=source_id, topic=topic))

    add(f"{occ.title} scores {career.score:g} out of 100 for you.", "scoring", "why")
    for c in career.components:
        if c.value is None:
            add(f"{c.label}: no data. {c.detail}. This signal is left out of the score.", c.source_id, TOPIC_OF[c.key])
        else:
            add(
                f"{c.label}: {c.detail}. It adds {c.contribution:g} points with a weight of {round(c.effective_weight * 100):g}%.",
                c.source_id, TOPIC_OF[c.key],
            )
    prev, latest = occ.ssv.get(store.previous_ess), occ.ssv.get(store.latest_ess)
    if prev is not None and latest is not None:
        add(f"Hard-to-fill share went from {prev:g}% in ESS {store.previous_ess} to {latest:g}% in ESS {store.latest_ess}.", "ess", "demand")
    for t in sorted(occ.ai_tasks, key=lambda t: -t["score"]):
        add(f"Task '{t['task']}' has an AI exposure of {t['score']:.2f}.", "ai_exposure", "risk")
    if career.stress:
        s = career.stress
        held = [x.label for x in s.scenarios if x.holds]
        failed = [x.label for x in s.scenarios if not x.holds]
        text = f"Stress test: it stays in your top {s.keep_within} in {s.holds} of {s.total} scenarios; the lowest score is {s.worst:g}."
        if failed:
            text += f" It drops out under: {', '.join(failed)}."
        elif held:
            text += " It holds under every scenario."
        add(text, "scoring", "risk")
    if career.hedge:
        h = career.hedge
        add(
            f"Hedge career: {h.title} (similarity {h.similarity:.2f}). It shares {', '.join(h.shared[:3]) or 'some strengths'}; {'; '.join(h.diversifies)}.",
            "scoring", "risk",
        )
    if career.confidence:
        add(f"Confidence: {career.confidence.level}. {'; '.join(career.confidence.reasons)}.", "scoring", "confidence")
    add(f"Typical level of study: {occ.study_level}.", "curated", "routes")
    if career.degree_role:
        add(f"How much the degree matters: {career.degree_role}.", "curated", "routes")
    if career.degrees:
        add(f"Degree subjects to consider: {', '.join(career.degrees)}.", "discover_uni", "routes")
    if occ.routes:
        names = "; ".join(f"{r['name']} ({r['level']})" for r in occ.routes)
        add(f"Routes in England: {names}.", "occupational_maps", "routes")
    for nation, routes in occ.nation_routes.items():
        names = "; ".join(f"{r['name']} ({r['level']})" for r in routes)
        add(f"Routes in {nation}: {names}.", "nations", "routes")
    for course in occ.courses:
        if course["median_earnings_15m"] is None:
            add(f"{course['subject']} ({course['qualification']}): no published earnings figure.", "discover_uni", "pay")
        else:
            add(
                f"{course['subject']} ({course['qualification']}): median earnings £{course['median_earnings_15m']:,} fifteen months after graduating.",
                "discover_uni", "pay",
            )
    if occ.skills_build:
        add(f"Skills to build: {', '.join(occ.skills_build)}.", "occupational_maps", "skills")
    add(f"A first step this month: {occ.first_step}", "curated", "skills")
    return ev


# Word prefixes per topic, checked in order; the first topic that matches wins.
TOPICS = [
    ("risk", ("risk", "ai", "automat", "robot", "replace", "safe", "hedge", "backup", "stress", "wrong")),
    ("confidence", ("confiden", "sure", "trust", "reliab", "accurate", "certain")),
    ("why", ("why", "rank", "score", "top", "higher", "lower", "explain")),
    ("pay", ("earn", "salary", "pay", "money", "wage", "£")),
    ("routes", ("study", "degree", "uni", "apprentic", "route", "college", "qualif", "course", "level", "scotland", "wales")),
    ("demand", ("demand", "need", "shortage", "future", "2035", "job", "growth", "secure", "hard")),
    ("skills", ("skill", "prepare", "start", "first", "begin", "month")),
    ("fit", ("fit", "interest", "like", "suit", "personality", "me")),
]


def route_topic(question: str) -> str:
    words = re.findall(r"[a-z0-9£]+", question.lower())
    return next(
        (name for name, prefixes in TOPICS if any(w == p or (len(p) > 2 and w.startswith(p)) for w in words for p in prefixes)),
        "why",
    )


def template_answer(question: str, evidence: list[Evidence]) -> tuple[str, list[str]]:
    topic = route_topic(question)
    if topic == "why":
        chosen = [evidence[0]] + [e for e in evidence if e.topic in ("fit", "demand", "pay", "risk") and ("adds" in e.text or "no data" in e.text)]
    else:
        chosen = [e for e in evidence if e.topic == topic]
    if topic == "risk":
        chosen = [e for e in chosen if not e.text.startswith("Task ")][:3] + [e for e in chosen if e.text.startswith("Task ")][:1]
    if not chosen:
        return ("We do not hold evidence that answers this for this career.", [])
    return " ".join(f"{e.text} [{e.id}]" for e in chosen), [e.id for e in chosen]


def validate(answer: str, evidence: list[Evidence]) -> str | None:
    """Return a reason the AI answer is rejected, or None if it passes."""
    if not answer.strip():
        return "empty answer"
    if len(answer) > 1500:
        return "answer too long"
    ids = {e.id for e in evidence}
    cited = CITE.findall(answer)
    if not cited:
        return "no citations"
    if any(c not in ids for c in cited):
        return "cites evidence that does not exist"
    evidence_numbers = set(NUMBER.findall(" ".join(e.text for e in evidence).replace(",", "")))
    for n in NUMBER.findall(CITE.sub("", answer).replace(",", "")):
        if n not in evidence_numbers:
            return f"number {n} is not in the evidence"
    return None


def ai_answer(question: str, evidence: list[Evidence]) -> str:
    base = os.environ["CAREERS_LLM_URL"].rstrip("/")
    body = {
        "model": os.getenv("CAREERS_LLM_MODEL", "default"),
        "temperature": 0,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You explain one career result to a UK school pupil aged about 16. "
                    "Answer ONLY from the evidence lines given. After every sentence, cite the line(s) used like [E2]. "
                    "Never add numbers that are not in the evidence. If the evidence does not answer the question, say so. "
                    "Use plain, short sentences. At most 4 sentences."
                ),
            },
            {
                "role": "user",
                "content": "Evidence:\n" + "\n".join(f"[{e.id}] {e.text}" for e in evidence) + f"\n\nQuestion: {question}",
            },
        ],
    }
    headers = {"Content-Type": "application/json"}
    if key := os.getenv("CAREERS_LLM_KEY"):
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(f"{base}/chat/completions", data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=float(os.getenv("CAREERS_LLM_TIMEOUT", "10"))) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"].strip()


def explain(req: ExplainRequest, store: Store) -> ExplainResponse | None:
    career = analyse(req, store, req.soc)
    if career is None:
        return None
    evidence = build_evidence(career, store)

    reason = None
    if os.getenv("CAREERS_LLM_URL"):
        try:
            answer = ai_answer(req.question, evidence)
            reason = validate(answer, evidence)
            if reason is None:
                return ExplainResponse(
                    answer=answer, cited=sorted(set(CITE.findall(answer)), key=lambda s: int(s[1:])),
                    evidence=evidence, mode="ai",
                )
        except Exception as e:  # model down, timeout, bad JSON
            reason = f"AI unavailable ({type(e).__name__})"
    answer, cited = template_answer(req.question, evidence)
    return ExplainResponse(answer=answer, cited=cited, evidence=evidence, mode="template", fallback_reason=reason)
