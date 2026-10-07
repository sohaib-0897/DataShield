import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from database import initialize_database, log_activity
from sensitivity import get_sensitivity


WATCH_DIRECTORY = r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files"


class ActivityHandler(FileSystemEventHandler):

    def process_event(self, event_type, path):

        if os.path.isdir(path):
            return

        sensitivity = get_sensitivity(path)

        log_activity(
            event_type,
            path,
            sensitivity
        )

        print(
            f"[{event_type}] "
            f"{path} "
            f"| Sensitivity: {sensitivity}"
        )

    def on_modified(self, event):
        self.process_event("MODIFIED", event.src_path)

    def on_created(self, event):
        self.process_event("CREATED", event.src_path)

    def on_deleted(self, event):
        self.process_event("DELETED", event.src_path)

    def on_moved(self, event):
        self.process_event("MOVED", event.dest_path)


initialize_database()

event_handler = ActivityHandler()

observer = Observer()

observer.schedule(
    event_handler,
    WATCH_DIRECTORY,
    recursive=True
)

observer.start()

print("===================================")
print("       AI-DLP MONITORING AGENT")
print("===================================")
print(f"Monitoring: {WATCH_DIRECTORY}")
print("Status: ACTIVE")
print("Press CTRL+C to stop.")
print()

try:
    while True:
        pass

except KeyboardInterrupt:
    observer.stop()

observer.join()