import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "data/activity.db"

WINDOW_MINUTES = 60


def load_events():

    connection = sqlite3.connect(DB_PATH)

    activity = pd.read_sql_query(
        "SELECT * FROM activity",
        connection
    )

    transfers = pd.read_sql_query(
        "SELECT * FROM transfers",
        connection
    )

    connection.close()

    if not activity.empty:
        activity["timestamp"] = pd.to_datetime(
            activity["timestamp"]
        )

    if not transfers.empty:
        transfers["timestamp"] = pd.to_datetime(
            transfers["timestamp"]
        )

    return activity, transfers


def build_features():

    activity, transfers = load_events()

    if activity.empty and transfers.empty:
        print("No telemetry data available.")
        return pd.DataFrame()

    # --------------------------------
    # Determine overall time range
    # --------------------------------

    timestamps = []

    if not activity.empty:
        timestamps.extend(
            activity["timestamp"].tolist()
        )

    if not transfers.empty:
        timestamps.extend(
            transfers["timestamp"].tolist()
        )

    start_time = min(timestamps)
    end_time = max(timestamps)

    # Align start time to hour
    start_time = start_time.replace(
        minute=0,
        second=0,
        microsecond=0
    )

    rows = []

    current_time = start_time

    # --------------------------------
    # Build hourly windows
    # --------------------------------

    while current_time <= end_time:

        window_end = (
            current_time
            + timedelta(minutes=WINDOW_MINUTES)
        )

        # Activity inside this window
        activity_window = activity[
            (activity["timestamp"] >= current_time)
            &
            (activity["timestamp"] < window_end)
        ]

        # Transfers inside this window
        transfer_window = transfers[
            (transfers["timestamp"] >= current_time)
            &
            (transfers["timestamp"] < window_end)
        ]

        # --------------------------------
        # Sensitive activity
        # --------------------------------

        sensitive = activity_window[
            activity_window["sensitivity"].isin(
                ["HIGH", "CRITICAL"]
            )
        ]

        sensitive_accesses = len(sensitive)

        unique_sensitive_files = (
            sensitive["file_path"].nunique()
            if not sensitive.empty
            else 0
        )

        # --------------------------------
        # Repeated accesses
        # --------------------------------

        if not sensitive.empty:

            file_counts = (
                sensitive["file_path"]
                .value_counts()
            )

            repeated_accesses = sum(
                count - 1
                for count in file_counts
                if count > 1
            )

        else:

            repeated_accesses = 0

        # --------------------------------
        # Critical files
        # --------------------------------

        critical_accesses = len(
            activity_window[
                activity_window["sensitivity"]
                == "CRITICAL"
            ]
        )

        # --------------------------------
        # File modifications
        # --------------------------------

        files_modified = len(
            activity_window[
                activity_window["event_type"]
                == "FILE_WRITE"
            ]
        )

        # --------------------------------
        # File deletions
        # --------------------------------

        files_deleted = len(
            activity_window[
                activity_window["event_type"]
                == "FILE_DELETE"
            ]
        )

        # --------------------------------
        # USB activity
        # --------------------------------

        usb_insertions = len(
            activity_window[
                activity_window["event_type"]
                == "USB_INSERTED"
            ]
        )

        usb_removals = len(
            activity_window[
                activity_window["event_type"]
                == "USB_REMOVED"
            ]
        )

        # --------------------------------
        # Transfers
        # --------------------------------

        local_copies = len(
            transfer_window[
                transfer_window["event_type"]
                == "SENSITIVE_LOCAL_COPY"
            ]
        )

        usb_copies = len(
            transfer_window[
                transfer_window["event_type"]
                == "SENSITIVE_USB_COPY"
            ]
        )

        cloud_uploads = len(
            transfer_window[
                transfer_window["event_type"]
                == "SENSITIVE_CLOUD_COPY"
            ]
        )

        sensitive_uploads = len(
            transfer_window[
                transfer_window["event_type"]
                == "SENSITIVE_UPLOAD"
            ]
        )

        # --------------------------------
        # After-hours activity
        # --------------------------------

        after_hours = 0

        for timestamp in sensitive["timestamp"]:

            if (
                timestamp.hour < 9
                or timestamp.hour >= 17
            ):
                after_hours += 1

        # --------------------------------
        # Applications
        # --------------------------------

        applications_used = (
            activity_window["application"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

        # --------------------------------
        # Total activity
        # --------------------------------

        total_activity = len(
            activity_window
        )

        total_transfers = len(
            transfer_window
        )

        # --------------------------------
        # Create feature row
        # --------------------------------

        rows.append({

            "window_start":
                current_time,

            "window_end":
                window_end,

            "total_activity_events":
                total_activity,

            "total_transfer_events":
                total_transfers,

            "sensitive_files_accessed":
                sensitive_accesses,

            "unique_sensitive_files":
                unique_sensitive_files,

            "repeated_accesses":
                repeated_accesses,

            "critical_files_accessed":
                critical_accesses,

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
                after_hours,

            "applications_used":
                applications_used
        })

        current_time = window_end

    return pd.DataFrame(rows)


def main():

    print()
    print("===================================")
    print("       AI-DLP FEATURE BUILDER")
    print("===================================")

    features = build_features()

    if features.empty:
        return

    print()
    print(
        f"Generated {len(features)} behavior windows."
    )

    print()
    print(features.to_string(index=False))

    output_file = "data/features.csv"

    features.to_csv(
        output_file,
        index=False
    )

    print()
    print(
        f"Feature dataset saved to: {output_file}"
    )

    print("===================================")


if __name__ == "__main__":
    main()