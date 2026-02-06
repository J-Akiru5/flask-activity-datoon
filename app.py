from flask import Flask, render_template, request, redirect, url_for, flash
import os
from models import db, Student
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = "super_secret_key123"  # Change in production

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# ADD STUDENT ROUTE
# -------------------------
@app.route("/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":
        try:
            student = Student(
                id_number=request.form["id_number"],
                first_name=request.form["first_name"],
                middle_name=request.form["middle_name"],
                last_name=request.form["last_name"]
            )

            db.session.add(student)
            db.session.commit()

            flash("Student record added successfully!", "success")
            return redirect(url_for("home"))

        except IntegrityError:
            db.session.rollback()
            flash("Error: Student ID already exists.", "error")

        except Exception as e:
            db.session.rollback()
            flash("Unexpected error occurred.", "error")

    return render_template("add_student.html")

@app.route("/view-students")
def view_students():
    students = Student.query.all()
    return render_template("view_students.html", students=students)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
