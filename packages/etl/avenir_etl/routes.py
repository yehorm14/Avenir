"""Load the human-verified routes table (data/curated/routes.csv) into a RoutesFile.

Humans copy each route from its real page (apprenticeships.scot, Graduate Apprenticeships,
university course pages, Find an Apprenticeship) and paste the page URL. Every route keeps
its `nation`, so the roadmap can offer a student only routes in their own nation.
Same row-error style as curated.py: every bad row is reported with its line number and SOC.
"""
from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import get_args

from avenir_contracts.catalogue import RoutesFile
from avenir_contracts.models import Route
from avenir_contracts.vocab import Nation, RouteKind

from .curated import CuratedError, require_columns

REQUIRED_COLUMNS = ("soc2020", "nation", "kind", "name", "provider", "entry_requirements", "url", "source",
                    "verified_by")
NATIONS = get_args(Nation)
KINDS = get_args(RouteKind)
NOT_EMPTY = ("name", "entry_requirements", "url", "source")


def load_routes(csv_path: Path, demo_socs: set[str], *, generated_at: str | None = None) -> RoutesFile:
    routes: list[Route] = []
    problems: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()
    with Path(csv_path).open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        require_columns(reader, REQUIRED_COLUMNS, csv_path)
        for raw in reader:
            row = {k: (raw.get(k) or "").strip() for k in REQUIRED_COLUMNS}
            where = f"line {reader.line_num} (soc2020 {row['soc2020']})"
            errs: list[str] = []
            if not row["verified_by"]:
                errs.append("verified_by is empty (a team member must verify the row)")
            if row["soc2020"] not in demo_socs:
                errs.append("SOC is not in the ML demo set")
            if row["nation"] not in NATIONS:
                errs.append(f"unknown nation {row['nation']!r} (allowed: {', '.join(NATIONS)})")
            if row["kind"] not in KINDS:
                errs.append(f"unknown kind {row['kind']!r} (allowed: {', '.join(KINDS)})")
            errs.extend(f"{c} is empty" for c in NOT_EMPTY if not row[c])
            if row["url"] and not row["url"].startswith("https://"):
                errs.append("url must start with https://")
            key = (row["soc2020"], row["nation"], row["kind"], row["name"])
            if key in seen:
                errs.append("duplicate (soc2020, nation, kind, name)")
            seen.add(key)
            if errs:
                problems.extend(f"{where}: {e}" for e in errs)
                continue
            routes.append(Route(
                soc2020=row["soc2020"], nation=row["nation"], kind=row["kind"],  # type: ignore[arg-type]
                name=row["name"], provider=row["provider"] or None,
                entry_requirements=row["entry_requirements"], url=row["url"], source=row["source"],
                verified_by=row["verified_by"],
            ))
    if problems:
        raise CuratedError(f"{csv_path}: {len(problems)} problem(s)\n" + "\n".join(problems))
    return RoutesFile(generated_at=generated_at or datetime.now(UTC).isoformat(timespec="seconds"),
                      status="preliminary", routes=routes)
