import pandas as pd

INPUT_FILE = "data/features.csv"
OUTPUT_FILE = "data/training_features.csv"


def prepare_training_data():

    print()
    print("===================================")
    print("     AI-DLP TRAINING PREPARATION")
    print("===================================")

    df = pd.read_csv(INPUT_FILE)

    print(f"Total behavior windows: {len(df)}")

    # --------------------------------
    # Remove completely empty windows
    # --------------------------------

    feature_columns = [
        "total_activity_events",
        "total_transfer_events",
        "sensitive_files_accessed",
        "unique_sensitive_files",
        "repeated_accesses",
        "critical_files_accessed",
        "files_modified",
        "files_deleted",
        "usb_insertions",
        "usb_removals",
        "local_copies",
        "usb_copies",
        "cloud_uploads",
        "sensitive_uploads",
        "after_hours_events",
        "applications_used"
    ]

    training_df = df[
        df[feature_columns].sum(axis=1) > 0
    ].copy()

    print(
        f"Non-empty behavior windows: "
        f"{len(training_df)}"
    )

    # --------------------------------
    # Save training dataset
    # --------------------------------

    training_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print()
    print(
        f"Training dataset saved to:"
        f" {OUTPUT_FILE}"
    )

    print()
    print("Training samples:")
    print(training_df.to_string(index=False))

    print("===================================")


if __name__ == "__main__":
    prepare_training_data()