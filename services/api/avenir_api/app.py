"""Avenir FastAPI app: envelope on every response, no tracebacks, runs without keys."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from avenir_contracts import (
    AdsSource,
    AvenirData,
    Envelope,
    ErrorCode,
    ErrorDetail,
    ExplanationWriter,
    SourceStatus,
    TagSuggester,
    load_data,
)

from .deps import default_ports
from .envelope import fail, ok
from .routes_read import ERROR_RESPONSES
from .routes_read import router as read_router
from .routes_write import router as write_router

log = logging.getLogger("avenir_api")


class HealthOut(BaseModel):
    status: str
    ml_mode: str
    sources: list[SourceStatus]


def create_app(
    data: AvenirData | None = None,
    ads: AdsSource | None = None,
    writer: ExplanationWriter | None = None,
    suggester: TagSuggester | None = None,
) -> FastAPI:
    app = FastAPI(title="Avenir API", version="1")
    d_ads, d_writer, d_suggester = default_ports()
    app.state.data = data if data is not None else load_data()
    app.state.ads = ads if ads is not None else d_ads
    app.state.writer = writer if writer is not None else d_writer
    app.state.suggester = suggester if suggester is not None else d_suggester

    # Registered before CORS so it sits inside it: a crash still gets CORS headers and the
    # browser can read the INTERNAL envelope (Starlette's own 500 handler runs outside CORS).
    @app.middleware("http")
    async def _catch_all(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            log.error("Unhandled error on %s", request.url.path, exc_info=exc)
            return fail(ErrorCode.INTERNAL, "Something went wrong")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        details = [
            ErrorDetail(
                field="body" if e["type"] == "json_invalid" else ".".join(map(str, e["loc"])),
                issue=e["msg"],
            )
            for e in exc.errors()
        ]
        return fail(ErrorCode.VALIDATION_ERROR, "Invalid request", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        if exc.status_code in (404, 405):
            code, msg = ErrorCode.NOT_FOUND, "Not found"
        elif 400 <= exc.status_code < 500:
            code, msg = ErrorCode.VALIDATION_ERROR, "Invalid request"
        else:
            log.warning("HTTP %s on %s", exc.status_code, request.url.path)
            code, msg = ErrorCode.INTERNAL, "Something went wrong"
        resp = fail(code, msg)
        resp.status_code = exc.status_code
        if exc.status_code == 429 and exc.headers:  # keep Retry-After from the public rate limit
            resp.headers.update(exc.headers)
        return resp

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.error("Unhandled error on %s", request.url.path, exc_info=exc)
        return fail(ErrorCode.INTERNAL, "Something went wrong")

    app.include_router(read_router)
    app.include_router(write_router)

    @app.get("/health", response_model=Envelope[HealthOut], responses=ERROR_RESPONSES)
    def health():
        d = app.state.data
        sources = [s.model_dump(mode="json") for s in d.statuses]
        return ok({"status": "ok", "ml_mode": d.ml_mode, "sources": sources}, d.statuses)

    return app


app = create_app()
