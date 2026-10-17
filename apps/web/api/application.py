"""Same-origin production UI plus both API layers, using one contract envelope."""

from __future__ import annotations

import inspect
from functools import wraps
from pathlib import Path
from typing import Any

from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from avenir_api.app import create_app
from avenir_api.envelope import ok
from avenir_api.routes_read import ERROR_RESPONSES
from avenir_contracts import Envelope

from .main import app as experience
from .product_data import product_data


def _experience_endpoint(endpoint, sources):
    @wraps(endpoint)
    def wrapped(*args, **kwargs):
        return ok(endpoint(*args, **kwargs), sources)

    # Resolve forward annotations against their original module, not this wrapper.
    wrapped.__signature__ = inspect.signature(endpoint, eval_str=True)
    return wrapped


def create_application(web_dir: Path | None = None):
    app = create_app(data=product_data())
    app.title = "Aventier API"
    app.version = "1.1.0"
    app.description = "Career discovery, sourced evidence and deterministic decision comparisons. No API key is required."
    for route in experience.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api/"):
            app.add_api_route(
                route.path,
                _experience_endpoint(route.endpoint, app.state.data.statuses),
                methods=sorted(route.methods),
                response_model=Envelope[route.response_model or Any],
                responses=ERROR_RESPONSES,
                tags=["Experience"],
                name=route.name,
            )
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware("http")
    async def browser_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    built_web = web_dir if web_dir is not None else Path(__file__).resolve().parents[1] / "dist"
    if (built_web / "index.html").is_file():
        app.mount("/", StaticFiles(directory=built_web, html=True), name="web")
    else:

        @app.get("/", include_in_schema=False)
        def build_needed():
            return HTMLResponse(
                "<h1>Aventier API is ready</h1><p>Build the web app with npm run build in apps/web, then restart.</p>",
                status_code=503,
            )

    return app


app = create_application()
