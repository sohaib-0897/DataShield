import sqlite3
from collections import Counter
from datetime import datetime, timedelta

DB_PATH = "data/activity.db"

# How much recent activity should be used for current behavior?
DEFAULT_WINDOW_MINUTES = 60

WORK_START = 9
WORK_END = 17


def get_behavior(username=None, window_minutes=DEFAULT_WINDOW_MINUTES):

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    cutoff_time = datetime.now() - timedelta(
        minutes=window_minutes
    )

    cutoff_string = cutoff_time.isoformat()

    # -----------------------------
    # Activity events
    # -----------------------------

    if username:

        activity_rows = connection.execute("""
            SELECT *
            FROM activity
            WHERE username = ?
            AND timestamp >= ?
            ORDER BY timestamp
        """, (
            username,
            cutoff_string
        )).fetchall()

        transfer_rows = connection.execute("""
            SELECT *
            FROM transfers
            WHERE username = ?
            AND timestamp >= ?
            ORDER BY timestamp
        """, (
            username,
            cutoff_string
        )).fetchall()

    else:

        activity_rows = connection.execute("""
            SELECT *
            FROM activity
            WHERE timestamp >= ?
            ORDER BY timestamp
        """, (cutoff_string,)).fetchall()

        transfer_rows = connection.execute("""
            SELECT *
            FROM transfers
            WHERE timestamp >= ?
            ORDER BY timestamp
        """, (cutoff_string,)).fetchall()

    connection.close()

    # -----------------------------
    # Sensitive activity
    # -----------------------------

    sensitive_rows = [
        row for row in activity_rows
        if row["sensitivity"] in ("HIGH", "CRITICAL")
    ]

    sensitive_files_accessed = len(
        sensitive_rows
    )

    unique_sensitive_files = len(
        set(
            row["file_path"]
            for row in sensitive_rows
        )
    )

    # -----------------------------
    # Repeated accesses
    # -----------------------------

    file_counts = Counter(
        row["file_path"]
        for row in sensitive_rows
    )

    repeated_accesses = sum(
        count - 1
        for count in file_counts.values()
        if count > 1
    )

    # -----------------------------
    # Critical files
    # -----------------------------

    critical_files_accessed = sum(
        1
        for row in activity_rows
        if row["sensitivity"] == "CRITICAL"
    )

    # -----------------------------
    # File modifications
    # -----------------------------

    files_modified = sum(
        1
        for row in activity_rows
        if row["event_type"] == "FILE_WRITE"
    )

    # -----------------------------
    # File deletions
    # -----------------------------

    files_deleted = sum(
        1
        for row in activity_rows
        if row["event_type"] == "FILE_DELETE"
    )

    # -----------------------------
    # USB events
    # -----------------------------

    usb_insertions = sum(
        1
        for row in activity_rows
        if row["event_type"] == "USB_INSERTED"
    )

    usb_removals = sum(
        1
        for row in activity_rows
        if row["event_type"] == "USB_REMOVED"
    )

    # -----------------------------
    # Transfer events
    # -----------------------------

    local_copies = sum(
        1
        for row in transfer_rows
        if row["event_type"] == "SENSITIVE_LOCAL_COPY"
    )

    usb_copies = sum(
        1
        for row in transfer_rows
        if row["event_type"] == "SENSITIVE_USB_COPY"
    )

    cloud_uploads = sum(
        1
        for row in transfer_rows
        if row["event_type"] == "SENSITIVE_CLOUD_COPY"
    )

    sensitive_uploads = sum(
        1
        for row in transfer_rows
        if row["event_type"] == "SENSITIVE_UPLOAD"
    )

    # -----------------------------
    # After-hours activity
    # -----------------------------

    after_hours_events = 0

    for row in sensitive_rows:

        try:

            timestamp = datetime.fromisoformat(
                row["timestamp"]
            )

            hour = timestamp.hour

            if (
                hour < WORK_START
                or hour >= WORK_END
            ):
                after_hours_events += 1

        except ValueError:
            continue

    # -----------------------------
    # Applications used
    # -----------------------------

    applications_used = len(
        set(
            row["application"]
            for row in activity_rows
            if row["application"]
        )
    )

    # -----------------------------
    # Total events
    # -----------------------------

    total_activity_events = len(
        activity_rows
    )

    total_transfer_events = len(
        transfer_rows
    )

    # -----------------------------
    # Return behavior features
    # -----------------------------

    return {

        "window_minutes":
            window_minutes,

        "total_activity_events":
            total_activity_events,

        "total_transfer_events":
            total_transfer_events,

        "sensitive_files_accessed":
            sensitive_files_accessed,

        "unique_sensitive_files":
            unique_sensitive_files,

        "repeated_accesses":
            repeated_accesses,

        "critical_files_accessed":
            critical_files_accessed,

        "files_modified":
            files_modified,

        "files_deleted":
            files_deleted,

        "usb_insertions":
            usb_insertions,

        "usb_removals":
            usb_removals,

        "local_copies":
            local_copies,

        "usb_copies":
            usb_copies,

        "cloud_uploads":
            cloud_uploads,

        "sensitive_uploads":
            sensitive_uploads,

        "after_hours_events":
            after_hours_events,

        "applications_used":
            applications_used
    }


def print_behavior(username=None):

    behavior = get_behavior(username)

    print()
    print("===================================")
    print("      RECENT USER BEHAVIOR")
    print("===================================")

    print(
        f"Analysis window: "
        f"Last {behavior['window_minutes']} minutes"
    )

    print()

    for key, value in behavior.items():

        if key == "window_minutes":
            continue

        print(
            f"{key.replace('_', ' ').title():30} {value}"
        )

    print("===================================")


if __name__ == "__main__":

    print_behavior()