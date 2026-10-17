"""Metric: every number Avenir shows. Same shape as packages/ml/CONTRACTS.md section 2.1,
plus `region` (default UK). Unknown fields are ignored so ML minor versions don't break us."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .vocab import Confidence, MetricStatus

MOCK_SOURCE = "MOCK"


class Metric(BaseModel):
    model_config = ConfigDict(extra="ignore")

    value: float | None
    low: float | None = None
    high: float | None = None
    unit: str
    as_of: str | None = None
    source: str = Field(min_length=1, description="key in sources.json / data/manifest.yaml, or MOCK")
    granularity: str = Field(default="occupation", description="occupation | parent_group | major_group | estimate")
    confidence: Confidence
    flags: list[str] = Field(default_factory=list, description="vocabulary in packages/ml/CONTRACTS.md 2.3")
    status: MetricStatus = "final"
    note: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)
    region: str = "UK"

    @property
    def is_missing(self) -> bool:
        return self.value is None

    @property
    def is_mock(self) -> bool:
        return self.status == "mock" or self.source == MOCK_SOURCE or "mock" in self.flags

    @classmethod
    def missing(cls, unit: str, source: str, note: str = "Not available yet.", **kw: Any) -> Metric:
        return cls(value=None, unit=unit, source=source, confidence="low", status="pending",
                   flags=["pending_source"], note=note, **kw)
