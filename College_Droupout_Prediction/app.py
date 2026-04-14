
import os
import mysql.connector
from dotenv import load_dotenv

from flask import Flask, redirect, render_template, request, url_for

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "dropout_prediction")
    )
    return conn



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
        cursor = conn.cursor()

        # 1) Insert into student table
        cursor.execute(
            """
            INSERT INTO student (name, age, class, school_name, location)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                data["name"],
                data["age"],
                data["class_name"],
                None,   # leave as NULL
                None    # leave as NULL
            )
        )

        # get newly created student id
        student_id = cursor.lastrowid

        # 2) Insert into attendance table
        cursor.execute(
            """
            INSERT INTO attendance
            (student_id, total_days, present_days, attendance_percentage)
            VALUES (%s, %s, %s, %s)
            """,
            (
                student_id,
                200,
                int((data["attendance"] / 100) * 200),
                data["attendance"]
            )
        )

        # 3) Insert into academic performance
        marks = data["marks"]

        if marks >= 80:
            grade = "A"
        elif marks >= 60:
            grade = "B"
        elif marks >= 40:
            grade = "C"
        else:
            grade = "D"

        cursor.execute(
            """
            INSERT INTO academic_performance
            (student_id, subject, marks, grade)
            VALUES (%s, %s, %s, %s)
            """,
            (
                student_id,
                None,   # subject not asked on website -> NULL
                marks,
                grade
            )
        )

        # 4) Insert into family background
        income_map = {
            "low": 15000,
            "medium": 30000,
            "high": 50000
        }

        parent_income = income_map.get(
            data["family_income"], None
        )

        financial_support = (
            "No"
            if data["parental_support"] == "low"
            else "Yes"
        )

        cursor.execute(
            """
            INSERT INTO family_background
            (student_id, parent_income,
             parent_education, family_size,
             financial_support)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                student_id,
                parent_income,
                None,   # NULL
                None,   # NULL
                financial_support
            )
        )

        # 5) Insert into prediction result
        cursor.execute(
            """
            INSERT INTO prediction_result
            (student_id, risk_level, prediction_date)
            VALUES (%s, %s, CURDATE())
            """,
            (
                student_id,
                risk_label
            )
        )

        conn.commit()
        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print("Database Error:", e)
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
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, name, age, class_name,
               attendance, marks,
               parental_support, family_income,
               risk_label, risk_score, created_at
        FROM Student
        ORDER BY id DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "students.html",
        students=records,
        current_page="students"
    )


@app.route("/delete-student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM Student WHERE id = %s",
        (student_id,)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("students"))


if __name__ == "__main__":
    app.run(debug=True)
