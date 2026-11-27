"""Presentation metadata derived from the supplied evidence, without changing metrics."""

import re

from pathfinder_ml import ML


def evidence_metadata(evidence: ML) -> dict[str, str]:
    occupations = evidence.occupations_meta()
    price_base = occupations.get("price_base", "")
    tax_year = re.search(r"tax year (\d{4}/\d{2})", price_base, re.IGNORECASE)
    return {
        "schema_version": occupations.get("schema_version", ""),
        "price_base": price_base,
        "price_label": f"{tax_year[1]} prices" if tax_year else price_base or "the supplied price base",
    }


def demand_comparison(metric: dict) -> str:
    return " relative to the typical occupation" if "typical_occupation_trend" in metric.get("extra", {}) else ""
