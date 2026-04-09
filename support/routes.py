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
    role = session.get('role')   
    return render_template('index.html', role=role)


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
    reviews = []

    if worker:
        assigned_jobs = Job.query.filter_by(assigned_worker_id=worker.id).all()
        reviews = Review.query.filter_by(worker_id=worker.id).all()

    return render_template(
        "worker_dashboard.html",
        username=session.get("username"),
        role=session.get("role"),
        worker=worker,
        assigned_jobs=assigned_jobs,
        reviews=reviews
    )


@app.route("/create-admin")
def create_admin():
    existing_admin = User.query.filter_by(username="admin").first()

    if existing_admin:
        return "Admin already exists!"

    admin = User(
        username="admin",
        password="123",
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()
    return "Admin created!"


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

    if not has_role("employer", "admin"):
        return redirect("/")

    return render_template(
        "jobs.html",
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


@app.route("/pay_transaction", methods=["POST"])
def pay_transaction():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Only employers can make payment"}), 403

    data = request.get_json(silent=True) or {}
    transaction_id = data.get("transaction_id")

    if not transaction_id:
        return jsonify({"error": "Transaction ID required"}), 400

    transaction = HireTransaction.query.get(transaction_id)

    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    if transaction.employer_id != session["user_id"]:
        return jsonify({"error": "Unauthorized"}), 403

    if transaction.status == "completed":
        return jsonify({"error": "Already paid"}), 400

    transaction.status = "completed"
    db.session.commit()

    return jsonify({"message": "Payment successful"}), 200


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