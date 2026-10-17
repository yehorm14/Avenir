"""0-100 percentile ranks within one set of occupations.

Pure function: no I/O, no network, no LLM. A missing value (None) stays None and is not
ranked, so it never shifts the other ranks.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Mapping


def rank_0_100(values: Mapping[str, float | None], higher_is_better: bool = True) -> dict[str, float | None]:
    """Percentile rank of each value among the non-missing values, 0 (worst) to 100 (best).

    Ties share the average of their rank positions. A single ranked value scores 50.
    Results are rounded to one decimal place and keep the input key order.
    """
    present = {k: (v if higher_is_better else -v) for k, v in values.items() if v is not None}
    ordered = sorted(present.values())
    n = len(ordered)

    def average_position(v: float) -> float:
        first = bisect_left(ordered, v)
        last = bisect_right(ordered, v) - 1
        return (first + last) / 2

    ranks: dict[str, float | None] = {}
    for key, value in values.items():
        if value is None:
            ranks[key] = None
        elif n == 1:
            ranks[key] = 50.0
        else:
            ranks[key] = round(average_position(present[key]) / (n - 1) * 100, 1)
    return ranks
