"""Synthetic training smoke: artifacts remain explicitly TEST only."""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ml.registry import load_artifact, score, validate_activation_evaluation
from ml.training.train_anomaly import main


def test_training_requires_explicit_dataset_kind(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["train", "--dataset", "events.jsonl", "--output", "candidate"])
    with pytest.raises(SystemExit):
        main()


def test_synthetic_train_roundtrip(tmp_path, monkeypatch):
    pytest.importorskip("sklearn")
    dataset = tmp_path / "synthetic.jsonl"
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with dataset.open("w", encoding="utf-8") as stream:
        for index in range(25):
            row = {"source_event_id": f"fake-{index}", "username": "synthetic.user", "machine_id": "FAKE-PC", "hostname": "FAKE-PC",
                   "timestamp": (start + timedelta(days=index)).isoformat(), "channel": "FILE", "event_type": "FILE_CREATE",
                   "resource_id": f"fake-{index}.txt", "metadata": {"synthetic": True}}
            stream.write(json.dumps(row) + "\n")
    artifact = tmp_path / "test-v1"
    monkeypatch.setattr(sys, "argv", ["train", "--dataset", str(dataset), "--output", str(artifact), "--synthetic-test"])
    main()
    with pytest.raises(ValueError, match="Synthetic test"):
        load_artifact(artifact)
    model, metadata = load_artifact(artifact, allow_test=True)
    assert metadata["status"] == "TEST"
    assert 0 <= score(model, {"total_event_count": 1}) <= 100
    metadata_path = artifact / "metadata.json"
    fingerprint = metadata["dataset_id"]
    metadata.pop("dataset_id")
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint"):
        load_artifact(artifact, allow_test=True)
    metadata["dataset_id"] = fingerprint
    metadata["feature_schema_version"] = "incompatible"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="Incompatible"):
        load_artifact(artifact, allow_test=True)


def test_candidate_activation_requires_distinct_reviewed_heldout_evaluation():
    fingerprint = "a" * 64
    with pytest.raises(ValueError, match="reviewed held-out"):
        validate_activation_evaluation({"dataset_id": fingerprint, "evaluation_status": "NOT_EVALUATED"})
    evaluation = {"dataset_id": "b" * 64, "metrics": {"precision": .8, "recall": .7, "f1": .74, "false_positive_rate": .03, "sample_count": 100}}
    assert validate_activation_evaluation({"dataset_id": fingerprint, "evaluation_status": "REVIEWED", "evaluation": evaluation}) == evaluation
    evaluation["dataset_id"] = fingerprint
    with pytest.raises(ValueError, match="distinct dataset"):
        validate_activation_evaluation({"dataset_id": fingerprint, "evaluation_status": "REVIEWED", "evaluation": evaluation})
