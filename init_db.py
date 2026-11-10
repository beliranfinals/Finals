
import sqlite3

DATABASE = "students.db"

conn = sqlite3.connect(DATABASE)

conn.execute("""
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL
)
""")

# Insert one initial practice record only if the table is empty.
count = conn.execute(
    "SELECT COUNT(*) FROM students"
).fetchone()[0]

if count == 0:

    conn.execute("""
        INSERT INTO students
        (student_id, name, program, year, section)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "2026-00123",
        "Arnie Beliran",
        "BSIT",
        3,
        "A"
    ))

    print("Initial student record created.")

conn.commit()
conn.close()

print("Database initialized successfully!")
