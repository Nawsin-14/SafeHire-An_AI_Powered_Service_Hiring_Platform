from flask import jsonify, render_template, redirect, request, session
from support.app import app
from support.models import db, Worker, Job, HireTransaction, User, Review
from support.services.matching import calculate_match_score
from sqlalchemy import desc


def is_logged_in():
    return "user_id" in session


def has_role(*roles):
    return session.get("role") in roles


@app.route('/')
def home():
    role = session.get("role")
    username = session.get("username")

    total_workers = Worker.query.count()
    total_jobs = Job.query.count()

    return render_template(
        "index.html",
        role=role,
        username=username,
        total_workers=total_workers,
        total_jobs=total_jobs
    )


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "").strip()

    if not username or not password or role not in ["worker", "employer"]:
        return jsonify({"error": "Invalid input"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(username=username, password=password, role=role)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Signup successful"}), 201


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    data = request.get_json(silent=True) or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
        return jsonify({"error": "Invalid credentials"}), 401

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return jsonify({
        "message": "Login successful",
        "role": user.role,
        "redirect": "/admin-dashboard" if user.role == "admin"
        else "/worker-dashboard" if user.role == "worker"
        else "/jobs"
    })


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/login")

    if session["role"] == "admin":
        return redirect("/admin-dashboard")
    elif session["role"] == "worker":
        return redirect("/worker-dashboard")
    elif session["role"] == "employer":
        return redirect("/jobs")

    return redirect("/")


@app.route("/worker-dashboard")
def worker_dashboard():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("worker"):
        return redirect("/")

    worker = Worker.query.filter_by(user_id=session["user_id"]).first()

    assigned_jobs = []
    reviews = []

    if worker:
        assigned_jobs = Job.query.filter_by(assigned_worker_id=worker.id).all()
        reviews = Review.query.filter_by(worker_id=worker.id).all()

    return render_template(
        "worker_dashboard.html",
        username=session["username"],
        role=session["role"],
        worker=worker,
        assigned_jobs=assigned_jobs,
        reviews=reviews
    )


@app.route("/create-admin")
def create_admin():
    if User.query.filter_by(username="admin").first():
        return "Admin already exists!"

    admin = User(username="admin", password="123", role="admin")
    db.session.add(admin)
    db.session.commit()

    return "Admin created!"


@app.route("/admin-dashboard")
def admin_dashboard():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("admin"):
        return redirect("/")

    return render_template(
        "admin_dashboard.html",
        username=session["username"],
        role=session["role"],
        total_workers=Worker.query.count(),
        total_employers=User.query.filter_by(role="employer").count(),
        total_jobs=Job.query.count(),
        total_transactions=HireTransaction.query.count()
    )


@app.route("/jobs")
def jobs_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("employer", "admin"):
        return redirect("/")

    return render_template(
        "jobs.html",
        username=session["username"],
        role=session["role"]
    )


@app.route("/post-job")
def post_job_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("employer"):
        return redirect("/")

    return render_template(
        "post_job.html",
        username=session["username"],
        role=session["role"]
    )


@app.route("/add_job", methods=["POST"])
def add_job():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Only employers can post jobs"}), 403

    data = request.get_json(silent=True) or {}

    title = data.get("title")
    category = data.get("category")
    location = data.get("location")
    budget = data.get("budget")
    description = data.get("description")

    new_job = Job(
        employer_id=session["user_id"],
        title=title,
        category=category,
        location=location,
        budget=float(budget),
        description=description,
        status="open"
    )

    db.session.add(new_job)
    db.session.commit()

    return jsonify({"message": "Job added successfully"}), 201


@app.route("/job_matches")
def job_matches():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Unauthorized"}), 403

    jobs = Job.query.filter_by(employer_id=session["user_id"]).all()
    workers = Worker.query.all()

    result = []

    for job in jobs:
        matches = []

        for worker in workers:
            if worker.verification_status != "Verified":
                continue

            score = calculate_match_score(worker, job)

            matches.append({
                "worker_id": worker.id,
                "worker_name": worker.name,
                "skills": worker.skills,
                "rating": worker.rating,
                "experience": worker.experience,
                "score": score
            })

        matches.sort(key=lambda x: x["score"], reverse=True)

        result.append({
            "job_id": job.id,
            "job_title": job.title,
            "job_category": job.category,
            "job_location": job.location,
            "budget": job.budget,
            "status": job.status,
            "top_matches": matches[:3]
        })

    return jsonify(result)


@app.route("/hire", methods=["POST"])
def hire():
    data = request.get_json()

    job_id = data.get("job_id")
    worker_id = data.get("worker_id")

    job = Job.query.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    job.status = "assigned"
    job.assigned_worker_id = worker_id

    transaction = HireTransaction(
        employer_id=session["user_id"],
        worker_id=worker_id,
        job_id=job_id,
        status="assigned",
        amount=job.budget
    )

    db.session.add(transaction)
    db.session.commit()

    return jsonify({"message": "Worker hired successfully"}), 201


@app.route("/transactions")
def transactions_page():
    if not is_logged_in():
        return redirect("/login")

    return render_template(
        "transactions.html",
        username=session["username"],
        role=session["role"]
    )