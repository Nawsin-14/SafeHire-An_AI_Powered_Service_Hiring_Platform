from flask import jsonify, render_template, redirect, request, session
from support.app import app
from support.models import db, Worker, Job, HireTransaction, User
from support.services.matching import calculate_match_score


def is_logged_in():
    return "user_id" in session


def has_role(*roles):
    return session.get("role") in roles


@app.route("/")
def home():
    return render_template(
        "index.html",
        username=session.get("username"),
        role=session.get("role")
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

    new_user = User(
        username=username,
        password=password,
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Signup successful!!!"}), 201

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
     "message": "Login successful!!!",
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

    if session.get("role") == "admin":
        return redirect("/admin-dashboard")
    elif session.get("role") == "employer":
        return redirect("/jobs")
    elif session.get("role") == "worker":
        return redirect("/worker-dashboard")

    return redirect("/")


@app.route("/worker-dashboard")
def worker_dashboard():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("worker"):
        return redirect("/")

    worker = Worker.query.filter_by(user_id=session["user_id"]).first()
    assigned_jobs = []

    if worker:
        assigned_jobs = Job.query.filter_by(assigned_worker_id=worker.id).all()

    return render_template(
        "worker_dashboard.html",
        username=session.get("username"),
        role=session.get("role"),
        worker=worker,
        assigned_jobs=assigned_jobs
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


@app.route("/admin-workers")
def admin_workers_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("admin"):
        return redirect("/")

    return render_template(
        "admin_workers.html",
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/jobs")
def jobs_page():
    if not is_logged_in():
        return redirect("/login")

    return render_template(
        "jobs.html",
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/post-job")
def post_job_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("employer"):
        return redirect("/")

    return render_template(
        "post_job.html",
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/transactions")
def transactions_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("admin", "employer"):
        return redirect("/")

    return render_template(
        "transactions.html",
        username=session.get("username"),
        role=session.get("role")
    )


@app.route("/workers", methods=["GET"])
def get_workers():
    workers = Worker.query.all()
    return jsonify([w.to_dict() for w in workers])


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


@app.route("/verify_worker/<int:worker_id>", methods=["POST"])
def verify_worker(worker_id):
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("admin"):
        return jsonify({"error": "Only admin can verify workers"}), 403

    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip()

    if status not in ["Pending", "Verified", "Rejected"]:
        return jsonify({"error": "Invalid status"}), 400

    worker = Worker.query.get(worker_id)
    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    worker.verification_status = status
    db.session.commit()

    return jsonify({"message": "Worker verification updated successfully"}), 200


@app.route("/jobs_api", methods=["GET"])
def get_jobs():
    jobs = Job.query.all()
    return jsonify([job.to_dict() for job in jobs])


@app.route("/add_job", methods=["POST"])
def add_job():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Only employers can post jobs"}), 403

    data = request.get_json(silent=True) or {}

    title = data.get("title", "").strip()
    category = data.get("category", "").strip()
    location = data.get("location", "").strip()
    budget = data.get("budget")
    description = data.get("description", "").strip()

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
        status="open",
        assigned_worker_id=None
    )

    db.session.add(new_job)
    db.session.commit()

    return jsonify({
        "message": "Job added successfully",
        "job": new_job.to_dict()
    }), 201


@app.route("/job_matches", methods=["GET"])
def get_job_matches():
    try:
        jobs = Job.query.all()
        workers = Worker.query.all()

        result = []

        for job in jobs:
            matched_workers = []

            for worker in workers:
                if (worker.verification_status or "").strip().lower() != "verified":
                    continue

                score = calculate_match_score(worker, job)

                matched_workers.append({
                    "worker_id": worker.id,
                    "worker_name": worker.name,
                    "skills": worker.skills,
                    "risk_score": worker.risk_score,
                    "verification_status": worker.verification_status,
                    "rating": worker.rating,
                    "experience": worker.experience,
                    "score": score
                })

            matched_workers.sort(key=lambda x: x["score"], reverse=True)

            result.append({
                "job_id": job.id,
                "job_title": job.title,
                "job_category": job.category,
                "job_location": job.location,
                "budget": job.budget,
                "status": job.status,
                "top_matches": matched_workers[:3]
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


@app.route("/hire", methods=["POST"])
def hire_worker():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Only employers can hire workers"}), 403

    data = request.get_json(silent=True) or {}

    job_id = data.get("job_id")
    worker_id = data.get("worker_id")

    if not job_id or not worker_id:
        return jsonify({"error": "Missing required fields"}), 400

    worker = Worker.query.get(worker_id)
    job = Job.query.get(job_id)

    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.employer_id != session["user_id"]:
        return jsonify({"error": "You can only hire for your own jobs"}), 403

    if worker.verification_status != "Verified":
        return jsonify({"error": "Only verified workers can be hired"}), 400

    if job.status != "open":
        return jsonify({"error": "This job is not available"}), 400

    job.status = "assigned"
    job.assigned_worker_id = worker.id

    transaction = HireTransaction(
        employer_id=session["user_id"],
        worker_id=worker.id,
        job_id=job.id,
        status="assigned",
        amount=job.budget
    )

    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "message": "Worker hired successfully",
        "transaction": transaction.to_dict()
    }), 201


@app.route("/transactions_api", methods=["GET"])
def get_transactions():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if has_role("admin"):
        transactions = HireTransaction.query.all()
    elif has_role("employer"):
        transactions = HireTransaction.query.filter_by(employer_id=session["user_id"]).all()
    else:
        return jsonify({"error": "Unauthorized"}), 403

    result = []

    for t in transactions:
        worker = Worker.query.get(t.worker_id)
        job = Job.query.get(t.job_id)
        employer = User.query.get(t.employer_id)

        result.append({
            "id": t.id,
            "employer_name": employer.username if employer else "Unknown",
            "worker_name": worker.name if worker else "Unknown",
            "job_title": job.title if job else "Unknown",
            "location": job.location if job else "Unknown",
            "amount": t.amount,
            "status": t.status,
            "created_at": str(t.created_at)
        })

    return jsonify(result)

@app.route("/admin-dashboard")
def admin_dashboard():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("admin"):
        return redirect("/")

    total_workers = Worker.query.count()
    total_employers = User.query.filter_by(role="employer").count()
    total_jobs = Job.query.count()
    total_transactions = HireTransaction.query.count()

    return render_template(
        "admin_dashboard.html",
        username=session.get("username"),
        role=session.get("role"),
        total_workers=total_workers,
        total_employers=total_employers,
        total_jobs=total_jobs,
        total_transactions=total_transactions
    )
