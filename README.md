SafeHire – AI Powered Service Hiring Platform

SafeHire is a secure and intelligent web based service hiring platform designed to connect employers with verified workers.

The system integrates:

structured worker registration
AI-assisted matching logic
risk assessment
transparent hiring workflows

to ensure safe, reliable, and efficient hiring decisions.

The platform demonstrates how AI-assisted verification, structured worker data, and transparent hiring transactions can improve trust in digital service marketplaces.

Project Type

CSE299 – Junior Design Project

Project Overview

Traditional service hiring often suffers from:

Lack of worker verification
Risk of fraud or identity issues
No transparent hiring records

SafeHire addresses these problems by providing:

Worker registration with identity details
Risk score estimation (AI-assisted logic)
Worker verification system
Job posting platform
Secure hiring workflow
Transparent transaction history
Review and rating system
Current Features 
Backend (Flask + SQLite)
Worker Registration API (POST /add_worker)
Worker Listing API (GET /workers)
Worker Verification System (Admin)
Job Posting API (POST /add_job)
Job Listing API (GET /jobs_api)
AI Job Matching System
Job Application System (POST /apply_job)
Hiring Workflow (POST /hire)
Transaction System (GET /transactions_api)
Payment Completion System
Review & Rating System (decimal ratings supported)
Duplicate NID prevention
Frontend
Home Page
Login & Signup System
Worker Dashboard (AI matched jobs)
Admin Dashboard
Worker Verification Dashboard
Job Posting Page
Employer Hiring Interface
Transaction History Page
Review Submission Interface
AI Matching System

SafeHire uses a lightweight AI-based scoring system to match workers and jobs.

The system considers:

Skill similarity
Job category matching
Title keyword matching
Location similarity
Worker experience
Worker rating

This allows the system to recommend the most suitable workers and jobs dynamically.

Technologies Used
Backend
Python 3
Flask
Flask-SQLAlchemy
Flask-CORS
Database
SQLite
Frontend
HTML
Tailwind CSS
JavaScript (Fetch API)
How To Run The Project
Clone the repository
git clone https://github.com/diyanazia/SafeHire-An_AI_Powered_Service_Hiring_Platform.git
cd SafeHire-An_AI_Powered_Service_Hiring_Platform
Install Dependencies
pip install -r requirements.txt
Run the project
python main.py
Open in browser
http://127.0.0.1:5000


Contributing Members
Nazia Faruque Diya
Afridur Rahman Khan Mim

Conclusion

SafeHire demonstrates how AI-assisted matching, worker verification, and transparent hiring workflows can create a secure and efficient service hiring platform.