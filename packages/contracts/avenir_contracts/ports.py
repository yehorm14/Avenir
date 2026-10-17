"""Interfaces between the API (Nazar) and the live adapters (Yehor), with safe defaults.

The API depends only on these Protocols. Defaults never touch the network, so the demo runs
with no keys. Real implementations come from `avenir_adapters.registry` (Yehor's plan).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from pathfinder_ml import ML

from .envelope import SourceStatus
from .metric import Metric
from .models import Career, Explanation, RecommendationOut, TagMatch


@runtime_checkable
class TagSuggester(Protocol):
    name: str  # keyword | matcher | llm | none

    def suggest(self, free_text: str) -> list[TagMatch]: ...


@runtime_checkable
class AdsSource(Protocol):
    def ads_now(self, career: Career, region: str) -> tuple[Metric, SourceStatus]:
        """Live ad count, or the snapshot value with status 'snapshot'. Never raises."""
        ...

    def set_live(self, enabled: bool) -> None:
        """Pull-the-plug switch: False forces snapshot mode."""
        ...


@runtime_checkable
class ExplanationWriter(Protocol):
    def explain(self, rec: RecommendationOut) -> Explanation:
        """Plain English citing only numbers in `rec` and mentioning every text in rec.notices. Never raises."""
        ...


class KeywordSuggester:
    """ML's deterministic keyword baseline (packages/ml/CONTRACTS.md section 5, match_tags)."""
    name = "keyword"

    def __init__(self, ml: ML | None = None) -> None:
        self._ml = ml or ML()

    def suggest(self, free_text: str) -> list[TagMatch]:
        return [TagMatch.model_validate(m) for m in self._ml.match_tags(free_text)]


class SnapshotAds:
    """Serves the ads_now metric already in the catalogue, or missing."""

    def __init__(self) -> None:
        self.live = False

    def set_live(self, enabled: bool) -> None:
        self.live = enabled

    def ads_now(self, career: Career, region: str) -> tuple[Metric, SourceStatus]:
        m = career.metrics.get("ads_now") or Metric.missing("count", "adzuna")
        state = "mock" if m.is_mock else ("missing" if m.is_missing else "snapshot")
        return m, SourceStatus(name="adzuna", status=state, as_of=m.as_of, region=m.region)


class TemplateExplanation:
    def explain(self, rec: RecommendationOut) -> Explanation:
        if not rec.picks:
            text = "No career passed the fit check yet. Try picking a few more interests."
        else:
            text = " ".join(f"{p.tier.capitalize()}: {p.career.title}." for p in rec.picks)
        if rec.notices:
            text += " " + " ".join(rec.notices)
        return Explanation(text=text, ai_written=False)
