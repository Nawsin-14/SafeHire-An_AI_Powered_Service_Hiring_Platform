def normalize_words(text):
    if not text:
        return []
    return [word.strip().lower() for word in text.replace("/", " ").replace("-", " ").split() if word.strip()]


def calculate_match_score(worker, job):
    score = 0

    worker_skills = [s.strip().lower() for s in (worker.skills or "").split(",") if s.strip()]
    worker_address = (worker.address or "").strip().lower()

    job_title = (job.title or "").strip().lower()
    job_category = (job.category or "").strip().lower()
    job_description = (job.description or "").strip().lower()
    job_location = (job.location or "").strip().lower()

    job_text = f"{job_title} {job_category} {job_description}"
    job_words = set(normalize_words(job_text))
    worker_skill_words = set()

    for skill in worker_skills:
        worker_skill_words.update(normalize_words(skill))

    for skill in worker_skills:
        if skill and skill in job_text:
            score += 30

    common_words = worker_skill_words.intersection(job_words)
    score += len(common_words) * 10

    if job_category:
        for skill in worker_skills:
            if job_category in skill or skill in job_category:
                score += 20
                break

    title_words = set(normalize_words(job_title))
    title_overlap = worker_skill_words.intersection(title_words)
    score += len(title_overlap) * 8

    if worker_address and job_location:
        worker_address_words = set(normalize_words(worker_address))
        location_words = set(normalize_words(job_location))
        location_overlap = worker_address_words.intersection(location_words)

        if worker_address in job_location or job_location in worker_address:
            score += 15
        else:
            score += len(location_overlap) * 3

    score += int(worker.experience or 0) * 2

    score += int(round((worker.rating or 0) * 5))

    return score