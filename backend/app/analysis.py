"""Deterministic sensitivity, feature and risk analysis; no trained model implied."""
import re
from collections import Counter
from datetime import timedelta, timezone
from pathlib import PurePath

from .schemas import PolicyConfig

FEATURE_SCHEMA_VERSION = "event-window-v2"
SCORING_VERSION = "weighted-v1"
CNIC = re.compile(r"\b\d{5}-\d{7}-\d\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def detections(text):
    results = []
    for name, pattern in (("CNIC", CNIC), ("EMAIL", EMAIL)):
        found = pattern.findall(text[:32768])
        if found:
            masked = [f[:2] + "***" + f[-2:] for f in found[:5]]
            results.append({"type": name, "count": len(found), "masked": masked, "source": "RULE", "version": "patterns-v1"})
    return results


def classify(event):
    text = str(event.metadata.get("sample_text", ""))[:32768]
    found = detections(text)
    declared = event.metadata.get("sensitivity_label")
    if found:
        label, score = "restricted", 90.0
    elif declared in {"public", "internal", "confidential", "restricted"}:
        label, score = declared, {"public": 0, "internal": 20, "confidential": 70, "restricted": 90}[declared]
    else:
        label, score = "unclassified", 0.0
    return {"label": label, "score": score, "confidence": 1.0 if found else 0.5 if declared else 0.0,
            "source": "RULE" if found else "DECLARED" if declared else "UNAVAILABLE", "model_version": None, "detections": found}


def features(events, start, end):
    # SQLite used in isolated tests drops timezone info; persisted timestamps are UTC.
    events = [e for e in events if start <= (e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp) < end]
    types = Counter(e.event_type for e in events)
    channels = Counter(e.channel for e in events)
    unusual_extensions = {".zip", ".7z", ".rar", ".sql", ".db"}
    def metadata(e):
        return getattr(e, "details", None) or getattr(e, "metadata", {}) or {}
    return {
        "total_event_count": len(events), "file_create_count": types["FILE_CREATE"],
        "file_modify_count": types["FILE_MODIFY"], "file_delete_count": types["FILE_DELETE"],
        "file_move_count": types["FILE_MOVE"], "usb_event_count": channels["USB"],
        "upload_count": channels["UPLOAD"], "unique_resource_count": len({e.resource_id for e in events if e.resource_id}),
        "unique_channel_count": len(channels), "after_hours_count": sum(e.timestamp.hour < 6 or e.timestamp.hour >= 20 for e in events),
        "weekend_count": sum(e.timestamp.weekday() >= 5 for e in events),
        "event_frequency_per_hour": round(len(events) / max((end-start).total_seconds()/3600, 1/60), 2),
        "removable_transfer_count": types["USB_FILE_TRANSFER"],
        "cloud_upload_attempt_count": types["UPLOAD_ATTEMPT"] + types["CLOUD_UPLOAD_ATTEMPT"],
        "failed_blocked_count": types["BLOCKED"],
        "sensitive_document_interaction_count": sum(metadata(e).get("classified_sensitivity_label", metadata(e).get("sensitivity_label")) in {"confidential", "restricted"} for e in events),
        "unusual_extension_count": sum(str(metadata(e).get("extension", "")).lower() in unusual_extensions for e in events),
    }


def behavior(current, previous_counts):
    if len(previous_counts) < 3:
        return {"score": 0.0, "source": "INSUFFICIENT_HISTORY", "reason": "At least three prior windows are required"}
    average = sum(previous_counts) / len(previous_counts)
    excess = max(0, current["total_event_count"] - average)
    score = min(100.0, round(excess / max(average, 1) * 30, 2))
    return {"score": score, "source": "HEURISTIC", "reason": "30 points per multiple above mean prior event count, capped at 100"}


def assess(event, classification, behavioral, history, policy: PolicyConfig):
    activity = {"FILE_DELETE": 45, "USB_FILE_TRANSFER": 85, "UPLOAD_ATTEMPT": 75, "CLOUD_UPLOAD_ATTEMPT": 70, "FILE_MOVE": 30}.get(event.event_type, 15)
    channel = {"FILE": 15, "USB": 70, "CLOUD": 65, "UPLOAD": 65, "NETWORK": 20}[event.channel.value if hasattr(event.channel, "value") else event.channel]
    components = {"anomaly": behavioral["score"], "sensitivity": classification["score"], "activity": activity,
                  "channel": channel, "history": min(100, history)}
    contributions = {key: round(value * policy.weights[key], 2) for key, value in components.items()}
    score = round(min(100, sum(contributions.values())), 2)
    severity = "CRITICAL" if score >= policy.critical_threshold else "HIGH" if score >= policy.high_threshold else "MEDIUM" if score >= policy.medium_threshold else "LOW"
    return {"score": score, "severity": severity, "components": components, "contributions": contributions,
            "anomaly_source": behavioral["source"], "anomaly_reason": behavioral["reason"],
            "anomaly_model_version": behavioral.get("model_version"), "classifier_source": classification["source"],
            "classifier_reason": classification.get("fallback_reason"),
            "classifier_model_version": classification.get("model_version"), "rule_version": "patterns-v1",
            "feature_schema_version": FEATURE_SCHEMA_VERSION, "scoring_version": SCORING_VERSION,
            "policy_threshold": policy.alert_threshold}
