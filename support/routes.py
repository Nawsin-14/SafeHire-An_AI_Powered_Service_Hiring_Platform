from flask import jsonify, render_template, redirect, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user 
from support.app import app
from support.models import db, Worker, Job, HireTransaction, User, Review, JobApplication
from support.services.matching import calculate_match_score


def is_logged_in():
    return "user_id" in session


def has_role(*roles):
    return session.get("role") in roles


def verify_user_password(user, password):
    if not user or not password:
        return False

    stored_password = user.password or ""

    try:
        if check_password_hash(stored_password, password):
            return True
    except Exception:
        pass

    if stored_password == password:
        user.password = generate_password_hash(password)
        db.session.commit()
        return True

    return False


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

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        role = data.get("role", "").strip().lower()
        phone = data.get("phone", "").strip()
        nid = data.get("nid", "").strip()
        address = data.get("address", "").strip()
        gender = data.get("gender", "").strip().lower()

        if not all([username, password, role, phone, nid, address, gender]):
            return jsonify({"error": "All fields are required"}), 400

        if role not in ["worker", "employer"]:
            return jsonify({"error": "Invalid role selected"}), 400

        if not phone.isdigit() or len(phone) != 11:
            return jsonify({"error": "Phone number must be exactly 11 digits"}), 400

        if not nid.isdigit() or len(nid) != 13:
            return jsonify({"error": "NID must be exactly 13 digits"}), 400

        if gender not in ["male", "female", "other"]:
            return jsonify({"error": "Invalid gender selected"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400

        if hasattr(User, "phone"):
            existing_phone = User.query.filter_by(phone=phone).first()
            if existing_phone:
                return jsonify({"error": "Phone number already exists"}), 400

        if hasattr(User, "nid"):
            existing_nid = User.query.filter_by(nid=nid).first()
            if existing_nid:
                return jsonify({"error": "NID already exists"}), 400

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password,
            role=role,
            phone=phone,
            nid=nid,
            address=address,
            gender=gender
        )

        db.session.add(user)
        db.session.commit()

        return jsonify({
            "message": "Signup successful",
            "redirect": "/login"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Signup failed: {str(e)}"}), 500


@app.route("/login", methods=["GET", "POST"]) 

def login(): 

    if request.method == "GET": 

        return render_template("login.html") 

  

    try: 

       

        data = request.get_json(silent=True) or request.form.to_dict() or {} 

  

        username = data.get("username", "").strip() 

        password = data.get("password", "").strip() 

  

     

        if not username or not password: 

            return jsonify({"error": "Username and password are required"}), 400 

  

      

        user = User.query.filter_by(username=username).first() 

  

    

        if not user or not user.check_password(password):  # Assuming `check_password` is a method in the User model 

            return jsonify({"error": "Invalid credentials"}), 401 

  

     

        login_user(user) 

  

   

        if user.role == "admin": 

            redirect_url = "/admin-dashboard" 

        elif user.role == "worker": 

            redirect_url = "/worker-dashboard" 

        else: 

            redirect_url = "/jobs" 

  

        return jsonify({ 

            "message": "Login successful", 

            "role": user.role, 

            "redirect": redirect_url 

        }), 200 

  

    except Exception as e: 

        return jsonify({"error": f"Login failed: {str(e)}"}), 500 


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if username not in ["Nazia", "Afrid"]:
            return jsonify({"error": "Only Nazia or Afrid can login as admin"}), 403

        user = User.query.filter_by(username=username, role="admin").first()

        if not user:
            return jsonify({"error": "Admin account not found"}), 404

        if not verify_user_password(user, password):
            return jsonify({"error": "Invalid admin password"}), 401

        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role

        return jsonify({
            "message": "Admin login successful",
            "redirect": "/admin-dashboard"
        }), 200

    except Exception as e:
        return jsonify({"error": f"Admin login failed: {str(e)}"}), 500


from flask import redirect, url_for 

from flask_login import logout_user, login_required 

  

@app.route("/logout") 

@login_required 

def logout(): 

    logout_user() 

    return redirect(url_for("home"))   


@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect("/login")

    if session.get("role") == "admin":
        return redirect("/admin-dashboard")
    elif session.get("role") == "worker":
        return redirect("/worker-dashboard")
    elif session.get("role") == "employer":
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
    total_earnings = 0

    if worker:
        assigned_jobs = Job.query.filter_by(assigned_worker_id=worker.id).all()
        reviews = Review.query.filter_by(worker_id=worker.id).all()

        completed_transactions = HireTransaction.query.filter_by(
            worker_id=worker.id,
            status="completed"
        ).all()

        total_earnings = sum(t.amount or 0 for t in completed_transactions)

    return render_template(
        "worker_dashboard.html",
        username=session["username"],
        role=session["role"],
        worker=worker,
        assigned_jobs=assigned_jobs,
        reviews=reviews,
        total_earnings=total_earnings
    )


@app.route("/worker_jobs", methods=["GET"])
def worker_jobs():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("worker"):
        return jsonify({"error": "Unauthorized"}), 403

    worker = Worker.query.filter_by(user_id=session["user_id"]).first()
    if not worker:
        return jsonify([]), 200

    open_jobs = Job.query.filter_by(status="open").order_by(Job.id.desc()).all()

    applications = JobApplication.query.filter_by(worker_id=worker.id).all()
    applied_job_ids = {app_item.job_id for app_item in applications}

    matched_jobs = []

    for job in open_jobs:
        score = calculate_match_score(worker, job)

        if score > 0:
            matched_jobs.append({
                "id": job.id,
                "title": job.title,
                "category": job.category,
                "location": job.location,
                "budget": job.budget,
                "description": job.description or "",
                "score": score,
                "already_applied": job.id in applied_job_ids
            })

    matched_jobs.sort(key=lambda x: x["score"], reverse=True)

    return jsonify(matched_jobs), 200


@app.route("/apply_job", methods=["POST"])
def apply_job():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("worker"):
        return jsonify({"error": "Only workers can apply to jobs"}), 403

    try:
        worker = Worker.query.filter_by(user_id=session["user_id"]).first()
        if not worker:
            return jsonify({"error": "Worker profile not found"}), 404

        data = request.get_json(silent=True) or request.form.to_dict() or {}
        job_id = data.get("job_id")

        if not job_id:
            return jsonify({"error": "Job ID is required"}), 400

        job = Job.query.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if (job.status or "").lower() != "open":
            return jsonify({"error": "This job is no longer open"}), 400

        existing_application = JobApplication.query.filter_by(
            worker_id=worker.id,
            job_id=job.id
        ).first()

        if existing_application:
            return jsonify({"error": "You have already applied to this job"}), 400

        new_application = JobApplication(
            worker_id=worker.id,
            job_id=job.id,
            status="applied"
        )

        db.session.add(new_application)
        db.session.commit()

        return jsonify({"message": "Applied successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to apply: {str(e)}"}), 500


@app.route("/my_applications", methods=["GET"])
def my_applications():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("worker"):
        return jsonify({"error": "Unauthorized"}), 403

    worker = Worker.query.filter_by(user_id=session["user_id"]).first()
    if not worker:
        return jsonify([]), 200

    applications = JobApplication.query.filter_by(worker_id=worker.id).order_by(JobApplication.id.desc()).all()

    result = []
    for app_item in applications:
        job = Job.query.get(app_item.job_id)
        if not job:
            continue

        result.append({
            "application_id": app_item.id,
            "status": app_item.status,
            "job_id": job.id,
            "title": job.title,
            "category": job.category,
            "location": job.location,
            "budget": job.budget,
            "description": job.description or "",
            "job_status": job.status
        })

    return jsonify(result), 200


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

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}

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

        if Worker.query.filter_by(user_id=session["user_id"]).first():
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
            "worker": new_worker.to_dict(),
            "redirect": "/worker-dashboard"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create worker profile: {str(e)}"}), 500


@app.route("/update-worker")
def update_worker_page():
    if not is_logged_in():
        return redirect("/login")

    if not has_role("worker"):
        return redirect("/")

    worker = Worker.query.filter_by(user_id=session["user_id"]).first()
    if not worker:
        return redirect("/add-worker")

    return render_template(
        "update_worker.html",
        username=session.get("username"),
        role=session.get("role"),
        worker=worker
    )


@app.route("/update_worker", methods=["POST"])
def update_worker():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("worker"):
        return jsonify({"error": "Only worker accounts can update worker profiles"}), 403

    try:
        worker = Worker.query.filter_by(user_id=session["user_id"]).first()
        if not worker:
            return jsonify({"error": "Worker profile not found"}), 404

        data = request.get_json(silent=True) or request.form.to_dict() or {}

        name = data.get("name", "").strip()
        phone = data.get("phone", "").strip()
        address = data.get("address", "").strip()
        skills = data.get("skills", "").strip()
        experience = data.get("experience", 0)

        if not all([name, phone, address, skills]):
            return jsonify({"error": "Missing required fields"}), 400

        try:
            experience = int(experience)
        except (TypeError, ValueError):
            experience = 0

        worker.name = name
        worker.phone = phone
        worker.address = address
        worker.skills = skills
        worker.experience = experience
        worker.risk_score = len([s for s in skills.split(",") if s.strip()]) * 10

        db.session.commit()

        return jsonify({
            "message": "Profile updated successfully",
            "redirect": "/worker-dashboard"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update worker profile: {str(e)}"}), 500


@app.route("/workers", methods=["GET"])
def get_workers():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("admin"):
        return jsonify({"error": "Unauthorized"}), 403

    workers = Worker.query.all()
    return jsonify([w.to_dict() for w in workers]), 200


@app.route("/verify_worker/<int:worker_id>", methods=["POST"])
def verify_worker(worker_id):
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("admin"):
        return jsonify({"error": "Only admin can verify workers"}), 403

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}
        status = (data.get("status") or "").strip()

        if status not in ["Pending", "Verified", "Rejected"]:
            return jsonify({"error": "Invalid status"}), 400

        worker = Worker.query.get(worker_id)
        if not worker:
            return jsonify({"error": "Worker not found"}), 404

        worker.verification_status = status
        db.session.commit()

        return jsonify({"message": "Worker verification updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update worker verification: {str(e)}"}), 500


@app.route("/create-admins")
def create_admins():
    try:
        shared_password = "12345"

        admins_to_create = [
            {
                "username": "Nazia",
                "role": "admin",
                "phone": "01700000001",
                "nid": "1111111111111",
                "address": "Admin Office",
                "gender": "female"
            },
            {
                "username": "Afrid",
                "role": "admin",
                "phone": "01700000002",
                "nid": "2222222222222",
                "address": "Admin Office",
                "gender": "male"
            }
        ]

        created_any = False

        for admin_data in admins_to_create:
            existing_user = User.query.filter_by(username=admin_data["username"]).first()
            if not existing_user:
                admin = User(
                    username=admin_data["username"],
                    password=generate_password_hash(shared_password),
                    role=admin_data["role"],
                    phone=admin_data["phone"],
                    nid=admin_data["nid"],
                    address=admin_data["address"],
                    gender=admin_data["gender"]
                )
                db.session.add(admin)
                created_any = True

        if created_any:
            db.session.commit()
            return "Admins created successfully!"
        else:
            return "Admins already exist!"

    except Exception as e:
        db.session.rollback()
        return f"Failed to create admins: {str(e)}", 500


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
        username=session["username"],
        role=session["role"]
    )


@app.route("/jobs_api", methods=["GET"])
def jobs_api():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    if has_role("admin"):
        jobs = Job.query.order_by(Job.id.desc()).all()
    else:
        jobs = Job.query.filter(
            Job.employer_id == session["user_id"],
            Job.status != "completed"
        ).order_by(Job.id.desc()).all()

    result = []
    for job in jobs:
        result.append({
            "id": job.id,
            "title": job.title,
            "category": job.category,
            "location": job.location,
            "budget": job.budget,
            "description": job.description or "",
            "status": job.status,
            "assigned_worker_id": job.assigned_worker_id,
            "employer_id": job.employer_id
        })

    return jsonify(result), 200


@app.route("/job_applicants/<int:job_id>", methods=["GET"])
def job_applicants(job_id):
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Unauthorized"}), 403

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job.employer_id != session["user_id"]:
        return jsonify({"error": "You can only view applicants for your own jobs"}), 403

    applications = JobApplication.query.filter_by(job_id=job_id).order_by(JobApplication.id.desc()).all()

    result = []
    for app_item in applications:
        worker = Worker.query.get(app_item.worker_id)
        if not worker:
            continue

        score = calculate_match_score(worker, job)

        result.append({
            "application_id": app_item.id,
            "worker_id": worker.id,
            "worker_name": worker.name,
            "skills": worker.skills,
            "experience": worker.experience,
            "rating": worker.rating,
            "verification_status": worker.verification_status,
            "status": app_item.status,
            "score": score
        })

    result.sort(key=lambda x: x["score"], reverse=True)

    return jsonify(result), 200


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

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}

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

        return jsonify({
            "message": "Job added successfully",
            "redirect": "/jobs"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to add job: {str(e)}"}), 500


@app.route("/job_matches")
def job_matches():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    if has_role("admin"):
        jobs = Job.query.order_by(Job.id.desc()).all()
    else:
        jobs = Job.query.filter(
            Job.employer_id == session["user_id"],
            Job.status != "completed"
        ).order_by(Job.id.desc()).all()

    result = []

    for job in jobs:
        applications = JobApplication.query.filter_by(job_id=job.id).all()
        matches = []

        for app_item in applications:
            worker = Worker.query.get(app_item.worker_id)
            if not worker:
                continue

            if (worker.verification_status or "").strip().lower() != "verified":
                continue

            score = calculate_match_score(worker, job)

            if score > 0:
                matches.append({
                    "application_id": app_item.id,
                    "worker_id": worker.id,
                    "worker_name": worker.name,
                    "skills": worker.skills,
                    "rating": worker.rating,
                    "experience": worker.experience,
                    "score": score,
                    "application_status": app_item.status
                })

        matches.sort(key=lambda x: x["score"], reverse=True)

        result.append({
            "job_id": job.id,
            "job_title": job.title,
            "job_category": job.category,
            "job_location": job.location,
            "budget": job.budget,
            "status": job.status,
            "applicant_count": len(applications),
            "top_matches": matches[:5]
        })

    return jsonify(result), 200


@app.route("/hire", methods=["POST"])
def hire():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}

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

        application = JobApplication.query.filter_by(job_id=job.id, worker_id=worker.id).first()
        if not application:
            return jsonify({"error": "This worker has not applied for the job"}), 400

        job.status = "assigned"
        job.assigned_worker_id = worker_id

        application.status = "selected"

        other_applications = JobApplication.query.filter(
            JobApplication.job_id == job.id,
            JobApplication.worker_id != worker.id
        ).all()

        for other in other_applications:
            other.status = "rejected"

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

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to hire worker: {str(e)}"}), 500


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


@app.route("/transactions_api", methods=["GET"])
def get_transactions():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    try:
        if has_role("admin"):
            transactions = HireTransaction.query.all()
        elif has_role("employer"):
            transactions = HireTransaction.query.filter_by(
                employer_id=session["user_id"]
            ).all()
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
                "created_at": t.created_at.strftime("%Y-%m-%d") if t.created_at else "",
                "worker_id": t.worker_id,
                "job_id": t.job_id,
                "transaction_id": t.id
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": f"Failed to load transactions: {str(e)}"}), 500


@app.route("/complete-payment/<int:transaction_id>", methods=["POST"])
def complete_payment(transaction_id):
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer", "admin"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        transaction = HireTransaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        if has_role("employer") and transaction.employer_id != session["user_id"]:
            return jsonify({"error": "You can only pay your own transactions"}), 403

        transaction.status = "completed"

        job = Job.query.get(transaction.job_id)
        if job:
            job.status = "completed"

        db.session.commit()

        return jsonify({"message": "Payment completed successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to complete payment: {str(e)}"}), 500


@app.route("/add_review", methods=["POST"])
def add_review():
    if not is_logged_in():
        return jsonify({"error": "Login required"}), 401

    if not has_role("employer"):
        return jsonify({"error": "Only employers can submit reviews"}), 403

    try:
        data = request.get_json(silent=True) or request.form.to_dict() or {}

        worker_id = data.get("worker_id")
        transaction_id = data.get("transaction_id")
        rating = data.get("rating")
        comment = (data.get("comment") or "").strip()

        if not worker_id or not transaction_id or rating in [None, ""] or not comment:
            return jsonify({"error": "All review fields are required"}), 400

        try:
            worker_id = int(worker_id)
            transaction_id = int(transaction_id)
            rating = float(rating)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid review data"}), 400

        if rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be between 1 and 5"}), 400

        transaction = HireTransaction.query.get(transaction_id)
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404

        if transaction.employer_id != session["user_id"]:
            return jsonify({"error": "You can only review your own transactions"}), 403

        if transaction.worker_id != worker_id:
            return jsonify({"error": "Worker does not match this transaction"}), 400

        if (transaction.status or "").lower() != "completed":
            return jsonify({"error": "You can only review completed transactions"}), 400

        existing_review = Review.query.filter_by(transaction_id=transaction_id).first()
        if existing_review:
            return jsonify({"error": "Review already submitted for this transaction"}), 400

        worker = Worker.query.get(worker_id)
        if not worker:
            return jsonify({"error": "Worker not found"}), 404

        new_review = Review(
            employer_id=session["user_id"],
            worker_id=worker_id,
            transaction_id=transaction_id,
            rating=round(rating, 1),
            comment=comment
        )

        db.session.add(new_review)
        db.session.commit()

        all_reviews = Review.query.filter_by(worker_id=worker_id).all()
        if all_reviews:
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
            worker.rating = round(avg_rating, 1)
            db.session.commit()

        return jsonify({"message": "Review submitted successfully"}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to submit review: {str(e)}"}), 500