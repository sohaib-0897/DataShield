"""Source labels remain truthful when no NLP artifact is configured."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.sensitivity import ModelSensitivityClassifier, RuleBasedSensitivityClassifier


def test_rule_and_unavailable_sources():
    classifier = RuleBasedSensitivityClassifier()
    matched = classifier.classify({}, "Synthetic identifier 12345-1234567-1")
    assert matched["source"] == "RULE"
    assert matched["detections"][0]["masked"] == ["12***-1"]
    assert classifier.classify({}, "ordinary text")["source"] == "UNAVAILABLE"


def test_missing_model_artifact_is_explicit(tmp_path):
    with pytest.raises(FileNotFoundError):
        ModelSensitivityClassifier(tmp_path / "missing")
