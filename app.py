
import os
import requests

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from crud import (
    initialize_database,
    get_all_students,
    get_student,
    add_student,
    update_student,
    delete_student,
    get_partner_records,
    save_partner_record
)

# =====================================================
# FLASK CONFIGURATION
# =====================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-secret-key-change-this"
)

# PARTNER API URL
PARTNER_API_URL = os.environ.get(
    "PARTNER_API_URL",
    "https://myranie-arch.onrender.com/api/students"
).strip().rstrip("/")

# Initialize database
initialize_database()


# =====================================================
# FETCH PARTNER STUDENT RECORDS
# =====================================================

def fetch_partner_students():

    if not PARTNER_API_URL:
        return [], "Partner API URL is not configured."

    try:
        response = requests.get(
            PARTNER_API_URL,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            students = data

        elif isinstance(data, dict):
            students = data.get(
                "students",
                data.get("data", [])
            )

        else:
            return [], "Unsupported partner API response."

        if not isinstance(students, list):
            return [], "Partner API did not return a student list."

        return students, None

    except requests.exceptions.Timeout:
        return [], "Partner API request timed out."

    except requests.exceptions.ConnectionError:
        return [], "Cannot connect to partner API."

    except requests.exceptions.HTTPError as error:
        return [], f"Partner API HTTP error: {error}"

    except requests.exceptions.RequestException as error:
        return [], f"Partner API connection error: {error}"

    except ValueError:
        return [], "Partner API did not return valid JSON."


# =====================================================
# VALIDATE STUDENT FORM
# =====================================================

def validate_student_form(form):

    student_id = form.get("student_id", "").strip()
    name = form.get("name", "").strip()
    program = form.get("program", "").strip().upper()
    section = form.get("section", "").strip().upper()

    try:
        year = int(form.get("year", ""))

    except (TypeError, ValueError):
        return None, "Please enter a valid year level."

    if not all([student_id, name, program, section]):
        return None, "Please complete all fields."

    if year < 1 or year > 6:
        return None, "Year level must be between 1 and 6."

    return {
        "student_id": student_id,
        "name": name,
        "program": program,
        "year": year,
        "section": section
    }, None


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def index():

    students = get_all_students()

    partner_students, partner_error = fetch_partner_students()

    return render_template(
        "index.html",
        students=students,
        partner_students=partner_students,
        partner_error=partner_error,
        saved_partner_records=get_partner_records(),
        partner_api_url=PARTNER_API_URL
    )


# =====================================================
# ADD STUDENT
# =====================================================

@app.route("/students/add", methods=["POST"])
def add_student_route():

    student, error = validate_student_form(request.form)

    if error:
        flash(error, "error")
        return redirect(url_for("index"))

    success, message = add_student(
        student["student_id"],
        student["name"],
        student["program"],
        student["year"],
        student["section"]
    )

    flash(message, "success" if success else "error")

    return redirect(url_for("index"))


# =====================================================
# UPDATE STUDENT
# =====================================================

@app.route("/students/update/<int:record_id>", methods=["POST"])
def update_student_route(record_id):

    student, error = validate_student_form(request.form)

    if error:
        flash(error, "error")
        return redirect(url_for("index"))

    success, message = update_student(
        record_id,
        student["student_id"],
        student["name"],
        student["program"],
        student["year"],
        student["section"]
    )

    flash(message, "success" if success else "error")

    return redirect(url_for("index"))


# =====================================================
# DELETE STUDENT
# =====================================================

@app.route("/students/delete/<int:record_id>", methods=["POST"])
def delete_student_route(record_id):

    deleted = delete_student(record_id)

    if deleted:
        flash("Student deleted successfully.", "success")
    else:
        flash("Student record not found.", "error")

    return redirect(url_for("index"))


# =====================================================
# VIEW ALL OWN STUDENTS
# =====================================================

@app.route("/students")
def students_json():

    students = get_all_students()

    return jsonify([
        dict(student) for student in students
    ])


# =====================================================
# VIEW ONE STUDENT
# =====================================================

@app.route("/students/<int:record_id>")
def one_student_json(record_id):

    student = get_student(record_id)

    if student is None:
        return jsonify({
            "error": "Student not found"
        }), 404

    return jsonify(dict(student))


# =====================================================
# OWN STUDENT API
# =====================================================

@app.route("/api/students")
def api_students():

    students = get_all_students()

    return jsonify({
        "success": True,
        "count": len(students),
        "students": [
            dict(student) for student in students
        ]
    })


# =====================================================
# PARTNER STUDENT API
# =====================================================

@app.route("/api/partner/students")
def partner_students_json():

    students, error = fetch_partner_students()

    if error:
        return jsonify({
            "success": False,
            "error": error,
            "students": []
        }), 502

    return jsonify({
        "success": True,
        "count": len(students),
        "students": students
    })


# =====================================================
# SAVE PARTNER STUDENT
# =====================================================

@app.route("/partner/save", methods=["POST"])
def save_partner():

    selected_id = request.form.get(
        "student_id", ""
    ).strip()

    if not selected_id:
        flash("Missing partner student ID.", "error")
        return redirect(url_for("index"))

    students, error = fetch_partner_students()

    if error:
        flash(error, "error")
        return redirect(url_for("index"))

    selected = next(
        (
            student for student in students
            if str(
                student.get("student_id")
                or student.get("id")
                or ""
            ) == selected_id
        ),
        None
    )

    if selected is None:
        flash("Partner student record not found.", "error")
        return redirect(url_for("index"))

    success, message = save_partner_record(
        PARTNER_API_URL,
        selected
    )

    flash(
        message,
        "success" if success else "error"
    )

    return redirect(url_for("index"))


# =====================================================
# SAVED PARTNER RECORDS
# =====================================================

@app.route("/partner-records")
def partner_records_json():

    return jsonify([
        dict(record) for record in get_partner_records()
    ])


# =====================================================
# ABOUT
# =====================================================

@app.route("/about")
def about():

    return jsonify({
        "application": "Student Information System",
        "developer": "Arnie Beliran",
        "framework": "Python Flask",
        "database": "SQLite",
        "deployment": "Render / AWS Lightsail",
        "partner_api": PARTNER_API_URL
    })


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy",
        "application": "Student Information System"
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
