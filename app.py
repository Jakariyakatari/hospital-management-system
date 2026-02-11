from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "hospital123"

# ================= CONFIG =================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "hospital.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "static", "uploads")

db = SQLAlchemy(app)

# ================= MODELS =================

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    specialization = db.Column(db.String(100))
    password = db.Column(db.String(100))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100))
    doctor_name = db.Column(db.String(100))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    problem = db.Column(db.Text)
    report = db.Column(db.String(200))
    suggestion = db.Column(db.Text)
    medicine = db.Column(db.Text)
    ai_analysis = db.Column(db.Text)

# ================= HOME =================

@app.route("/")
def home():
    return render_template("home.html")

# ================= PATIENT =================

@app.route("/patient/register", methods=["GET", "POST"])
def patient_register():
    if request.method == "POST":
        p = Patient(
            name=request.form["name"],
            email=request.form["email"],
            password=request.form["password"]
        )
        db.session.add(p)
        db.session.commit()
        return redirect("/patient/login")
    return render_template("patient/register.html")


@app.route("/patient/login", methods=["GET", "POST"])
def patient_login():
    if request.method == "POST":
        patient = Patient.query.filter_by(
            email=request.form["email"],
            password=request.form["password"]
        ).first()

        if patient:
            session["patient_name"] = patient.name
            return redirect("/patient/dashboard")
        else:
            return "Invalid patient login"

    return render_template("patient/login.html")


@app.route("/patient/dashboard")
def patient_dashboard():
    if "patient_name" not in session:
        return redirect("/patient/login")

    appointments = Appointment.query.filter_by(
        patient_name=session["patient_name"]
    ).all()

    return render_template(
        "patient/dashboard.html",
        reviews=appointments,
        patient=session["patient_name"]
    )


# ================= NORMAL BOOK APPOINTMENT =================

@app.route("/patient/book", methods=["GET", "POST"])
def patient_book():
    if "patient_name" not in session:
        return redirect("/patient/login")

    if request.method == "POST":

        file = request.files["report"]
        filename = ""

        if file and file.filename != "":
            os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
            filename = file.filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        a = Appointment(
            patient_name=session["patient_name"],
            doctor_name=request.form["doctor"],
            date=request.form["date"],
            time=request.form["time"],
            problem=request.form["problem"],
            report=filename
        )

        db.session.add(a)
        db.session.commit()

        flash("Appointment booked successfully!")
        return redirect("/patient/dashboard")

    return render_template("patient/book.html")


# ================= AI DOCTOR (INSTANT) =================

@app.route("/patient/ai", methods=["GET", "POST"])
def patient_ai():
    if "patient_name" not in session:
        return redirect("/patient/login")

    if request.method == "POST":

        problem_text = request.form["problem"]

        # Simple AI Logic
        if "fracture" in problem_text.lower():
            ai_result = "AI: Possible fracture detected. Recommend X-ray."
        elif "fever" in problem_text.lower():
            ai_result = "AI: Possible viral infection. Stay hydrated."
        elif "chest pain" in problem_text.lower():
            ai_result = "AI: Possible cardiac issue. Immediate evaluation required."
        elif "headache" in problem_text.lower():
            ai_result = "AI: Could be migraine or stress-related."
        else:
            ai_result = "AI: Further clinical evaluation required."

        ai_medicine = "AI Suggested Medicines: Paracetamol, Ibuprofen (if required)"

        a = Appointment(
            patient_name=session["patient_name"],
            problem=problem_text,
            ai_analysis=ai_result + " | " + ai_medicine
        )

        db.session.add(a)
        db.session.commit()

        flash("AI Analysis completed successfully!")
        return redirect("/patient/dashboard")

    return render_template("patient/ai.html")


# ================= DOCTOR =================

@app.route("/doctor/register", methods=["GET", "POST"])
def doctor_register():
    if request.method == "POST":
        d = Doctor(
            name=request.form["name"],
            specialization=request.form["specialization"],
            password=request.form["password"]
        )
        db.session.add(d)
        db.session.commit()
        return redirect("/doctor/login")
    return render_template("doctor/register.html")


@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        doctor = Doctor.query.filter_by(
            name=request.form["name"],
            password=request.form["password"]
        ).first()

        if doctor:
            session["doctor_name"] = doctor.name
            return redirect("/doctor/dashboard")
        else:
            return "Invalid doctor login"

    return render_template("doctor/login.html")


@app.route("/doctor/dashboard")
def doctor_dashboard():
    if "doctor_name" not in session:
        return redirect("/doctor/login")

    appointments = Appointment.query.filter_by(
        doctor_name=session["doctor_name"]
    ).all()

    return render_template("doctor/dashboard.html", appointments=appointments)


@app.route("/doctor/review/<int:id>", methods=["GET", "POST"])
def doctor_review(id):
    if "doctor_name" not in session:
        return redirect("/doctor/login")

    appt = Appointment.query.get(id)

    if request.method == "POST":
        appt.suggestion = request.form["suggestion"]
        appt.medicine = request.form["medicine"]
        db.session.commit()

        flash(f"Suggestion sent successfully to {appt.patient_name}")
        return redirect("/doctor/dashboard")

    return render_template("doctor/review.html", appt=appt)


# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
