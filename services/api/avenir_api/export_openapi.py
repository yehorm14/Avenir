"""Write docs/openapi.json for the frontend's client generator: `make openapi`."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI

from avenir_contracts import AvenirData

from .app import create_app

OUT = Path(__file__).resolve().parents[3] / "docs" / "openapi.json"


def render(app: FastAPI) -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> None:
    OUT.write_text(render(create_app(data=AvenirData())))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
