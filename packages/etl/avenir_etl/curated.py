"""Load the human-verified curated occupations table (data/curated/occupations.csv).

Every row must carry `verified_by`; anything else wrong is reported with its line number
and SOC so humans can fix the whole file in one pass.
"""
from __future__ import annotations

import csv
from pathlib import Path

from avenir_contracts.catalogue import CatalogueEntry
from avenir_contracts.vocab import SUBJECTS


class CuratedError(ValueError):
    """One or more curated rows are invalid. The message names every bad row."""


REQUIRED_COLUMNS = ("soc2020", "title", "aliases", "description", "entry_subjects", "verified_by")


def require_columns(reader: csv.DictReader, required: tuple[str, ...], csv_path: Path) -> None:
    """Raise CuratedError naming every required header column the file lacks."""
    missing = [c for c in required if c not in (reader.fieldnames or [])]
    if missing:
        raise CuratedError(f"{csv_path}: missing required column(s): {', '.join(missing)}")


def _split(cell: str | None) -> list[str]:
    return [p.strip() for p in (cell or "").split("|") if p.strip()]


def load_curated(csv_path: Path, demo_socs: set[str]) -> list[CatalogueEntry]:
    entries: list[CatalogueEntry] = []
    problems: list[str] = []
    seen: set[str] = set()
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        require_columns(reader, REQUIRED_COLUMNS, csv_path)
        for row in reader:
            where = f"line {reader.line_num} (soc2020 {(row.get('soc2020') or '').strip()})"
            soc = (row.get("soc2020") or "").strip()
            title = (row.get("title") or "").strip()
            subjects = _split(row.get("entry_subjects"))
            errs: list[str] = []
            if not (row.get("verified_by") or "").strip():
                errs.append("verified_by is empty (a team member must verify the row)")
            if soc not in demo_socs:
                errs.append("SOC is not in the ML demo set")
            if soc in seen:
                errs.append("duplicate SOC")
            if not title:
                errs.append("title is empty")
            bad = [s for s in subjects if s not in SUBJECTS]
            if bad:
                errs.append(f"unknown entry_subjects {bad} (allowed: {', '.join(SUBJECTS)})")
            seen.add(soc)
            if errs:
                problems.extend(f"{where}: {e}" for e in errs)
                continue
            entries.append(CatalogueEntry(
                soc2020=soc, title=title, aliases=_split(row.get("aliases")),
                description=(row.get("description") or "").strip() or None,
                entry_subjects=subjects,  # type: ignore[arg-type]
            ))
    if not entries and not problems:
        raise CuratedError(f"{csv_path}: no data rows (the catalogue would be empty)")
    if problems:
        raise CuratedError(f"{csv_path}: {len(problems)} problem(s)\n" + "\n".join(problems))
    return entries
