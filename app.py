from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from models import db, Student, Admin
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "admin_secret_key"  # Change in production

# Database configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance/database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File Upload Configuration
UPLOAD_FOLDER = os.path.join("static", "uploads", "students")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Helper function for allowed files
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database
db.init_app(app)

# Create Default Admin Account (ONE TIME)
with app.app_context():
    db.create_all() # Ensure tables exist
    if not Admin.query.filter_by(username="admin").first():
        admin = Admin(username="admin", password="admin123")
        db.session.add(admin)
        db.session.commit()
        print("Default admin account created.")

@app.route("/")
def home():
    students = Student.query.all()
    return render_template("home.html", students=students)

# -------------------------
# ADMIN LOGIN ROUTE
# -------------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        admin = Admin.query.filter_by(username=username, password=password).first()

        if admin:
            session["admin_logged_in"] = True
            session["admin_username"] = admin.username
            flash("Admin login successful!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password", "error")

    return render_template("admin_login.html")

# -------------------------
# ADMIN DASHBOARD (Protected)
# -------------------------
@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "error")
        return redirect(url_for("admin_login"))

    students = Student.query.order_by(Student.last_name).all()
    return render_template("admin_dashboard.html", students=students)

@app.route("/admin-edit-student/<id_number>", methods=["POST"])
def admin_edit_student(id_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    student = Student.query.get_or_404(id_number)

    student.first_name = request.form["first_name"]
    student.middle_name = request.form["middle_name"]
    student.last_name = request.form["last_name"]

    file = request.files.get("photo")

    if file and file.filename != "" and allowed_file(file.filename):
        # Delete old photo
        if student.photo:
            old_path = os.path.join(app.config["UPLOAD_FOLDER"], student.photo)
            if os.path.exists(old_path):
                os.remove(old_path)

        # Save new photo
        filename = secure_filename(f"{student.id_number}_{file.filename}")
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        student.photo = filename

    db.session.commit()
    flash("Student record updated successfully.", "success")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin-delete-student/<id_number>", methods=["POST"])
def admin_delete_student(id_number):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    student = Student.query.get_or_404(id_number)
    db.session.delete(student)
    db.session.commit()

    flash("Student record deleted.", "success")
    return redirect(url_for("admin_dashboard"))

# -------------------------
# ADMIN LOGOUT ROUTE
# -------------------------
@app.route("/admin-logout")
def admin_logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin-change-password", methods=["GET", "POST"])
def change_password():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "error")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        admin = Admin.query.filter_by(username=session["admin_username"]).first()

        if admin.password != current_password:
            flash("Current password is incorrect.", "error")

        elif new_password != confirm_password:
            flash("New passwords do not match.", "error")

        else:
            admin.password = new_password
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for("admin_dashboard"))

    return render_template("admin_change_password.html")

# -------------------------
# ADD STUDENT ROUTE (Admin Protected)
# -------------------------
@app.route("/admin/add-student", methods=["GET", "POST"])
def admin_add_student():
    if not session.get("admin_logged_in"):
        flash("Please login first.", "error")
        return redirect(url_for("admin_login"))

    if request.method == "POST":
        try:
            file = request.files.get("photo")
            filename = None

            if file and allowed_file(file.filename):
                filename = secure_filename(f"{request.form['id_number']}_{file.filename}")
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            student = Student(
                id_number=request.form["id_number"],
                first_name=request.form["first_name"],
                middle_name=request.form["middle_name"],
                last_name=request.form["last_name"],
                photo=filename
            )

            db.session.add(student)
            db.session.commit()

            flash("Student record added successfully!", "success")
            return redirect(url_for("admin_dashboard"))

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

# Redirect old /admin route to new dashboard
@app.route("/admin")
def old_admin_redirect():
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)
