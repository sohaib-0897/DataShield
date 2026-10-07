import sqlite3

connection = sqlite3.connect("data/activity.db")

rows = connection.execute("""
    SELECT *
    FROM activity
    ORDER BY id DESC
    LIMIT 5
""").fetchall()

for row in rows:
    print(row)

connection.close()