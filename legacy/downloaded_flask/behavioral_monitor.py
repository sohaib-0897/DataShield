import time
import sqlite3
import getpass
import ctypes
from datetime import datetime

import psutil
import win32gui
import win32process


DB_PATH = "data/activity.db"

# Take one behavioral sample every 5 seconds
SAMPLE_INTERVAL = 5

# Consider the user idle after 60 seconds without keyboard/mouse input
IDLE_THRESHOLD_SECONDS = 60


def initialize_behavior_table():

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behavior_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            event_type TEXT,
            application TEXT,
            window_title TEXT,
            idle_seconds INTEGER
        )
    """)

    connection.commit()
    connection.close()


def get_foreground_application():

    try:

        hwnd = win32gui.GetForegroundWindow()

        if not hwnd:
            return "", ""

        _, process_id = win32process.GetWindowThreadProcessId(hwnd)

        process = psutil.Process(process_id)

        application = process.name()
        window_title = win32gui.GetWindowText(hwnd)

        return application, window_title

    except (
        psutil.NoSuchProcess,
        psutil.AccessDenied,
        psutil.ZombieProcess
    ):

        return "", ""


def get_idle_seconds():

    class LASTINPUTINFO(ctypes.Structure):

        _fields_ = [
            ("cbSize", ctypes.c_uint),
            ("dwTime", ctypes.c_uint)
        ]

    last_input = LASTINPUTINFO()

    last_input.cbSize = ctypes.sizeof(LASTINPUTINFO)

    success = ctypes.windll.user32.GetLastInputInfo(
        ctypes.byref(last_input)
    )

    if not success:

        return 0

    # Windows GetTickCount() returns a 32-bit millisecond counter.
    # dwTime from GetLastInputInfo() uses the same counter.
    tick_count = ctypes.windll.kernel32.GetTickCount()

    # Handle the 32-bit counter wrapping around.
    idle_milliseconds = (
        tick_count - last_input.dwTime
    ) & 0xFFFFFFFF

    idle_seconds = int(
        idle_milliseconds / 1000
    )

    return idle_seconds


def log_behavior(
    event_type,
    application,
    window_title,
    idle_seconds
):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO behavior_events
        (
            timestamp,
            username,
            event_type,
            application,
            window_title,
            idle_seconds
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        getpass.getuser(),
        event_type,
        application,
        window_title,
        idle_seconds
    ))

    connection.commit()
    connection.close()


def main():

    initialize_behavior_table()

    print("===================================")
    print("   AI-DLP BEHAVIOR MONITOR")
    print("===================================")
    print()
    print("Monitoring normal user behavior...")
    print(f"Sampling every {SAMPLE_INTERVAL} seconds.")
    print("Press CTRL+C to stop.")
    print()

    try:

        while True:

            # Detect currently active application
            application, window_title = (
                get_foreground_application()
            )

            # Detect keyboard/mouse inactivity
            idle_seconds = get_idle_seconds()

            # Classify current behavior
            if idle_seconds >= IDLE_THRESHOLD_SECONDS:

                event_type = "USER_IDLE"

            else:

                event_type = "APPLICATION_ACTIVE"

            # Display current behavioral observation
            print(
                f"[BEHAVIOR] "
                f"{event_type} | "
                f"Application: {application} | "
                f"Idle: {idle_seconds}s"
            )

            # Store behavioral observation
            log_behavior(
                event_type,
                application,
                window_title,
                idle_seconds
            )

            # Wait before next observation
            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:

        print()
        print("Stopping behavior monitor...")


if __name__ == "__main__":

    main()