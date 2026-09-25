"""Watchdog collector; configure DATASHIELD_MONITOR_FOLDERS explicitly."""
import logging
import os
import platform
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .common import event, send, heartbeat

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOG = logging.getLogger(__name__)


def removable(path):
    if platform.system() != "Windows":
        return False
    import ctypes
    drive = Path(path).drive
    return bool(drive and ctypes.windll.kernel32.GetDriveTypeW(drive + "\\") == 2)


class Handler(FileSystemEventHandler):
    def __init__(self):
        self.recent = {}
        self.extensions = {x.strip().lower() for x in os.getenv("DATASHIELD_EXTENSIONS", ".txt,.csv,.pdf,.docx,.xlsx,.json").split(",")}
        self.max_scan = min(12000, max(0, int(os.getenv("DATASHIELD_SCAN_BYTES", "8192"))))

    def on_any_event(self, change):
        if change.is_directory or change.event_type not in {"created", "modified", "deleted", "moved"}:
            return
        path = Path(getattr(change, "dest_path", change.src_path))
        if path.suffix.lower() not in self.extensions:
            return
        key = (str(path), change.event_type)
        current = time.monotonic()
        if current - self.recent.get(key, 0) < 1.5:
            return
        self.recent[key] = current
        if len(self.recent) > 1000:
            self.recent = {k: v for k, v in self.recent.items() if current-v < 3}
        metadata = {"filename": path.name, "extension": path.suffix.lower()}
        if change.event_type != "deleted":
            for attempt in range(3):
                try:
                    metadata["size"] = path.stat().st_size
                    if path.suffix.lower() in {".txt", ".csv", ".json"} and metadata["size"] <= self.max_scan:
                        metadata["sample_text"] = path.read_bytes()[:self.max_scan].decode("utf-8", errors="ignore")
                    break
                except (OSError, PermissionError):
                    time.sleep(.1 * (attempt+1))
        try:
            is_transfer = removable(path) and change.event_type in {"created", "moved"}
            result = send(event("USB" if is_transfer else "FILE", "USB_FILE_TRANSFER" if is_transfer else "FILE_" + {"created":"CREATE","modified":"MODIFY","deleted":"DELETE","moved":"MOVE"}[change.event_type], str(path), metadata))
            LOG.info("event=%s type=%s alert=%s", result["event_id"], change.event_type, result.get("alert_id"))
        except Exception as exc:
            LOG.error("File event delivery failed: %s", type(exc).__name__)


def main():
    folders = [Path(p.strip()) for p in os.getenv("DATASHIELD_MONITOR_FOLDERS", "").split(os.pathsep) if p.strip()]
    if not folders:
        raise SystemExit("Set DATASHIELD_MONITOR_FOLDERS to explicit paths separated by the OS path separator")
    observer = Observer()
    handler = Handler()
    for folder in folders:
        if folder.is_dir():
            observer.schedule(handler, str(folder), recursive=True)
            LOG.info("Monitoring %s", folder)
    observer.start()
    try:
        while True:
            try:
                heartbeat()
            except Exception as exc:
                LOG.warning("Heartbeat failed: %s", type(exc).__name__)
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__": main()
