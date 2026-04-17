def calculate_match_score(worker, job):
    """
    Smarter rule-based matching for SafeHire.

    Key improvements:
    1. Rejects irrelevant workers with no real service/category match
    2. Supports synonym groups (maid, cleaner, housekeeper, etc.)
    3. Uses job title/category/description together
    4. Rewards location, verification, experience, and low risk
       only after core relevance exists
    """

    def normalize_text(text):
        return (text or "").strip().lower()

    def split_keywords(text):
        cleaned = normalize_text(text)
        for ch in [",", ".", ";", ":", "/", "-", "_", "(", ")", "&"]:
            cleaned = cleaned.replace(ch, " ")
        return [word for word in cleaned.split() if word]

    # Worker data
    worker_skills_raw = normalize_text(worker.skills)
    worker_address = normalize_text(worker.address)
    worker_verification = normalize_text(worker.verification_status)
    worker_experience = worker.experience or 0
    worker_risk = worker.risk_score or 0

    worker_skill_words = set(split_keywords(worker_skills_raw))

    # Job data
    job_title = normalize_text(job.title)
    job_category = normalize_text(job.category)
    job_description = normalize_text(job.description)
    job_location = normalize_text(job.location)

    job_words = set(
        split_keywords(job_title) +
        split_keywords(job_category) +
        split_keywords(job_description)
    )

    # Service synonym groups
    service_groups = {
        "maid": {
            "maid", "cleaner", "cleaning", "housekeeping",
            "housekeeper", "domestic", "helper", "home", "care"
        },
        "mechanic": {
            "mechanic", "repair", "technician", "garage",
            "engine", "bike", "car", "motor", "vehicle"
        },
        "plumber": {
            "plumber", "plumbing", "pipe", "pipes",
            "sanitary", "water", "drain", "fittings", "tap"
        },
        "electrician": {
            "electrician", "electric", "wiring", "switch",
            "circuit", "light", "fan", "voltage", "socket"
        },
        "carpenter": {
            "carpenter", "wood", "furniture", "cabinet",
            "door", "table", "chair", "woodwork"
        },
        "painter": {
            "painter", "paint", "wall", "color", "coating"
        },
        "driver": {
            "driver", "driving", "car", "vehicle", "transport", "ride"
        },
        "cook": {
            "cook", "cooking", "chef", "kitchen", "meal", "food"
        },
        "gardener": {
            "gardener", "gardening", "plants", "garden", "lawn"
        }
    }

    # Detect job service group
    matched_job_groups = set()
    for group_name, keywords in service_groups.items():
        if any(word in keywords for word in job_words):
            matched_job_groups.add(group_name)

    # Detect worker service group
    matched_worker_groups = set()
    for group_name, keywords in service_groups.items():
        if any(word in keywords for word in worker_skill_words):
            matched_worker_groups.add(group_name)

    # Core service match
    common_groups = matched_job_groups.intersection(matched_worker_groups)

    # Exact keyword overlap
    exact_overlap = worker_skill_words.intersection(job_words)
    exact_match_score = min(len(exact_overlap) * 10, 30)

    # Group match score
    group_match_score = 0
    if common_groups:
        group_match_score = 40

    # Strong category direct match
    category_score = 0
    if job_category and (
        job_category in worker_skills_raw or
        job_category in worker_skill_words
    ):
        category_score = 20

    # Reject irrelevant workers completely
    if group_match_score == 0 and exact_match_score == 0 and category_score == 0:
        return 0

    # Location score
    location_score = 0
    if job_location and worker_address:
        if job_location in worker_address or worker_address in job_location:
            location_score = 10

    # Verification score
    verification_score = 10 if worker_verification == "verified" else 0

    # Experience score
    if worker_experience >= 5:
        experience_score = 10
    elif worker_experience >= 2:
        experience_score = 6
    elif worker_experience >= 1:
        experience_score = 3
    else:
        experience_score = 0

    # Rating score
    worker_rating = worker.rating or 0
    if worker_rating >= 4.5:
        rating_score = 10
    elif worker_rating >= 4.0:
        rating_score = 7
    elif worker_rating >= 3.0:
        rating_score = 4
    else:
        rating_score = 0

    # Risk score
    if worker_risk <= 20:
        risk_score = 5
    elif worker_risk <= 50:
        risk_score = 3
    else:
        risk_score = 0

    total_score = (
        group_match_score +
        exact_match_score +
        category_score +
        location_score +
        verification_score +
        experience_score +
        rating_score +
        risk_score
    )

    return total_score