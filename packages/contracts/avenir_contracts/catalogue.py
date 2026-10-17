"""Catalogue and routes: the display data Yehor's ETL owns (packages/ml/CONTRACTS.md section 3).

Files: snapshots/catalogue.json and snapshots/routes.json, falling back to snapshots/mock/.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .metric import Metric
from .models import SOC, Route
from .vocab import MetricStatus, Subject


class CatalogueEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    soc2020: str = SOC
    title: str = Field(description="friendly title shown to a 17-year-old")
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    entry_subjects: list[Subject] = Field(default_factory=list)
    metrics: dict[str, Metric] = Field(default_factory=dict, description="keys from vocab.CATALOGUE_METRICS")


class CatalogueFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    status: MetricStatus
    entries: list[CatalogueEntry]


class RoutesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_at: str
    status: MetricStatus
    routes: list[Route]
