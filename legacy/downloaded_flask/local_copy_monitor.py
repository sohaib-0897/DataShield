import os
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from sensitivity import calculate_hash, build_sensitive_hashes
from database import initialize_database, log_transfer


WATCH_DIRECTORY = r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent"

SENSITIVE_DIRECTORY = os.path.normcase(
    os.path.abspath(
        r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files"
    )
)

SENSITIVE_HASHES = {}


class LocalCopyHandler(FileSystemEventHandler):

    def check_file(self, file_path):

        if not os.path.isfile(file_path):
            return

        file_path = os.path.abspath(file_path)
        normalized_path = os.path.normcase(file_path)

        # Ignore the original sensitive files
        if normalized_path.startswith(
            SENSITIVE_DIRECTORY + os.sep
        ):
            return

        file_hash = calculate_hash(file_path)

        if not file_hash:
            return

        match = SENSITIVE_HASHES.get(file_hash)

        if match:

            source_path = match["source_path"]
            sensitivity = match["sensitivity"]

            print()
            print("===================================")
            print("[SENSITIVE LOCAL COPY]")
            print("===================================")
            print(f"Source:      {source_path}")
            print(f"Destination: {file_path}")
            print(f"Sensitivity: {sensitivity}")
            print(f"SHA-256:     {file_hash}")
            print("===================================")

            log_transfer(
                event_type="SENSITIVE_LOCAL_COPY",
                source_path=source_path,
                destination_path=file_path,
                sensitivity=sensitivity,
                destination_type="LOCAL",
                file_hash=file_hash
            )

        else:

            print()
            print("[LOCAL FILE] Not classified as sensitive")


    def on_created(self, event):

        if event.is_directory:
            return

        time.sleep(1)

        self.check_file(
            event.src_path
        )


    def on_moved(self, event):

        if event.is_directory:
            return

        time.sleep(1)

        self.check_file(
            event.dest_path
        )


def main():

    global SENSITIVE_HASHES

    initialize_database()

    print("===================================")
    print("     AI-DLP LOCAL COPY MONITOR")
    print("===================================")

    print("Building sensitive file fingerprints...")

    SENSITIVE_HASHES = build_sensitive_hashes()

    print(
        f"Sensitive file fingerprints loaded: "
        f"{len(SENSITIVE_HASHES)}"
    )

    print()
    print(f"Monitoring: {WATCH_DIRECTORY}")
    print("Press CTRL+C to stop.")
    print()

    observer = Observer()

    observer.schedule(
        LocalCopyHandler(),
        WATCH_DIRECTORY,
        recursive=True
    )

    observer.start()

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print()
        print("Stopping local copy monitor...")
        observer.stop()

    observer.join()


if __name__ == "__main__":
    main()