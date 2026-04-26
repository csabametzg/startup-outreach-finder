import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str, timeout: int = 10) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


def is_valid_internal_link(base_url: str, full_url: str, href: str) -> bool:
    if not href:
        return False

    href = href.strip().lower()

    if href.startswith("#"):
        return False
    if href.startswith("javascript:"):
        return False
    if href.startswith("mailto:"):
        return False
    if href.startswith("tel:"):
        return False

    base_domain = urlparse(base_url).netloc.lower().replace("www.", "")
    link_domain = urlparse(full_url).netloc.lower().replace("www.", "")

    if not link_domain:
        return True

    return base_domain == link_domain


def score_link(field: str, combined_text: str, full_url: str) -> int:
    score = 0
    text = combined_text.lower()
    url = full_url.lower()

    positive_map = {
        "careers_url": ["careers", "career", "join our team", "work with us"],
        "jobs_url": ["jobs", "job", "open positions", "open roles", "vacancies"],
        "contact_url": ["contact", "contact us", "get in touch", "talk to us"],
        "about_url": ["about", "about us", "company", "who we are", "our story"],
    }

    negative_fragments = [
        "blog",
        "template",
        "templates",
        "publish",
        "pricing",
        "product",
        "features",
        "demo",
        "webinar",
        "academy",
        "docs",
        "learn",
        "guide",
        "customer",
        "case-study",
        "podcast",
        "community",
        "discord",
        "facebook",
        "twitter",
        "linkedin",
        "instagram",
        "login",
        "signup",
        "sign-up",
        "sign_in",
        "sign-in",
    ]

    for word in positive_map.get(field, []):
        if word in text:
            score += 10
        if word in url:
            score += 15

    for fragment in negative_fragments:
        if fragment in url:
            score -= 20

    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if path:
        slash_count = path.count("/")
        score -= slash_count * 2

    return score


def extract_relevant_links(base_url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all("a", href=True)

    result = {
        "careers_url": "",
        "jobs_url": "",
        "contact_url": "",
        "about_url": "",
    }

    keywords = {
        "careers_url": ["careers", "career", "join our team", "work with us"],
        "jobs_url": ["jobs", "job", "open positions", "open roles", "vacancies"],
        "contact_url": ["contact", "contact us", "get in touch", "talk to us"],
        "about_url": ["about", "about us", "company", "who we are", "our story"],
    }

    candidates = {
        "careers_url": [],
        "jobs_url": [],
        "contact_url": [],
        "about_url": [],
    }

    for link in links:
        href = link.get("href", "").strip()
        anchor_text = link.get_text(" ", strip=True).lower()
        full_url = urljoin(base_url, href)
        combined_text = f"{href.lower()} {anchor_text}"

        if not is_valid_internal_link(base_url, full_url, href):
            continue

        for field, words in keywords.items():
            if any(word in combined_text for word in words):
                candidates[field].append((score_link(field, combined_text, full_url), full_url))

    for field, values in candidates.items():
        if values:
            values.sort(key=lambda x: x[0], reverse=True)
            best_score, best_url = values[0]
            if best_score > 0:
                result[field] = best_url

    return result


def fetch_multiple_pages(urls: list[str]) -> dict[str, str]:
    pages = {}

    for url in urls:
        if not url:
            continue

        if url in pages:
            continue

        html = fetch_html(url)
        if html:
            pages[url] = html

    return pages