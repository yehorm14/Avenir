from avenir_contracts import Metric
from avenir_decision.confidence import component_confidence, downgrade, lowest


def _metric(value: float | None, confidence: str = "high") -> Metric:
    return Metric(value=value, unit="GBP", source="test", confidence=confidence)


def test_lowest_picks_weakest_level():
    assert lowest("high", "medium") == "medium"
    assert lowest("high", "high") == "high"
    assert lowest("low", "high", "medium") == "low"


def test_downgrade_steps_one_level_and_floors_at_low():
    assert downgrade("high") == "medium"
    assert downgrade("medium") == "low"
    assert downgrade("low") == "low"


def test_component_uses_lowest_present_metric():
    assert component_confidence([_metric(1, "high"), _metric(2, "medium")]) == "medium"


def test_component_downgrades_once_when_any_input_missing():
    metrics = [_metric(1, "high"), _metric(2, "high"), _metric(None, "high")]
    assert component_confidence(metrics) == "medium"


def test_component_treats_none_input_as_missing():
    assert component_confidence([_metric(1, "high"), None]) == "medium"


def test_component_all_missing_is_low():
    assert component_confidence([None, _metric(None, "high")]) == "low"
