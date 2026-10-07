import sqlite3

connection = sqlite3.connect("data/activity.db")

rows = connection.execute("""
    SELECT
        timestamp,
        username,
        event_type,
        source_path,
        destination_path,
        sensitivity,
        destination_type,
        file_hash
    FROM transfers
    ORDER BY id DESC
    LIMIT 10
""").fetchall()

for row in rows:
    print(row)

connection.close()