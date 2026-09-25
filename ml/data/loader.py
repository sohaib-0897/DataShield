"""Chunked expected-format CSV mapping; input must be supplied by the operator."""
import csv
from datetime import datetime, timezone
from pathlib import Path

SOURCES = {
    "file.csv": ("FILE", {"id", "date", "user", "pc", "filename", "activity"}),
    "device.csv": ("USB", {"id", "date", "user", "pc", "activity"}),
    "http.csv": ("CLOUD", {"id", "date", "user", "pc", "url"}),
}


def parse_time(value):
    for pattern in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, pattern).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()


def iter_records(directory):
    folder = Path(directory)
    if not folder.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {folder}. Supply CERT files locally; no download is performed.")
    found_files = False
    for filename, (channel, required) in SOURCES.items():
        path = folder / filename
        if not path.is_file():
            continue
        found_files = True
        with path.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{filename} missing columns: {', '.join(sorted(missing))}")
            for row in reader:
                try:
                    activity = row.get("activity", "").strip().upper().replace(" ", "_").replace("-", "_")
                    if channel in ("FILE", "USB") and not activity:
                        raise ValueError("Missing activity value")
                    kind = ("FILE_" + activity) if channel == "FILE" else ("USB_" + activity) if channel == "USB" else "CLOUD_VISIT"
                    yield {"source_event_id": filename + ":" + row["id"], "username": row["user"], "machine_id": row["pc"],
                           "hostname": row["pc"], "timestamp": parse_time(row["date"]), "channel": channel, "event_type": kind,
                           "resource_id": row.get("filename") or row.get("url"), "metadata": {"synthetic": False}, "source": "cert-import"}
                except (ValueError, KeyError) as exc:
                    yield {"invalid": str(exc), "source_file": filename, "row_id": row.get("id")}
    if not found_files:
        raise FileNotFoundError(f"No supported CSV files found in {folder}; expected {', '.join(SOURCES)}")
