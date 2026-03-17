def calculate_match_score(worker, job):

    worker_skills = [skill.strip().lower() for skill in worker.skills.split(",") if skill.strip()]

    job_title_words = job.title.strip().lower().split() if job.title else []
    job_category_words = job.category.strip().lower().split() if job.category else []
    job_description_words = job.description.strip().lower().split() if job.description else []
    job_keywords = set(job_title_words + job_category_words + job_description_words)
    
    matched_skills = 0
    for skill in worker_skills:
        if skill in job_keywords:
            matched_skills += 1
    skill_score = min(matched_skills * 25, 50)

    category_score = 0
    if job.category:
        if (job.category or "").strip().lower() in worker_skills:
            category_score = 20

    worker_address = (worker.address or "").strip().lower()
    job_location = job.location.strip().lower()

    if job_location and (job_location in worker_address or worker_address in job_location):
        location_score = 15
    else:
        location_score = 5

    status = (worker.verification_status or "").strip().lower()
    if status == "verified":
        verification_score = 10
    else:
        verification_score = 0

    if worker.risk_score <= 20:
        risk_score = 5
    elif worker.risk_score <= 50:
        risk_score = 3
    else:
        risk_score = 0

    total_score = skill_score + category_score + location_score + verification_score + risk_score
    return total_score