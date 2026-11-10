
import os
import sqlite3
import requests

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

app = Flask(__name__)

# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

DATABASE = "students.db"

# Change this URL if your classmate uses another API.
CLASSMATE_API_URL = os.environ.get(
    "CLASSMATE_API_URL",
    "https://jasminerose-2.onrender.com/api/students"
)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


# --------------------------------------------------
# READ ALL STUDENTS - GET
# --------------------------------------------------

@app.route("/api/students", methods=["GET"])
def api_students():

    conn = get_db_connection()

    students = conn.execute(
        "SELECT * FROM students ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return jsonify([dict(student) for student in students])


# --------------------------------------------------
# CREATE STUDENT - POST
# --------------------------------------------------

@app.route("/api/students", methods=["POST"])
def add_student():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:
        if data.get(field) is None or str(data[field]).strip() == "":
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        year = int(data["year"])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Year must be a positive number"
        }), 400

    conn = get_db_connection()

    cursor = conn.execute(
        """
        INSERT INTO students
        (student_id, name, program, year, section)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            year,
            data["section"].strip().upper()
        )
    )

    conn.commit()

    new_id = cursor.lastrowid

    conn.close()

    return jsonify({
        "message": "Student added successfully",
        "id": new_id
    }), 201


# --------------------------------------------------
# READ ONE STUDENT - GET
# --------------------------------------------------

@app.route("/api/students/<int:id>", methods=["GET"])
def api_get_student(id):

    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# --------------------------------------------------
# UPDATE STUDENT - PUT
# --------------------------------------------------

@app.route("/api/students/<int:id>", methods=["PUT"])
def update_student(id):

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "error": "Invalid JSON data"
        }), 400

    required_fields = [
        "student_id",
        "name",
        "program",
        "year",
        "section"
    ]

    for field in required_fields:
        if data.get(field) is None or str(data[field]).strip() == "":
            return jsonify({
                "error": f"{field} is required"
            }), 400

    try:
        year = int(data["year"])

        if year < 1:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Year must be a positive number"
        }), 400

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    if existing is None:
        conn.close()

        return jsonify({
            "error": "Student not found"
        }), 404

    conn.execute(
        """
        UPDATE students
        SET student_id = ?,
            name = ?,
            program = ?,
            year = ?,
            section = ?
        WHERE id = ?
        """,
        (
            data["student_id"].strip(),
            data["name"].strip(),
            data["program"].strip(),
            year,
            data["section"].strip().upper(),
            id
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Student updated successfully"
    })


# --------------------------------------------------
# DELETE STUDENT - DELETE
# --------------------------------------------------

@app.route("/api/students/<int:id>", methods=["DELETE"])
def delete_student(id):

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT id FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    if existing is None:
        conn.close()

        return jsonify({
            "error": "Student not found"
        }), 404

    conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Student deleted successfully"
    })


# --------------------------------------------------
# RETRIEVE CLASSMATE'S API THROUGH FLASK
# --------------------------------------------------

@app.route("/api/classmate-students", methods=["GET"])
def classmate_students():

    try:

        response = requests.get(
            CLASSMATE_API_URL,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            return jsonify({
                "error": "Classmate API returned an invalid format"
            }), 502

        return jsonify(data)

    except requests.exceptions.RequestException as e:

        return jsonify({
            "error": "Unable to connect to classmate API",
            "details": str(e)
        }), 502

    except ValueError:

        return jsonify({
            "error": "Classmate API returned invalid JSON"
        }), 502


# --------------------------------------------------
# APPLICATION START
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
