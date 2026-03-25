import os
import sqlite3

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "students.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS Student (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            gender TEXT DEFAULT 'Girl',
            age INTEGER,
            class_name TEXT,
            attendance INTEGER,
            marks INTEGER,
            parental_support TEXT,
            family_income TEXT,
            risk_label TEXT,
            risk_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def calculate_girl_dropout_risk(data):
    score = 0
    factors = []

    attendance = data["attendance"]
    marks = data["marks"]

    if attendance < 60:
        score += 30
        factors.append("very low attendance")
    elif attendance < 75:
        score += 15
        factors.append("inconsistent attendance")

    if marks < 40:
        score += 25
        factors.append("low academic performance")
    elif marks < 55:
        score += 12
        factors.append("needs academic reinforcement")

    if data["parental_support"] == "low":
        score += 12
        factors.append("limited parental support")

    if data["family_income"] == "low":
        score += 10
        factors.append("economic stress in household")

    score = min(score, 100)

    if score >= 60:
        label = "High Risk"
    elif score >= 35:
        label = "Medium Risk"
    else:
        label = "Low Risk"

    return label, score, factors


def save_prediction(data, risk_label, risk_score):
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO Student(
                name, gender, age, class_name,
                attendance, marks, parental_support, family_income,
                risk_label, risk_score
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                "Girl",
                data["age"],
                data["class_name"],
                data["attendance"],
                data["marks"],
                data["parental_support"],
                data["family_income"],
    
                risk_label,
                risk_score,
            ),
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


@app.route("/")
def home():
    return render_template("index.html", current_page="predict")


@app.route("/predict", methods=["POST"])
def predict():
    form_data = {
        "name": request.form.get("name", "").strip(),
        "age": int(request.form.get("age", 0)),
        "class_name": request.form.get("class_name", "").strip(),
        "attendance": int(request.form.get("attendance", 0)),
        "marks": int(request.form.get("marks", 0)),
        "parental_support": request.form.get("parental_support", "medium"),
        "family_income": request.form.get("family_income", "medium"),
    }

    risk_label, risk_score, factors = calculate_girl_dropout_risk(form_data)
    db_saved = save_prediction(form_data, risk_label, risk_score)

    return render_template(
        "result.html",
        name=form_data["name"],
        risk=risk_label,
        score=risk_score,
        factors=factors,
        db_saved=db_saved,
        current_page="predict",
    )


@app.route("/students")
def students():
    conn = get_db_connection()
    records = conn.execute(
        """
        SELECT id, name, age, class_name, attendance, marks,
               parental_support, family_income, risk_label, risk_score, created_at
        FROM Student
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("students.html", students=records, current_page="students")


@app.route("/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM Student WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("students"))


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
