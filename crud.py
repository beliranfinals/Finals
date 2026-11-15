
import os
import sqlite3

DATABASE = os.environ.get(
    "DATABASE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "students.db")
)


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE IF NOT EXISTS partner_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_api_url TEXT NOT NULL,
            partner_student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(partner_api_url, partner_student_id)
        )
    """)

    connection.commit()
    connection.close()


def get_all_students():
    connection = get_db_connection()

    students = connection.execute("""
        SELECT * FROM students ORDER BY id DESC
    """).fetchall()

    connection.close()
    return students


def get_student(record_id):
    connection = get_db_connection()

    student = connection.execute("""
        SELECT * FROM students WHERE id = ?
    """, (record_id,)).fetchone()

    connection.close()
    return student


def add_student(student_id, name, program, year, section):
    connection = get_db_connection()

    try:
        connection.execute("""
            INSERT INTO students
            (student_id, name, program, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, name, program, year, section))

        connection.commit()
        return True, "Student added successfully."

    except sqlite3.IntegrityError:
        return False, "Student ID already exists."

    finally:
        connection.close()


def update_student(record_id, student_id, name, program, year, section):
    connection = get_db_connection()

    try:
        cursor = connection.execute("""
            UPDATE students
            SET student_id = ?,
                name = ?,
                program = ?,
                year = ?,
                section = ?
            WHERE id = ?
        """, (student_id, name, program, year, section, record_id))

        connection.commit()

        if cursor.rowcount == 0:
            return False, "Student record not found."

        return True, "Student updated successfully."

    except sqlite3.IntegrityError:
        return False, "Student ID already exists."

    finally:
        connection.close()


def delete_student(record_id):
    connection = get_db_connection()

    cursor = connection.execute("""
        DELETE FROM students WHERE id = ?
    """, (record_id,))

    connection.commit()
    deleted = cursor.rowcount > 0
    connection.close()

    return deleted


def get_partner_records():
    connection = get_db_connection()

    records = connection.execute("""
        SELECT * FROM partner_records ORDER BY id DESC
    """).fetchall()

    connection.close()
    return records


def save_partner_record(api_url, student):
    partner_id = str(
        student.get("student_id") or student.get("id") or ""
    ).strip()

    if not partner_id:
        return False, "Partner student ID is missing."

    try:
        year = int(student.get("year", 0))
    except (TypeError, ValueError):
        year = 0

    connection = get_db_connection()

    try:
        connection.execute("""
            INSERT INTO partner_records
            (
                partner_api_url,
                partner_student_id,
                name,
                program,
                year,
                section
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            api_url,
            partner_id,
            str(student.get("name", "")),
            str(student.get("program", "")),
            year,
            str(student.get("section", ""))
        ))

        connection.commit()
        return True, "Classmate record saved successfully."

    except sqlite3.IntegrityError:
        return False, "This classmate record is already saved."

    finally:
        connection.close()
