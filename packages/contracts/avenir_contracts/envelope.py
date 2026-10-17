"""The one response envelope every endpoint returns (docs/contracts.md)."""
from __future__ import annotations

from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .vocab import SourceState

T = TypeVar("T")


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"   # 422
    NOT_FOUND = "NOT_FOUND"                 # 404
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"  # 503, live source down and no snapshot
    INTERNAL = "INTERNAL"                   # 500


HTTP_STATUS: dict[ErrorCode, int] = {
    ErrorCode.VALIDATION_ERROR: 422,
    ErrorCode.NOT_FOUND: 404,
    ErrorCode.UPSTREAM_UNAVAILABLE: 503,
    ErrorCode.INTERNAL: 500,
}


class SourceStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    status: SourceState
    as_of: str | None = None
    region: str = "UK"


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str | None = None
    issue: str


class ErrorBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: ErrorCode
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class Meta(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_of: str
    request_id: str
    sources: list[SourceStatus] = Field(default_factory=list)


class Envelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")
    ok: bool
    data: T | None = None
    error: ErrorBody | None = None
    meta: Meta
