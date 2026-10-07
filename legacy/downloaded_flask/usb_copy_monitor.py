import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from sensitivity import (
    calculate_hash,
    build_sensitive_hashes
)

from database import (
    initialize_database,
    log_transfer
)


USB_DRIVE = r"E:\\"

SENSITIVE_HASHES = {}


class USBFileHandler(FileSystemEventHandler):

    def check_file(self, file_path):

        if not os.path.isfile(file_path):
            return

        file_path = os.path.abspath(file_path)

        print()
        print("Checking USB file:")
        print(file_path)

        # Wait for the copy operation to finish
        previous_size = -1

        for _ in range(10):

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

        if match:

            source_path = match["source_path"]
            sensitivity = match["sensitivity"]

            print()
            print("===================================")
            print("[SENSITIVE FILE COPIED TO USB]")
            print("===================================")
            print(f"Source:      {source_path}")
            print(f"Destination: {file_path}")
            print(f"Sensitivity: {sensitivity}")
            print(f"SHA-256:     {file_hash}")
            print("===================================")

            log_transfer(
                event_type="SENSITIVE_USB_COPY",
                source_path=source_path,
                destination_path=file_path,
                sensitivity=sensitivity,
                destination_type="USB",
                file_hash=file_hash
            )

        else:

            print()
            print("[USB FILE] Not classified as sensitive")


    def on_created(self, event):

        if event.is_directory:
            return

        self.check_file(
            event.src_path
        )


    def on_moved(self, event):

        if event.is_directory:
            return

        self.check_file(
            event.dest_path
        )


def main():

    global SENSITIVE_HASHES

    initialize_database()

    print("===================================")
    print("      AI-DLP USB COPY MONITOR")
    print("===================================")

    print("Building sensitive file fingerprints...")

    SENSITIVE_HASHES = build_sensitive_hashes()

    print(
        f"Sensitive file fingerprints loaded: "
        f"{len(SENSITIVE_HASHES)}"
    )

    print()
    print(f"Monitoring USB: {USB_DRIVE}")
    print("Press CTRL+C to stop.")
    print()

    if not os.path.exists(USB_DRIVE):

        print(
            f"ERROR: {USB_DRIVE} does not exist."
        )

        return

    event_handler = USBFileHandler()

    observer = Observer()

    observer.schedule(
        event_handler,
        USB_DRIVE,
        recursive=True
    )

    observer.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("Stopping USB copy monitor...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()