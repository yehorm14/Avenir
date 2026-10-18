"""No look-ahead in the backtest (AGENTS rule 6): tiers depend only on base-year features."""
import pytest

pd = pytest.importorskip("pandas")
pytest.importorskip("scipy")

from ml_common import assign_tiers  # noqa: E402


def base_frame():
    return pd.DataFrame({"pay": [20, 30, 40, 50, 60, 70], "prior": [0.1, -0.2, 0.05, 0.3, 0.0, -0.1]},
                        index=list("ABCDEF"))


def test_tiers_ignore_future_outcomes():
    base = base_frame()
    before = assign_tiers(base)
    # A future outcome going missing for F must not move anyone between tiers.
    outcomes = pd.DataFrame({"rpg": [0.1, 0.2, 0.0, -0.1, 0.05, None]}, index=list("ABCDEF"))
    after = assign_tiers(base.join(outcomes))
    pd.testing.assert_frame_equal(before, after)
    assert before.loc["F", "ambitious"] and before.loc["E", "ambitious"]


def test_tiers_use_only_base_columns():
    base = base_frame()
    with_future = base.assign(rpg=[9, 9, 9, 9, 9, 9], jg=[None] * 6)
    pd.testing.assert_frame_equal(assign_tiers(base), assign_tiers(with_future))
