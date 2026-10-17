"""Avenir FastAPI app: envelope on every response, no tracebacks, runs without keys."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from avenir_contracts import (
    AdsSource,
    AvenirData,
    ErrorCode,
    ErrorDetail,
    ExplanationWriter,
    TagSuggester,
    load_data,
)

from .deps import default_ports
from .envelope import fail, ok
from .routes_read import router as read_router

log = logging.getLogger("avenir_api")


def create_app(
    data: AvenirData | None = None,
    ads: AdsSource | None = None,
    writer: ExplanationWriter | None = None,
    suggester: TagSuggester | None = None,
) -> FastAPI:
    app = FastAPI(title="Avenir API", version="1")
    d_ads, d_writer, d_suggester = default_ports()
    app.state.data = data if data is not None else load_data()
    app.state.ads = ads or d_ads
    app.state.writer = writer or d_writer
    app.state.suggester = suggester or d_suggester

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        details = [ErrorDetail(field=".".join(map(str, e["loc"])), issue=e["msg"]) for e in exc.errors()]
        return fail(ErrorCode.VALIDATION_ERROR, "Invalid request", details)

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            return fail(ErrorCode.NOT_FOUND, "Not found")
        log.warning("HTTP %s on %s", exc.status_code, request.url.path)
        return fail(ErrorCode.INTERNAL, "Something went wrong")

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.error("Unhandled error on %s", request.url.path, exc_info=exc)
        return fail(ErrorCode.INTERNAL, "Something went wrong")

    app.include_router(read_router)

    @app.get("/health")
    def health():
        d = app.state.data
        sources = [s.model_dump(mode="json") for s in d.statuses]
        return ok({"status": "ok", "ml_mode": d.ml_mode, "sources": sources}, d.statuses)

    return app


app = create_app()
