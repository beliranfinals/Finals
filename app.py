
import os
import sqlite3
import requests

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# =====================================================
# FLASK CONFIGURATION
# =====================================================

app = Flask(__name__)
CORS(app)

DATABASE = "students.db"

PARTNER_API_URL = os.environ.get(
    "PARTNER_API_URL",
    "https://jasminerose-2.onrender.com/api/students"
)


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# =====================================================
# INITIALIZE DATABASE
# =====================================================

def initialize_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            program TEXT NOT NULL,
            year INTEGER NOT NULL,
            section TEXT NOT NULL,
            source TEXT DEFAULT 'Local'
        )
    """)

    columns = [
        column["name"]
        for column in conn.execute(
            "PRAGMA table_info(students)"
        ).fetchall()
    ]

    if "source" not in columns:
        conn.execute("""
            ALTER TABLE students
            ADD COLUMN source TEXT DEFAULT 'Local'
        """)

    conn.commit()
    conn.close()


initialize_database()


# =====================================================
# VALIDATE STUDENT INFORMATION
# =====================================================

def validate_student(data):
    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:
        value = data.get(field)

        if value is None or str(value).strip() == "":
            return False, f"Please provide {field.replace('_', ' ')}."

    try:
        year = int(data["year"])
    except (ValueError, TypeError):
        return False, "Year must be a number."

    if year not in [1, 2, 3, 4]:
        return False, "Year must be from 1 to 4."

    return True, ""


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def index():
    return render_template("index.html")


# =====================================================
# VIEW ALL MY RECORDS
# =====================================================

@app.route("/api/students", methods=["GET"])
def get_students():
    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    records = [dict(student) for student in students]

    return jsonify({
        "success": True,
        "count": len(records),
        "students": records
    }), 200


# =====================================================
# ADD STUDENT TO MY RECORDS
# =====================================================

@app.route("/add-student", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    valid, message = validate_student(data)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            int(data["year"]),
            data["section"].strip().upper(),
            "Local"
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student successfully added to My Records!"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Student ID already exists in My Records."
        }), 409

    finally:
        conn.close()


# =====================================================
# SEARCH / RETRIEVE STUDENT
# =====================================================

@app.route("/search-students", methods=["GET"])
def search_students():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({
            "success": False,
            "message": "Enter a student ID or name."
        }), 400

    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        WHERE student_id LIKE ? OR name LIKE ?
        ORDER BY id DESC
    """, (f"%{query}%", f"%{query}%")).fetchall()

    conn.close()

    records = [dict(student) for student in students]

    return jsonify({
        "success": True,
        "count": len(records),
        "students": records
    }), 200


# =====================================================
# RECEIVE STUDENT RECORD FROM ANOTHER SYSTEM
# =====================================================

@app.route("/api/students", methods=["POST"])
def receive_student():
    data = request.get_json(silent=True) or {}

    valid, message = validate_student(data)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            int(data["year"]),
            data["section"].strip().upper(),
            "Partner API"
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Student record received and saved successfully."
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "Student ID already exists."
        }), 409

    finally:
        conn.close()


# =====================================================
# RETRIEVE CLASSMATE'S RECORDS
# =====================================================

@app.route("/partner-records", methods=["GET"])
def get_partner_records():
    try:
        response = requests.get(
            PARTNER_API_URL,
            timeout=60
        )

        if response.status_code != 200:
            return jsonify({
                "success": False,
                "message": "Unable to retrieve classmate's records.",
                "partner_status": response.status_code
            }), 502

        data = response.json()

        if isinstance(data, list):
            students = data
        elif isinstance(data, dict):
            students = data.get(
                "students",
                data.get("records", [])
            )
        else:
            students = []

        if not isinstance(students, list):
            students = []

        return jsonify({
            "success": True,
            "count": len(students),
            "students": students
        }), 200

    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Classmate's API request timed out. Try again."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 502

    except ValueError:
        return jsonify({
            "success": False,
            "message": "Classmate's API returned invalid JSON."
        }), 502


# =====================================================
# SAVE CLASSMATE'S RECORD TO MY DATABASE
# =====================================================

@app.route("/import-student", methods=["POST"])
def import_student():
    data = request.get_json(silent=True) or {}

    valid, message = validate_student(data)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    conn = get_db_connection()

    try:
        conn.execute("""
            INSERT INTO students
            (student_id, name, program, year, section, source)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            int(data["year"]),
            data["section"].strip().upper(),
            "Classmate API"
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Classmate's record successfully saved to My Records!"
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "success": False,
            "message": "This Student ID already exists in your database."
        }), 409

    finally:
        conn.close()


# =====================================================
# SEND MY STUDENT RECORD TO CLASSMATE'S API
# =====================================================

@app.route("/send-to-partner", methods=["POST"])
def send_to_partner():
    data = request.get_json(silent=True) or {}

    valid, message = validate_student(data)

    if not valid:
        return jsonify({
            "success": False,
            "message": message
        }), 400

    student_data = {
        "student_id": data["student_id"].strip(),
        "name": data["name"].strip(),
        "program": data["program"].strip(),
        "year": int(data["year"]),
        "section": data["section"].strip().upper()
    }

    try:
        response = requests.post(
            PARTNER_API_URL,
            json=student_data,
            timeout=60
        )

        try:
            partner_result = response.json()
        except ValueError:
            partner_result = {"message": response.text}

        if response.status_code in [200, 201]:
            return jsonify({
                "success": True,
                "message": "Student record successfully sent to classmate's API!",
                "partner_response": partner_result
            }), 200

        return jsonify({
            "success": False,
            "message": "Classmate's API did not accept the record.",
            "partner_status": response.status_code,
            "partner_response": partner_result
        }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "message": "Sending request timed out. Please try again."
        }), 504

    except requests.exceptions.RequestException as error:
        return jsonify({
            "success": False,
            "message": str(error)
        }), 502


# =====================================================
# VIEW ONE STUDENT USING DATABASE ID
# =====================================================

@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    conn = get_db_connection()

    student = conn.execute("""
        SELECT * FROM students WHERE id = ?
    """, (student_id,)).fetchone()

    conn.close()

    if student is None:
        return jsonify({
            "success": False,
            "message": "Student record not found."
        }), 404

    return jsonify({
        "success": True,
        "student": dict(student)
    }), 200


# =====================================================
# VIEW STUDENTS BY SECTION
# =====================================================

@app.route("/students/section/<section>", methods=["GET"])
def get_students_by_section(section):
    conn = get_db_connection()

    students = conn.execute("""
        SELECT * FROM students
        WHERE UPPER(section) = ?
        ORDER BY id DESC
    """, (section.upper(),)).fetchall()

    conn.close()

    records = [dict(student) for student in students]

    return jsonify({
        "success": True,
        "count": len(records),
        "students": records
    }), 200


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "Student Data Exchange API is running."
    }), 200


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
