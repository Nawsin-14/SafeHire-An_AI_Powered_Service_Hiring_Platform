from flask import jsonify, render_template, redirect, request, session
from support.app import app
from support.models import db, Worker, Job, HireTransaction, User, Review
from support.services.matching import calculate_match_score
from sqlalchemy import desc


def is_logged_in():
    return "user_id" in session


def has_role(*roles):
    return session.get("role") in roles


@app.route("/")
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
    }), 200


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


@app.route("/add-worker")
def add_worker_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("worker"):
        return redirect("/")

    return render_template(
        "worker_page.html",
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/add_worker", methods=["POST"])
def add_worker():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("worker"):
        return jsonify({"error": "Only worker accounts can create worker profiles"}), 403

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    nid = data.get("nid", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    skills = data.get("skills", "").strip()
    experience = data.get("experience", 0)

    if not all([name, nid, phone, address, skills]):
        return jsonify({"error": "Missing required fields"}), 400

    if Worker.query.filter_by(nid=nid).first():
        return jsonify({"error": "Worker with this NID already exists"}), 400

    existing_worker = Worker.query.filter_by(user_id=session["user_id"]).first()
    if existing_worker:
        return jsonify({"error": "This account already has a worker profile"}), 400

    try:
        experience = int(experience)
    except (TypeError, ValueError):
        experience = 0

    risk_score = len([s for s in skills.split(",") if s.strip()]) * 10

    new_worker = Worker(
        user_id=session["user_id"],
        name=name,
        nid=nid,
        phone=phone,
        address=address,
        skills=skills,
        risk_score=risk_score,
        verification_status="Pending",
        experience=experience,
        rating=0.0
    )

    db.session.add(new_worker)
    db.session.commit()

    return jsonify({
        "message": "Worker profile created successfully",
        "worker": new_worker.to_dict()
    }), 201


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

    title = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip()
    location = (data.get("location") or "").strip()
    budget = data.get("budget")
    description = (data.get("description") or "").strip()

    if not all([title, category, location]) or budget in [None, ""]:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        budget = float(budget)
    except (TypeError, ValueError):
        return jsonify({"error": "Budget must be a number"}), 400

    new_job = Job(
        employer_id=session["user_id"],
        title=title,
        category=category,
        location=location,
        budget=budget,
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
            if (worker.verification_status or "").strip().lower() != "verified":
                continue

            score = calculate_match_score(worker, job)

            if score > 0:
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

    return jsonify(result), 200


@app.route("/hire", methods=["POST"])
def hire():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}

    job_id = data.get("job_id")
    worker_id = data.get("worker_id")

    if not job_id or not worker_id:
        return jsonify({"error": "Missing required fields"}), 400

    job = Job.query.get(job_id)
    worker = Worker.query.get(worker_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    if job.employer_id != session["user_id"]:
        return jsonify({"error": "You can only hire for your own jobs"}), 403

    if (job.status or "").lower() != "open":
        return jsonify({"error": "This job is already assigned"}), 400

    if (worker.verification_status or "").strip().lower() != "verified":
        return jsonify({"error": "Only verified workers can be hired"}), 400

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

    if not has_role("admin", "employer"):
        return redirect("/")

    return render_template(
        "transactions.html",
        username=session["username"],
        role=session["role"]
    )