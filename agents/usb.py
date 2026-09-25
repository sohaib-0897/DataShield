"""Windows removable drive insertion/removal collector using WMI change events."""
import logging
import platform
import threading
import time
from pathlib import Path

from watchdog.observers import Observer

from .common import event, send, heartbeat
from .filesystem import Handler


def main():
    if platform.system() != "Windows":
        raise SystemExit("USB monitoring requires Windows")
    import wmi
    client = wmi.WMI()
    watcher = client.watch_for(raw_wql="SELECT * FROM Win32_VolumeChangeEvent")
    logging.basicConfig(level=logging.INFO)
    def pulse():
        while True:
            try:
                heartbeat()
            except Exception as exc:
                logging.warning("Heartbeat failed: %s", type(exc).__name__)
            time.sleep(60)
    threading.Thread(target=pulse, daemon=True).start()
    watchers = {}
    while True:
        change = watcher()
        code = int(change.EventType)
        if code in (2, 3):
            drive = str(getattr(change, "DriveName", ""))
            if code == 2 and drive and drive not in watchers and Path(drive + "\\").is_dir():
                observer = Observer()
                observer.schedule(Handler(), drive + "\\", recursive=True)
                observer.start()
                watchers[drive] = observer
            elif code == 3 and drive in watchers:
                observer = watchers.pop(drive)
                observer.stop()
                observer.join(timeout=5)
            try:
                send(event("USB", "USB_INSERT" if code == 2 else "USB_REMOVE", drive, {"drive": drive}))
            except Exception as exc:
                logging.error("USB delivery failed: %s", type(exc).__name__)


if __name__ == "__main__": main()
