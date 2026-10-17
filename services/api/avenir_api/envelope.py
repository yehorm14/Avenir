"""Build the contract envelope for every response."""
from __future__ import annotations

import math
from datetime import date
from typing import Any
from uuid import uuid4

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from avenir_contracts import HTTP_STATUS, Envelope, ErrorBody, ErrorCode, ErrorDetail, Meta, SourceStatus


def _meta(sources: list[SourceStatus]) -> Meta:
    return Meta(as_of=date.today().isoformat(), request_id=uuid4().hex[:12], sources=sources)


def _finite(v: Any) -> Any:
    """NaN and infinity are not valid JSON; send them as null (missing)."""
    if isinstance(v, float) and not math.isfinite(v):
        return None
    if isinstance(v, dict):
        return {k: _finite(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_finite(x) for x in v]
    return v


def _respond(env: Envelope[Any], status: int) -> JSONResponse:
    return JSONResponse(
        _finite(jsonable_encoder(env.model_dump(mode="json"))),
        status_code=status,
        headers={"X-Request-ID": env.meta.request_id},
    )


def ok(data: Any, sources: list[SourceStatus]) -> JSONResponse:
    return _respond(Envelope[Any](ok=True, data=data, meta=_meta(sources)), 200)


def fail(code: ErrorCode, message: str, details: list[ErrorDetail] | None = None) -> JSONResponse:
    body = ErrorBody(code=code, message=message, details=list(details or []))
    return _respond(Envelope[Any](ok=False, error=body, meta=_meta([])), HTTP_STATUS[code])
