from flask import jsonify, render_template, request
from support.app import app
from support.models import db, Worker, Job, HireTransaction
from support.services.matching import calculate_match_score


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/worker-dashboard")
def worker_dashboard():
    return render_template("worker_dashboard.html")


@app.route("/add-worker")
def add_worker_page():
    return render_template("worker_page.html")


@app.route("/verify-workers")
def verify_workers_page():
    return render_template("verify_workers.html")


@app.route("/jobs")
def jobs_page():
    return render_template("jobs.html")


@app.route("/transactions")
def transactions_page():
    return render_template("transactions.html")


@app.route("/workers", methods=["GET"])
def get_workers():
    workers = Worker.query.all()
    return jsonify([w.to_dict()
        for w in workers
    ])


@app.route("/add_worker", methods=["POST"])
def add_worker():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    nid = data.get("nid", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    skills = data.get("skills", "").strip()

    if not all([name, nid, phone, address, skills]):
        return jsonify({"error": "Missing required fields"}), 400

    if Worker.query.filter_by(nid=nid).first():
        return jsonify({"error": "Worker with this NID already exists"}), 400

    risk_score = len([s for s in skills.split(",") if s.strip()]) * 10

    new_worker = Worker(
        name=name,
        nid=nid,
        phone=phone,
        address=address,
        skills=skills,
        risk_score=risk_score,
        verification_status="Pending"
    )

    db.session.add(new_worker)
    db.session.commit()

    return jsonify({"message": "Worker added successfully"}), 201


@app.route("/verify_worker/<int:worker_id>", methods=["POST"])
def verify_worker(worker_id):
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip()

    if status not in ["Pending", "Verified", "Rejected"]:
        return jsonify({"error": "Invalid status"}), 400

    worker = Worker.query.get(worker_id)
    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    worker.verification_status = status
    db.session.commit()

    return jsonify({"message": "Worker Verification Updated"})


@app.route("/jobs_api", methods=["GET"])
def get_jobs():
    jobs = Job.query.all()
    return jsonify([job.to_dict() for job in jobs])

@app.route("/job_matches", methods=["GET"])
def get_job_matches():
    try:
        jobs = Job.query.all()
        workers = Worker.query.all()

        result = []

        for job in jobs:
            best_worker = None
            best_score = -1

            for worker in workers:
                if (worker.verification_status or "").strip().lower() != "verified":
                    continue

                score = calculate_match_score(worker, job)

                if score > best_score:
                    best_score = score
                    best_worker = worker

            result.append({
                "job_id": job.id,
                "job_title": job.title,
                "job_category": job.category,
                "job_location": job.location,
                "matched_worker": best_worker.name if best_worker else "No suitable worker found",
                "worker_id": best_worker.id if best_worker else None,
                "score": best_score if best_worker else None
           })

        return jsonify(result)
    except Exception as e:
       return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

@app.route("/add_job", methods=["POST"])
def add_job():
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
        title=title,
        category=category,
        location=location,
        budget=budget,
        description=description
    )

    db.session.add(new_job)
    db.session.commit()

    return jsonify({"message": "Job added successfully"}), 201


@app.route("/transactions_api", methods=["GET"])
def get_transactions():
    transactions = HireTransaction.query.all()
    result = []

    for t in transactions:
        worker = Worker.query.get(t.worker_id)
        job = Job.query.get(t.job_id)

        result.append({
            "id": t.id,
            "employer_name": t.employer_name,
            "worker_name": worker.name if worker else "Unknown",
            "job_title": job.title if job else "Unknown",
            "location": job.location if job else "Unknown",
            "status": t.status
        })

    return jsonify(result)


@app.route("/hire", methods=["POST"])
def hire_worker():
    data = request.get_json(silent=True) or {}

    employer_name = data.get("employer_name", "").strip()
    job_id = data.get("job_id")
    worker_id = data.get("worker_id")

    if not employer_name or not job_id or not worker_id:
        return jsonify({"error": "Missing required fields"}), 400

    worker = Worker.query.get(worker_id)
    job = Job.query.get(job_id)

    if not worker:
        return jsonify({"error": "Worker not found"}), 404

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if worker.verification_status != "Verified":
        return jsonify({"error": "Only verified workers can be hired"}), 400

    job.status = "assigned"

    transaction = HireTransaction(
        employer_name=employer_name,
        job_id=job_id,
        worker_id=worker_id,
        status="assigned"
    )

    db.session.add(transaction)
    db.session.commit()

    return jsonify({
        "message": "Hiring recorded successfully",
        "transaction": transaction.to_dict()
    }), 201