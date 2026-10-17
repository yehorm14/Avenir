"""Runs the AI evaluation set (data/ai_eval.json) for the Trust page and tests."""

from __future__ import annotations

import json

from .data import DATA_DIR
from .explain import route_topic, validate
from .models import EvalCase, Evidence, TrustReport


def run_eval() -> TrustReport:
    with open(DATA_DIR / "ai_eval.json", encoding="utf-8") as f:
        spec = json.load(f)
    evidence = [Evidence(**e) for e in spec["evidence"]]
    cases = []
    for c in spec["validator"]:
        reason = validate(c["answer"], evidence)
        got = "pass" if reason is None else "fail"
        cases.append(EvalCase(id=c["id"], kind="validator", input=c["answer"] or "(empty)", expected=c["expect"],
                              got=got if reason is None else f"fail: {reason}", passed=got == c["expect"]))
    for i, c in enumerate(spec["routing"], 1):
        got = route_topic(c["question"])
        cases.append(EvalCase(id=f"r{i}", kind="routing", input=c["question"], expected=c["expect"], got=got, passed=got == c["expect"]))
    v = [c for c in cases if c.kind == "validator"]
    r = [c for c in cases if c.kind == "routing"]
    return TrustReport(
        validator_cases=len(v), validator_passed=sum(c.passed for c in v),
        routing_cases=len(r), routing_passed=sum(c.passed for c in r), cases=cases,
    )
