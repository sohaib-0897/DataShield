"""Local artifact contract for an optional anomaly model."""
import json
import re
from pathlib import Path

from backend.app.analysis import FEATURE_SCHEMA_VERSION

FEATURES = ["total_event_count", "file_create_count", "file_modify_count", "file_delete_count", "file_move_count",
            "usb_event_count", "upload_count", "unique_resource_count", "unique_channel_count", "after_hours_count",
            "weekend_count", "event_frequency_per_hour", "removable_transfer_count", "cloud_upload_attempt_count", "failed_blocked_count",
            "sensitive_document_interaction_count", "unusual_extension_count"]


def validate_activation_evaluation(metadata):
    evaluation = metadata.get("evaluation")
    fingerprint = str(evaluation.get("dataset_id", "")) if isinstance(evaluation, dict) else ""
    metrics = evaluation.get("metrics", {}) if isinstance(evaluation, dict) else {}
    required = {"precision", "recall", "f1", "false_positive_rate", "sample_count"}
    if metadata.get("evaluation_status") != "REVIEWED" or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise ValueError("Candidate requires a separately fingerprinted, reviewed held-out evaluation")
    if fingerprint == metadata.get("dataset_id") or not required.issubset(metrics):
        raise ValueError("Evaluation must use a distinct dataset and include precision, recall, F1, false-positive rate, and sample count")
    try:
        values = [float(metrics[key]) for key in ("precision", "recall", "f1", "false_positive_rate")]
        sample_count = int(metrics["sample_count"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Evaluation metrics must be numeric") from exc
    if sample_count < 1 or any(value < 0 or value > 1 for value in values):
        raise ValueError("Evaluation metrics must be in [0, 1] and sample_count must be positive")
    return evaluation


def load_artifact(directory, allow_test=False):
    import joblib
    folder = Path(directory)
    metadata = json.loads((folder / "metadata.json").read_text(encoding="utf-8"))
    if not re.fullmatch(r"[0-9a-f]{64}", str(metadata.get("dataset_id", ""))):
        raise ValueError("Missing or invalid dataset fingerprint")
    status = metadata.get("status")
    if status not in {"TEST", "CANDIDATE"}:
        raise ValueError("Missing or invalid artifact status")
    if status != "TEST" and metadata.get("dataset_kind") != "REAL_UNVERIFIED":
        raise ValueError("Candidate must identify a real, non-synthetic dataset")
    if status == "TEST" and not allow_test:
        raise ValueError("Synthetic test artifacts cannot be activated")
    if metadata["feature_schema_version"] != FEATURE_SCHEMA_VERSION:
        raise ValueError("Incompatible feature schema")
    if metadata.get("window_minutes") != 60:
        raise ValueError("Incompatible feature window duration")
    return joblib.load(folder / "model.joblib"), metadata


def score(model, values):
    sample = [[float(values.get(key, 0)) for key in FEATURES]]
    # IsolationForest decision scores have no calibrated probability interpretation.
    return max(0.0, min(100.0, round(50 - float(model.decision_function(sample)[0]) * 100, 2)))
