import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from sensitivity import calculate_hash, build_sensitive_hashes
from database import initialize_database, log_transfer


GOOGLE_DRIVE = r"G:\My Drive"

SENSITIVE_HASHES = {}


class GoogleDriveHandler(FileSystemEventHandler):

    def check_file(self, file_path):

        if not os.path.isfile(file_path):
            return

        file_path = os.path.abspath(file_path)

        print()
        print("Checking Google Drive file:")
        print(file_path)

        # Wait for Google Drive to finish writing/syncing
        previous_size = -1

        for _ in range(20):

            try:
                current_size = os.path.getsize(file_path)
            except OSError:
                time.sleep(0.5)
                continue

            if current_size == previous_size:
                break

            previous_size = current_size
            time.sleep(0.5)

        file_hash = calculate_hash(file_path)

        if not file_hash:
            return

        match = SENSITIVE_HASHES.get(file_hash)

        if not match:
            print("[GOOGLE DRIVE FILE] Not classified as sensitive")
            return

        source_path = match["source_path"]
        sensitivity = match["sensitivity"]

        print()
        print("===================================")
        print("[SENSITIVE GOOGLE DRIVE TRANSFER]")
        print("===================================")
        print(f"Source:      {source_path}")
        print(f"Destination: {file_path}")
        print(f"Sensitivity: {sensitivity}")
        print(f"SHA-256:     {file_hash}")
        print("===================================")

        log_transfer(
            event_type="SENSITIVE_CLOUD_COPY",
            source_path=source_path,
            destination_path=file_path,
            sensitivity=sensitivity,
            destination_type="GOOGLE_DRIVE",
            file_hash=file_hash
        )

    def on_created(self, event):

        if event.is_directory:
            return

        self.check_file(event.src_path)

    def on_moved(self, event):

        if event.is_directory:
            return

        self.check_file(event.dest_path)


def main():

    global SENSITIVE_HASHES

    initialize_database()

    print("===================================")
    print("   AI-DLP GOOGLE DRIVE MONITOR")
    print("===================================")

    print("Building sensitive file fingerprints...")

    SENSITIVE_HASHES = build_sensitive_hashes()

    print(
        f"Sensitive fingerprints loaded: "
        f"{len(SENSITIVE_HASHES)}"
    )

    print()
    print(f"Monitoring: {GOOGLE_DRIVE}")
    print("Destination type: GOOGLE_DRIVE")
    print("Press CTRL+C to stop.")
    print()

    if not os.path.exists(GOOGLE_DRIVE):

        print(
            f"ERROR: {GOOGLE_DRIVE} does not exist."
        )

        return

    observer = Observer()

    observer.schedule(
        GoogleDriveHandler(),
        GOOGLE_DRIVE,
        recursive=True
    )

    observer.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("Stopping Google Drive monitor...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()