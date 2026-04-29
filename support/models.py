from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(11), nullable=False)
    nid = db.Column(db.String(13), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    gender = db.Column(db.String(10), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "phone": self.phone,
            "nid": self.nid,
            "address": self.address,
            "gender": self.gender
        }

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)

    name = db.Column(db.String(100), nullable=False)
    nid = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.String(200), nullable=False)

    risk_score = db.Column(db.Float, default=0)
    verification_status = db.Column(db.String(20), default="Pending")
    experience = db.Column(db.Integer, default=0)
    rating = db.Column(db.Float, default=0.0)

    reviews = db.relationship("Review", backref="worker", lazy=True)
    applications = db.relationship("JobApplication", backref="worker", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "nid": self.nid,
            "phone": self.phone,
            "address": self.address,
            "skills": self.skills,
            "risk_score": self.risk_score,
            "verification_status": self.verification_status,
            "experience": self.experience,
            "rating": self.rating
        }


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default="open")
    assigned_worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=True)

    applications = db.relationship("JobApplication", backref="job", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "employer_id": self.employer_id,
            "title": self.title,
            "category": self.category,
            "location": self.location,
            "budget": self.budget,
            "description": self.description or "",
            "status": self.status,
            "assigned_worker_id": self.assigned_worker_id
        }


class HireTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)

    status = db.Column(db.String(20), default="assigned")
    amount = db.Column(db.Float, default=0.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "employer_id": self.employer_id,
            "worker_id": self.worker_id,
            "job_id": self.job_id,
            "status": self.status,
            "amount": self.amount,
            "created_at": str(self.created_at)
        }

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('hire_transaction.id'), nullable=False)

    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "employer_id": self.employer_id,
            "worker_id": self.worker_id,
            "transaction_id": self.transaction_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": str(self.created_at)
        }


class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)

    status = db.Column(db.String(20), default="applied")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('worker_id', 'job_id', name='unique_worker_job_application'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "worker_id": self.worker_id,
            "job_id": self.job_id,
            "status": self.status,
            "created_at": str(self.created_at)
        }
