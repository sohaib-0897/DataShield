"""Train a candidate isolation forest on supplied prepared events."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from backend.app.analysis import FEATURE_SCHEMA_VERSION
from backend.app.schemas import EventIn
from ml.registry import FEATURES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True, help="Prepared events.jsonl")
    parser.add_argument("--output", required=True)
    dataset_kind = parser.add_mutually_exclusive_group(required=True)
    dataset_kind.add_argument("--synthetic-test", action="store_true", help="Mark this artifact test-only; it can never be registered")
    dataset_kind.add_argument("--real-dataset", action="store_true", help="Attest that the input is real; activation still requires reviewed evaluation")
    args = parser.parse_args()
    source = Path(args.dataset)
    if not source.is_file(): parser.error("Prepared dataset file is missing; run prepare_dataset first")
    try:
        import joblib
        from sklearn.ensemble import IsolationForest
    except ImportError:
        parser.error("Install requirements-ml.txt to train a model")
    grouped = defaultdict(Counter)
    resources = defaultdict(set)
    channels = defaultdict(set)
    fingerprint = hashlib.sha256()
    with source.open("rb") as stream:
        for line in stream:
            fingerprint.update(line)
            event = EventIn.model_validate_json(line)
            window_start = event.timestamp.replace(minute=0, second=0, microsecond=0)
            key = (event.username, window_start)
            values = grouped[key]
            values["total_event_count"] += 1
            values[{"FILE_CREATE":"file_create_count", "FILE_MODIFY":"file_modify_count", "FILE_DELETE":"file_delete_count",
                    "FILE_MOVE":"file_move_count", "USB_FILE_TRANSFER":"removable_transfer_count", "BLOCKED":"failed_blocked_count"}.get(event.event_type, "unmapped_event_count")] += 1
            if event.channel.value == "USB": values["usb_event_count"] += 1
            if event.channel.value == "UPLOAD": values["upload_count"] += 1
            if event.event_type in ("UPLOAD_ATTEMPT", "CLOUD_UPLOAD_ATTEMPT"): values["cloud_upload_attempt_count"] += 1
            if event.timestamp.hour < 6 or event.timestamp.hour >= 20: values["after_hours_count"] += 1
            if event.timestamp.weekday() >= 5: values["weekend_count"] += 1
            if event.metadata.get("sensitivity_label") in {"confidential", "restricted"}: values["sensitive_document_interaction_count"] += 1
            if str(event.metadata.get("extension", "")).lower() in {".zip", ".7z", ".rar", ".sql", ".db"}: values["unusual_extension_count"] += 1
            if event.resource_id: resources[key].add(event.resource_id)
            channels[key].add(event.channel.value)
    samples = []
    for key, values in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        values["unique_resource_count"] = len(resources[key])
        values["unique_channel_count"] = len(channels[key])
        values["event_frequency_per_hour"] = values["total_event_count"]
        samples.append([float(values.get(key, 0)) for key in FEATURES])
    if len(samples) < 20: parser.error("At least 20 user/day windows are required for a candidate training run")
    cut = max(1, int(len(samples) * .8))
    model = IsolationForest(n_estimators=100, random_state=42, contamination="auto")
    model.fit(samples[:cut])
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, folder / "model.joblib")
    metadata = {"model_type": "IsolationForest", "version": folder.name, "feature_schema_version": FEATURE_SCHEMA_VERSION, "window_minutes": 60,
                "dataset_id": fingerprint.hexdigest(), "dataset_kind": "SYNTHETIC_TEST" if args.synthetic_test else "REAL_UNVERIFIED",
                "evaluation_status": "NOT_EVALUATED", "status": "TEST" if args.synthetic_test else "CANDIDATE",
                "created_at": datetime.now(timezone.utc).isoformat(), "training_windows": cut, "holdout_windows": len(samples)-cut,
                "metrics": {"holdout_outlier_count": int(sum(model.predict(samples[cut:]) == -1))}}
    (folder / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata))


if __name__ == "__main__": main()
