"""Metric: every number Avenir shows, with its provenance (AGENTS.md rule 2 and 3)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .vocab import Confidence, Granularity

MOCK_SOURCE = "MOCK"


class Metric(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: float | None
    low: float | None = None
    high: float | None = None
    unit: str = Field(description="e.g. GBP_per_year, pct, pct_per_year, index_0_1, flag, count, score_0_10")
    source: str = Field(min_length=1, description="data/manifest.yaml id, an ML artefact name, or MOCK")
    year: str | None = Field(default=None, description="'2025' or a period like '2025-04/2026-03'")
    region: str = Field(description="UK, GB, Scotland, England, International")
    granularity: Granularity
    n: int | None = Field(default=None, ge=0)
    confidence: Confidence
    note: str | None = None

    @model_validator(mode="after")
    def _missing_is_low(self) -> Metric:
        if self.value is None and self.confidence != "low":
            raise ValueError("a missing value must have confidence 'low'")
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError("low must not exceed high")
        return self

    @property
    def is_missing(self) -> bool:
        return self.value is None

    @property
    def is_mock(self) -> bool:
        return self.source == MOCK_SOURCE

    @classmethod
    def missing(cls, unit: str, source: str, region: str = "UK",
                granularity: Granularity = "occupation", note: str = "missing") -> Metric:
        return cls(value=None, unit=unit, source=source, region=region,
                   granularity=granularity, confidence="low", note=note)
