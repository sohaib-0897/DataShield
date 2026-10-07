import sqlite3
from datetime import datetime
import os
import getpass

DB_PATH = "data/activity.db"


def initialize_database():
    os.makedirs("data", exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            event_type TEXT,
            file_path TEXT,
            sensitivity TEXT,
            application TEXT
        )
    """)

    connection.commit()
    connection.close()


def log_activity(
    event_type,
    file_path,
    sensitivity,
    application=""
):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO activity
        (
            timestamp,
            username,
            event_type,
            file_path,
            sensitivity,
            application
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        getpass.getuser(),
        event_type,
        file_path,
        sensitivity,
        application
    ))

    connection.commit()
    connection.close()

def initialize_transfer_table():
    os.makedirs("data", exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            event_type TEXT,
            source_path TEXT,
            destination_path TEXT,
            sensitivity TEXT,
            destination_type TEXT,
            file_hash TEXT
        )
    """)

    connection.commit()
    connection.close()


def log_transfer(
    event_type,
    source_path,
    destination_path,
    sensitivity,
    destination_type,
    file_hash=""
):
    initialize_transfer_table()

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transfers
        (
            timestamp,
            username,
            event_type,
            source_path,
            destination_path,
            sensitivity,
            destination_type,
            file_hash
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        getpass.getuser(),
        event_type,
        source_path,
        destination_path,
        sensitivity,
        destination_type,
        file_hash
    ))

    connection.commit()
    connection.close()