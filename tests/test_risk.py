"""Boundaries and explanations for the deterministic, non-probabilistic risk formula."""
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.analysis import assess, behavior, classify
from app.schemas import PolicyConfig


def event(event_type="FILE_CREATE", channel="FILE", metadata=None):
    return SimpleNamespace(event_type=event_type, channel=channel, metadata=metadata or {})


def test_risk_score_minimum_and_maximum_are_bounded():
    only_anomaly = {"anomaly": 1, "sensitivity": 0, "activity": 0, "channel": 0, "history": 0}
    config = PolicyConfig(weights=only_anomaly)
    low = assess(event(), {"score": 0, "source": "UNAVAILABLE"}, {"score": 0, "source": "UNAVAILABLE", "reason": "missing"}, 0, config)
    high = assess(event(), {"score": 100, "source": "MODEL"}, {"score": 100, "source": "MODEL", "reason": "score"}, 100, config)
    assert low["score"] == 0 and low["severity"] == "LOW"
    assert high["score"] == 100 and high["severity"] == "CRITICAL"


@pytest.mark.parametrize(("score", "severity"), [
    (0, "LOW"), (34.99, "LOW"), (35, "MEDIUM"), (64.99, "MEDIUM"),
    (65, "HIGH"), (84.99, "HIGH"), (85, "CRITICAL"), (100, "CRITICAL"),
])
def test_each_severity_boundary(score, severity):
    weights = {"anomaly": 0, "sensitivity": 1, "activity": 0, "channel": 0, "history": 0}
    result = assess(event(), {"score": score, "source": "RULE"}, {"score": 0, "source": "INSUFFICIENT_HISTORY", "reason": "few windows"}, 0,
                    PolicyConfig(weights=weights))
    assert result["score"] == score
    assert result["severity"] == severity


def test_cnic_detection_and_high_behavioral_deviation_raise_explained_score():
    sensitive = classify(event(metadata={"sample_text": "Synthetic 12345-1234567-1"}))
    deviation = behavior({"total_event_count": 10}, [1, 1, 1])
    assert sensitive["label"] == "restricted"
    assert sensitive["score"] == 90 and sensitive["source"] == "RULE"
    assert deviation["source"] == "HEURISTIC" and deviation["score"] == 100
    result = assess(event("UPLOAD_ATTEMPT", "UPLOAD"), sensitive, deviation, 20, PolicyConfig())
    assert result["score"] == sum(result["contributions"].values())
    assert result["score"] <= 100
    assert result["contributions"]["sensitivity"] == 27
    assert result["anomaly_source"] == "HEURISTIC"


def test_unavailable_analysis_is_not_mislabeled_as_heuristic():
    result = assess(event(), {"score": 0, "source": "UNAVAILABLE"},
                    {"score": 0, "source": "UNAVAILABLE", "reason": "missing"}, 0, PolicyConfig())
    assert result["anomaly_source"] == "UNAVAILABLE"
    assert result["score"] == result["contributions"]["activity"] + result["contributions"]["channel"]


def test_invalid_threshold_order_and_unbalanced_weights_are_rejected():
    with pytest.raises(ValidationError):
        PolicyConfig(medium_threshold=70, high_threshold=65)
    with pytest.raises(ValidationError):
        PolicyConfig(weights={"anomaly": .5, "sensitivity": .3, "activity": .2, "channel": .2, "history": .1})
