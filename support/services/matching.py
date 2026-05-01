import re


STOP_WORDS = {
    "a", "an", "and", "at", "for", "from", "in", "job", "of", "on",
    "or", "service", "services", "the", "to", "with", "work", "worker"
}


def normalize_words(text):
    if not text:
        return []
    return [
        word.strip().lower()
        for word in re.split(r"[^a-zA-Z0-9]+", text)
        if word.strip() and word.strip().lower() not in STOP_WORDS
    ]


def similar_word(left, right):
    if left == right:
        return True

    if len(left) < 4 or len(right) < 4:
        return False

    return left.startswith(right[:5]) or right.startswith(left[:5])


def overlap_count(left_words, right_words):
    count = 0
    matched_right = set()

    for left in left_words:
        for right in right_words:
            if right in matched_right:
                continue

            if similar_word(left, right):
                count += 1
                matched_right.add(right)
                break

    return count


def text_matches_phrase(phrase, text):
    phrase_words = normalize_words(phrase)
    text_words = normalize_words(text)

    if not phrase_words or not text_words:
        return False

    normalized_phrase = " ".join(phrase_words)
    normalized_text = " ".join(text_words)

    return normalized_phrase in normalized_text or overlap_count(phrase_words, text_words) > 0


def calculate_match_score(worker, job):
    relevance_score = 0

    worker_skills = [s.strip().lower() for s in (worker.skills or "").split(",") if s.strip()]
    worker_profession = (worker.profession or "").strip().lower()
    worker_address = (worker.address or "").strip().lower()

    job_title = (job.title or "").strip().lower()
    job_category = (job.category or "").strip().lower()
    job_description = (job.description or "").strip().lower()
    job_location = (job.location or "").strip().lower()

    job_text = f"{job_title} {job_category} {job_description}"
    job_words = set(normalize_words(job_text))
    worker_skill_words = set()
    profession_words = set(normalize_words(worker_profession))

    for skill in worker_skills:
        worker_skill_words.update(normalize_words(skill))

    if worker_profession and job_category:
        if text_matches_phrase(worker_profession, job_category):
            relevance_score += 35

    if worker_profession and text_matches_phrase(worker_profession, f"{job_title} {job_description}"):
        relevance_score += 20

    profession_overlap = overlap_count(profession_words, job_words)
    relevance_score += min(profession_overlap * 10, 20)

    for skill in worker_skills:
        if skill and text_matches_phrase(skill, job_text):
            relevance_score += 15

    relevance_score = min(relevance_score, 80)

    common_skill_words = overlap_count(worker_skill_words, job_words)
    relevance_score += min(common_skill_words * 5, 25)

    title_words = set(normalize_words(job_title))
    title_overlap = overlap_count(worker_skill_words.union(profession_words), title_words)
    relevance_score += min(title_overlap * 5, 15)

    if relevance_score <= 0:
        return 0

    score = relevance_score

    if worker_address and job_location:
        worker_address_words = set(normalize_words(worker_address))
        location_words = set(normalize_words(job_location))
        location_overlap = overlap_count(worker_address_words, location_words)

        if worker_address in job_location or job_location in worker_address:
            score += 15
        else:
            score += location_overlap * 3

    score += min(int(worker.experience or 0) * 2, 20)

    score += min(int(round((worker.rating or 0) * 5)), 25)

    return min(score, 100)
