def score_company(text: str) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    positive_keywords = {
        "python": 25,
        "automation": 20,
        "api": 15,
        "data": 15,
        "analytics": 10,
        "integrations": 10,
        "reporting": 10,
        "etl": 10,
        "pipeline": 10,
        "saas": 10,
        "developer tools": 10,
    }

    negative_keywords = {
        "senior": -15,
        "staff": -20,
        "principal": -20,
        "architect": -20,
        "kubernetes": -10,
        "infrastructure": -10,
        "security clearance": -30,
        "must be located in us": -25,
        "us only": -25,
    }

    for keyword, points in positive_keywords.items():
        if keyword in text:
            score += points
            reasons.append(f"+ {keyword} ({points})")

    for keyword, points in negative_keywords.items():
        if keyword in text:
            score += points
            reasons.append(f"{keyword} ({points})")

    return score, reasons


def get_outreach_priority(score: int, has_email: bool, has_careers_page: bool) -> str:
    if score >= 50 and (has_email or has_careers_page):
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    return "LOW"