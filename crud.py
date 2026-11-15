
import sqlite3

DATABASE = "students.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------
# CHECK DUPLICATE STUDENT ID
# ------------------------------------

def student_id_exists(student_id):
    conn = get_db_connection()

    student = conn.execute("""
        SELECT id FROM students
        WHERE student_id = ?
    """, (student_id,)).fetchone()

    conn.close()

    return student is not None


# ------------------------------------
# CREATE STUDENT
# ------------------------------------

def create_student(student):

    conn = get_db_connection()

    cursor = conn.execute("""
        INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        student["student_id"],
        student["name"],
        student["program"],
        student["year"],
        student["section"],
        student.get("source", "Local")
    ))

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return new_id


# ------------------------------------
# READ ALL STUDENTS
# ------------------------------------

def get_all_students():

    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(student) for student in students]


# ------------------------------------
# READ ONE STUDENT
# ------------------------------------

def get_student(student_id):

    conn = get_db_connection()

    student = conn.execute("""
        SELECT * FROM students
        WHERE id = ?
    """, (student_id,)).fetchone()

    conn.close()

    return dict(student) if student else None


# ------------------------------------
# UPDATE STUDENT
# ------------------------------------

def update_student(student_id, student):

    conn = get_db_connection()

    cursor = conn.execute("""
        UPDATE students
        SET student_id = ?,
            name = ?,
            program = ?,
            year = ?,
            section = ?
        WHERE id = ?
    """, (
        student["student_id"],
        student["name"],
        student["program"],
        student["year"],
        student["section"],
        student_id
    ))

    conn.commit()

    updated = cursor.rowcount > 0

    conn.close()

    return updated


# ------------------------------------
# DELETE STUDENT
# ------------------------------------

def delete_student(student_id):

    conn = get_db_connection()

    cursor = conn.execute("""
        DELETE FROM students
        WHERE id = ?
    """, (student_id,))

    conn.commit()

    deleted = cursor.rowcount > 0

    conn.close()

    return deleted


# ------------------------------------
# IMPORT PARTNER STUDENT
# ------------------------------------

def import_student(student):

    student["source"] = "Classmate API"

    return create_student(student)
