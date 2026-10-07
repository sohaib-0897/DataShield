import sqlite3
from collections import Counter
from datetime import datetime


DB_PATH = "data/activity.db"


def collect_baseline(username=None):

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    if username:
        rows = connection.execute("""
            SELECT *
            FROM activity
            WHERE username = ?
            ORDER BY timestamp
        """, (username,)).fetchall()
    else:
        rows = connection.execute("""
            SELECT *
            FROM activity
            ORDER BY timestamp
        """).fetchall()

    connection.close()

    if not rows:
        print("No activity data available.")
        return

    # --------------------------------
    # Basic activity
    # --------------------------------

    total_events = len(rows)

    sensitive_events = [
        row for row in rows
        if row["sensitivity"] in ("HIGH", "CRITICAL")
    ]

    sensitive_count = len(sensitive_events)

    # --------------------------------
    # Unique sensitive files
    # --------------------------------

    unique_sensitive_files = len(
        set(row["file_path"] for row in sensitive_events)
    )

    # --------------------------------
    # Access frequency
    # --------------------------------

    file_counts = Counter(
        row["file_path"]
        for row in sensitive_events
    )

    average_accesses = (
        sensitive_count / unique_sensitive_files
        if unique_sensitive_files
        else 0
    )

    # --------------------------------
    # Applications
    # --------------------------------

    applications = Counter(
        row["application"]
        for row in rows
        if row["application"]
    )

    # --------------------------------
    # Hours
    # --------------------------------

    hours = []

    for row in rows:

        try:
            timestamp = datetime.fromisoformat(
                row["timestamp"]
            )

            hours.append(timestamp.hour)

        except ValueError:
            continue

    # --------------------------------
    # Display baseline
    # --------------------------------

    print()
    print("===================================")
    print("       USER BEHAVIOR BASELINE")
    print("===================================")

    print(
        f"Total activity events:       "
        f"{total_events}"
    )

    print(
        f"Sensitive file accesses:     "
        f"{sensitive_count}"
    )

    print(
        f"Unique sensitive files:      "
        f"{unique_sensitive_files}"
    )

    print(
        f"Average accesses/file:       "
        f"{average_accesses:.2f}"
    )

    print()

    print("Applications:")
    for app, count in applications.items():
        print(f"  {app}: {count}")

    print()

    if hours:
        print(
            f"Typical activity hour range: "
            f"{min(hours)}:00 - {max(hours)}:00"
        )

    print()

    print("Sensitive file frequency:")

    for file_path, count in file_counts.items():
        print(f"  {count}x  {file_path}")

    print("===================================")


if __name__ == "__main__":
    collect_baseline()