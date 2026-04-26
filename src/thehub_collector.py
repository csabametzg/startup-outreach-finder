from pathlib import Path
import csv
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, urlunparse


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "thehub_startups.csv"

BASE_URL = "https://thehub.io/startups"
START_PAGE = 1
MAX_PAGES = 5

PROFILE_LINK_PREFIX = "https://thehub.io/startups/"


def setup_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


def ensure_output_file_exists() -> None:
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(["company_name", "website"])


def load_existing_websites() -> set[str]:
    existing = set()

    if not OUTPUT_FILE.exists():
        return existing

    with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        for row in reader:
            website = (row.get("website") or "").strip().lower()
            if website:
                existing.add(website)

    return existing


def append_row(company_name: str, website: str) -> None:
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow([company_name, website])


def accept_cookies_if_present(driver: webdriver.Chrome) -> None:
    possible_texts = [
        "Accept",
        "Accept all",
        "Allow all",
        "I agree",
    ]

    for text in possible_texts:
        try:
            buttons = driver.find_elements(By.XPATH, f"//button[contains(., '{text}')]")
            for button in buttons:
                if button.is_displayed() and button.is_enabled():
                    button.click()
                    time.sleep(1)
                    return
        except Exception:
            continue


def collect_profile_links_from_current_page(driver: webdriver.Chrome) -> list[str]:
    links = set()

    excluded_slugs = {
        "career-page",
        "join",
    }

    a_tags = driver.find_elements(By.TAG_NAME, "a")

    for tag in a_tags:
        href = (tag.get_attribute("href") or "").strip()

        if not href:
            continue

        if not href.startswith(PROFILE_LINK_PREFIX):
            continue

        if "?" in href:
            continue

        path_part = href.replace(PROFILE_LINK_PREFIX, "").strip("/")

        if not path_part:
            continue

        if "/" in path_part:
            continue

        if path_part in excluded_slugs:
            continue

        links.add(href)

    return sorted(links)


def extract_company_name(driver: webdriver.Chrome) -> str:
    selectors = [
        (By.TAG_NAME, "h1"),
        (By.CSS_SELECTOR, "h1"),
        (By.CSS_SELECTOR, "h2"),
        (By.XPATH, "//h1"),
        (By.XPATH, "//h2"),
    ]

    for by, value in selectors:
        try:
            elements = driver.find_elements(by, value)
            for element in elements:
                text = element.text.strip()
                if text and len(text) < 100:
                    return text
        except Exception:
            continue

    return ""


def extract_company_website(driver: webdriver.Chrome) -> str:
    blocked_domains = [
        "thehub.io",
        "cookieinformation.com",
        "tools.google.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "twitter.com",
        "x.com",
        "youtube.com",
    ]

    a_tags = driver.find_elements(By.TAG_NAME, "a")
    candidates = []

    for tag in a_tags:
        href = (tag.get_attribute("href") or "").strip()
        text = (tag.text or "").strip().lower()
        target = (tag.get_attribute("target") or "").strip().lower()
        class_name = (tag.get_attribute("class") or "").strip().lower()

        if not href:
            continue

        if not (href.startswith("http://") or href.startswith("https://")):
            continue

        if any(domain in href.lower() for domain in blocked_domains):
            continue

        score = 0

        if target == "_blank":
            score += 20

        if "." in text and " " not in text:
            score += 30

        if "text-blue-900" in class_name:
            score += 20

        normalized_href = (
            href.lower()
            .replace("http://", "")
            .replace("https://", "")
            .replace("www.", "")
            .strip("/")
        )
        normalized_text = text.replace("www.", "").strip("/")

        if normalized_text and normalized_href.startswith(normalized_text):
            score += 30

        candidates.append((score, href, text))

    if not candidates:
        return ""

    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score, best_href, best_text = candidates[0]
    return best_href


def collect_company_data(driver: webdriver.Chrome, profile_url: str) -> tuple[str, str]:
    print(f"  Open profile: {profile_url}")

    try:
        driver.get(profile_url)
    except TimeoutException:
        print("  Timeout on the profile page.")
        return "", ""

    time.sleep(3)

    company_name = extract_company_name(driver)
    website = extract_company_website(driver)

    print(f"  Found company name: {company_name}")
    print(f"  Found website: {website}")

    return company_name, website




def normalize_website_url(url: str) -> str:
    url = url.strip()

    if not url:
        return ""

    parsed = urlparse(url)

    scheme = "https"
    netloc = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/")

    normalized = urlunparse((scheme, netloc, path, "", "", ""))
    return normalized


def build_page_url(page_number: int) -> str:
    if page_number == 1:
        return BASE_URL
    return f"{BASE_URL}&page={page_number}"


def main():
    ensure_output_file_exists()
    existing_websites = load_existing_websites()

    driver = setup_driver()

    try:
        for page_number in range(START_PAGE, MAX_PAGES + 1):
            page_url = build_page_url(page_number)
            print(f"\n=== Page {page_number} ===")
            print(page_url)

            try:
                driver.get(page_url)
            except TimeoutException:
                print("The page load was interrupted due to a timeout.")
                continue

            time.sleep(3)
            accept_cookies_if_present(driver)

            profile_links = collect_profile_links_from_current_page(driver)
            print(f"Found profile links: {len(profile_links)}")

            for index, profile_url in enumerate(profile_links, start=1):
                print(f"[{index}/{len(profile_links)}] Processing...")

                company_name, website = collect_company_data(driver, profile_url)

                website = normalize_website_url(website)

                if not company_name:
                    print("  No company name, skipped.")
                    continue

                if not website:
                    print(f"  No website: {company_name}")
                    continue

                website_lower = website.lower().strip()

                if website_lower in existing_websites:
                    print(f"  Already exists, skipped: {website}")
                    continue

                append_row(company_name, website)
                existing_websites.add(website_lower)

                print(f"  Saved: {company_name} | {website}")

            print(f"Page done: {page_number} | unique websites so far: {len(existing_websites)}")

            time.sleep(2)

    finally:
        driver.quit()

    print(f"\nDone. Saved here: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()