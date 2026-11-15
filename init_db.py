
import sqlite3

DATABASE = "students.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    # Create the students table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT DEFAULT 'Local'
        )
    """)

    # Check existing columns
    columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(students)"
        ).fetchall()
    ]

    # Upgrade an existing Activity 8 database
    if "source" not in columns:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT DEFAULT 'Local'
        """)

    # Give previous records a Local source
    conn.execute("""
        UPDATE students
        SET source = 'Local'
        WHERE source IS NULL OR source = ''
    """)

    conn.commit()
    conn.close()

    print("Database initialized successfully!")
    print("Source column is ready!")


if __name__ == "__main__":
    init_db()
