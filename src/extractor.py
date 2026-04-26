import re
from bs4 import BeautifulSoup


EMAIL_PATTERN = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"


def clean_email(email: str) -> str:
    email = email.strip().lower()

    email = email.replace("u003e", "")
    email = email.replace(">", "")
    email = email.replace("&gt;", "")
    email = email.replace("%3e", "")

    email = email.strip(" \"'<>[](){}")

    return email


def is_valid_email(email: str) -> bool:
    if "@" not in email:
        return False

    if email.count("@") != 1:
        return False

    if "." not in email.split("@")[1]:
        return False

    blocked_prefixes = [
        "example@",
        "test@",
        "yourname@",
        "you@example",
    ]

    return not any(email.startswith(prefix) for prefix in blocked_prefixes)


def extract_emails_from_html(html: str) -> list[str]:
    found = re.findall(EMAIL_PATTERN, html)

    clean_emails = set()

    for email in found:
        cleaned = clean_email(email)
        if is_valid_email(cleaned):
            clean_emails.add(cleaned)

    return sorted(clean_emails)


def extract_visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(" ", strip=True).lower()


def extract_emails_from_pages(pages: dict[str, str]) -> list[str]:
    all_emails = set()

    for html in pages.values():
        emails = extract_emails_from_html(html)
        all_emails.update(emails)

    return sorted(all_emails)


def combine_visible_text_from_pages(pages: dict[str, str]) -> str:
    text_parts = []

    for html in pages.values():
        text_parts.append(extract_visible_text(html))

    return " ".join(text_parts).strip()