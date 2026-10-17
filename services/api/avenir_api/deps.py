"""Default ports: live adapters when available, else offline contract defaults."""
from __future__ import annotations

from avenir_contracts import (
    AdsSource,
    ExplanationWriter,
    KeywordSuggester,
    SnapshotAds,
    TagSuggester,
    TemplateExplanation,
)


def default_ports() -> tuple[AdsSource, ExplanationWriter, TagSuggester]:
    try:
        from avenir_adapters.registry import ads_source, explanation_writer, tag_suggester
    except ImportError:
        return SnapshotAds(), TemplateExplanation(), KeywordSuggester()
    return ads_source(), explanation_writer(), tag_suggester()
