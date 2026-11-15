
from crud import get_db_connection, initialize_database


def initialize():
    initialize_database()

    connection = get_db_connection()

    count = connection.execute(
        "SELECT COUNT(*) FROM students"
    ).fetchone()[0]

    if count == 0:
        students = [
            ("2026-00123", "Arnie Beliran", "BSIT", 3, "A"),
            ("2026-00124", "Maria Santos", "BSIT", 1, "A"),
            ("2026-00125", "Pedro Reyes", "BSIT", 2, "B"),
            ("2026-00126", "Ana Cruz", "BSCS", 2, "B"),
            ("2026-00127", "John Garcia", "BSIT", 4, "C")
        ]

        connection.executemany("""
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, students)

        connection.commit()
        print("Sample records inserted successfully.")

    else:
        print("Existing student records preserved.")

    connection.close()
    print("Database initialized successfully.")


if __name__ == "__main__":
    initialize()
