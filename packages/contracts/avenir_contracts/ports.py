"""Interfaces between the API (Nazar) and the live adapters (Yehor), with safe defaults.

The API depends only on these Protocols. Until the real adapters land it uses the
defaults below, which never touch the network, so the demo runs with no keys.
Real implementations are exposed by `avenir_adapters.registry` (Yehor's plan).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .envelope import SourceStatus
from .metric import Metric
from .models import Career, Explanation, RecommendationOut
from .vocab import InterestTag


@runtime_checkable
class TagSuggester(Protocol):
    name: str  # "matcher" | "keyword" | "none"

    def suggest(self, free_text: str) -> list[InterestTag]: ...


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
        """Plain-English text citing only numbers present in `rec`. Never raises."""
        ...


class NoTagSuggester:
    name = "none"

    def suggest(self, free_text: str) -> list[InterestTag]:
        return []


class SnapshotAds:
    """Serves the ads_now metric already in careers.json."""

    def __init__(self) -> None:
        self.live = False

    def set_live(self, enabled: bool) -> None:
        self.live = enabled

    def ads_now(self, career: Career, region: str) -> tuple[Metric, SourceStatus]:
        m = career.metrics.ads_now
        state = "mock" if m.is_mock else ("missing" if m.is_missing else "snapshot")
        return m, SourceStatus(name="adzuna", status=state, as_of=m.year, region=m.region)


class TemplateExplanation:
    def explain(self, rec: RecommendationOut) -> Explanation:
        if not rec.picks:
            return Explanation(text="No career passed the fit check. Try adding more interests.",
                               ai_written=False)
        parts = [f"{p.tier.capitalize()}: {p.career.title}." for p in rec.picks]
        return Explanation(text=" ".join(parts), ai_written=False)
