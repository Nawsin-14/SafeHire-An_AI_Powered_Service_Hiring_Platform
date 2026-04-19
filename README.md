SafeHire – AI Powered Service Hiring Platform

SafeHire is a secure and intelligent web-based service hiring platform designed to connect employers with verified workers.

The system integrates:

✔ Structured worker registration
✔ AI-assisted matching logic
✔ Risk assessment
✔ Transparent hiring workflows

to ensure safe, reliable, and efficient hiring decisions.

The platform demonstrates how AI-assisted verification, structured worker data, and transparent transactions improve trust in digital service marketplaces.

 Project Type

CSE299 – Junior Design Project

 Project Overview

Traditional service hiring often suffers from:

 Lack of worker verification
 Risk of fraud or identity issues
 No transparent hiring records
 SafeHire solves this by providing:
Worker registration with identity details
AI-assisted risk score estimation
Worker verification system
Job posting platform
Secure hiring workflow
Transparent transaction history
Review & rating system
 Current Features (Implemented)
 Backend (Flask + SQLite)
Worker Registration API (POST /add_worker)
Worker Listing API (GET /workers)
Worker Verification System
Job Posting API (POST /add_job)
Job Listing API (GET /jobs_api)
AI Job Matching System
Job Application System (POST /apply_job)
Hiring Workflow (POST /hire)
Transaction History (GET /transactions_api)
Payment Completion System
Review & Rating System (supports decimal ratings)
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
Review Submission System
 AI Matching System

SafeHire uses a lightweight AI-based scoring system to match workers and jobs.

 Matching Factors:
Skill similarity
Job category matching
Title keyword matching
Location similarity
Worker experience
The system still matches them using keyword similarity and assigns a match score.

 System Architecture
Frontend (HTML, Tailwind CSS, JS)
        ↓
Flask Backend (Routes + API)
        ↓
SQLite Database
        ↓
AI Matching Logic (matching.py)

 How To Run The Project
1 Clone Repository
git clone https://github.com/diyanazia/SafeHire-An_AI_Powered_Service_Hiring_Platform.git
cd SafeHire-An_AI_Powered_Service_Hiring_Platform
2️ Install Dependencies
pip install -r requirements.txt
3️ Run the Project
python main.py
4️ Open in Browser
http://127.0.0.1:5000

Technologies Used
Backend
Python (Flask)
Flask-SQLAlchemy
Flask-CORS
Database
SQLite
Frontend
HTML
Tailwind CSS
JavaScript (Fetch API)
Future Improvements
Real-time chat system
Notification system
Payment gateway integration
Advanced machine learning model
Mobile application
 Contributing Members
Nazia Faruque Diya
Afridur Rahman Khan Mim
Md. Zarif Hossain Alvi
 Conclusion

SafeHire demonstrates how AI-assisted matching, worker verification, and transparent hiring workflows can create a secure and efficient service hiring platform.