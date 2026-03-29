from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)
    nid = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    skills = db.Column(db.String(200), nullable=False)
    risk_score = db.Column(db.Float, default=0)
    verification_status = db.Column(db.String(20),default="Pending")

    
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "nid": self.nid,
            "phone": self.phone,
            "address": self.address,
            "skills": self.skills,
            "risk_score": self.risk_score,
            "verification_status": self.verification_status
        }
    
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Float, nullable=False, default=0.0)

    description = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(20), default="open") 

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "location": self.location,
            "budget": self.budget,
            "description": self.description or "",
            "status": self.status
        }
    
class HireTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    employer_name = db.Column(db.String(120), nullable=False)

    job_id = db.Column(db.Integer, nullable=False)
    worker_id = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(20), default="assigned") 

    def to_dict(self):
        return {
            "id": self.id,
            "employer_name": self.employer_name,
            "job_id": self.job_id,
            "worker_id": self.worker_id,
            "status": self.status
        }
    
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False) 

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role
        }