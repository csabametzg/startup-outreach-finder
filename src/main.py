from pathlib import Path
import pandas as pd

from scraper import fetch_html, extract_relevant_links, fetch_multiple_pages
from extractor import (
    extract_emails_from_pages,
    combine_visible_text_from_pages,
)
from scorer import score_company, get_outreach_priority
from utils import (
    normalize_url,
    get_domain,
    ensure_output_dir,
    save_to_csv,
    save_dataframe_to_csv,
    load_contacted_domains,
    append_row_to_csv,
)


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "data" / "startups.csv"
CONTACTED_FILE = BASE_DIR / "data" / "contacted_domains.txt"
OUTPUT_DIR = BASE_DIR / "output"

ALL_LEADS_FILE = OUTPUT_DIR / "startup_leads.csv"
HIGH_PRIORITY_FILE = OUTPUT_DIR / "high_priority_leads.csv"
MANUAL_REVIEW_FILE = OUTPUT_DIR / "manual_review_leads.csv"
ALREADY_CONTACTED_FILE = OUTPUT_DIR / "already_contacted_leads.csv"
DISCARDED_FILE = OUTPUT_DIR / "discarded_leads.csv"


def process_company(company_name: str, website: str, contacted_domains: set[str]) -> dict:
    website = normalize_url(website)
    domain = get_domain(website)
    already_contacted = domain in contacted_domains

    print(f"Feldolgozás: {company_name} - {website}")

    homepage_html = fetch_html(website)

    if not homepage_html:
        return {
            "company_name": company_name,
            "website": website,
            "domain": domain,
            "already_contacted": already_contacted,
            "careers_url": "",
            "jobs_url": "",
            "contact_url": "",
            "about_url": "",
            "emails": "",
            "has_email": False,
            "has_careers_page": False,
            "pages_fetched": 0,
            "score": 0,
            "outreach_priority": "LOW",
            "score_reasons": "Homepage not reachable",
        }

    links = extract_relevant_links(website, homepage_html)

    urls_to_fetch = [
        website,
        links["contact_url"],
        links["careers_url"],
        links["jobs_url"],
        links["about_url"],
    ]

    pages = fetch_multiple_pages(urls_to_fetch)
    emails = extract_emails_from_pages(pages)
    combined_text = combine_visible_text_from_pages(pages)

    score, reasons = score_company(combined_text)

    has_email = len(emails) > 0
    has_careers_page = bool(links["careers_url"] or links["jobs_url"])

    outreach_priority = get_outreach_priority(
        score=score,
        has_email=has_email,
        has_careers_page=has_careers_page,
    )

    return {
        "company_name": company_name,
        "website": website,
        "domain": domain,
        "already_contacted": already_contacted,
        "careers_url": links["careers_url"],
        "jobs_url": links["jobs_url"],
        "contact_url": links["contact_url"],
        "about_url": links["about_url"],
        "emails": ", ".join(emails[:10]),
        "has_email": has_email,
        "has_careers_page": has_careers_page,
        "pages_fetched": len(pages),
        "score": score,
        "outreach_priority": outreach_priority,
        "score_reasons": " | ".join(reasons),
    }


def main():
    ensure_output_dir(OUTPUT_DIR)

    # if ALL_LEADS_FILE.exists():       # Option if we want to delete the exist file data
    #     ALL_LEADS_FILE.unlink()

    contacted_domains = load_contacted_domains(CONTACTED_FILE)
    df = pd.read_csv(INPUT_FILE)

    results = []

    for row_number, (_, row) in enumerate(df.iterrows(), start=1):
        result = process_company(
            company_name=row["company_name"],
            website=row["website"],
            contacted_domains=contacted_domains,
        )

        results.append(result)
        append_row_to_csv(result, ALL_LEADS_FILE)

        print(f"[{row_number}/{len(df)}] mentve")

    result_df = pd.DataFrame(results)

    already_contacted_df = result_df[
        result_df["already_contacted"] == True
    ].copy()

    high_priority_df = result_df[
        (result_df["outreach_priority"] == "HIGH")
        & (result_df["already_contacted"] == False)
    ].copy()

    manual_review_df = result_df[
        (
            (result_df["outreach_priority"] == "MEDIUM")
            | (
                (result_df["outreach_priority"] == "LOW")
                & (result_df["score"] >= 20)
            )
        )
        & (result_df["already_contacted"] == False)
    ].copy()

    discarded_df = result_df[
        (result_df["already_contacted"] == False)
        & ~result_df.index.isin(high_priority_df.index)
        & ~result_df.index.isin(manual_review_df.index)
    ].copy()

    high_priority_df = high_priority_df.sort_values(
        by=["score", "has_email", "has_careers_page"],
        ascending=[False, False, False],
    )

    manual_review_df = manual_review_df.sort_values(
        by=["score", "has_email", "has_careers_page"],
        ascending=[False, False, False],
    )

    already_contacted_df = already_contacted_df.sort_values(
        by=["score", "has_email", "has_careers_page"],
        ascending=[False, False, False],
    )

    discarded_df = discarded_df.sort_values(
        by=["score", "has_email", "has_careers_page"],
        ascending=[False, False, False],
    )

    save_dataframe_to_csv(high_priority_df, HIGH_PRIORITY_FILE)
    save_dataframe_to_csv(manual_review_df, MANUAL_REVIEW_FILE)
    save_dataframe_to_csv(already_contacted_df, ALREADY_CONTACTED_FILE)
    save_dataframe_to_csv(discarded_df, DISCARDED_FILE)

    print(f"\nDone. Saved here: {ALL_LEADS_FILE}")
    print(f"HIGH priority saved here: {HIGH_PRIORITY_FILE}")
    print(f"Manual review saved here: {MANUAL_REVIEW_FILE}")
    print(f"Already contacted saved here: {ALREADY_CONTACTED_FILE}")
    print(f"Discarded leadek saved here: {DISCARDED_FILE}")


if __name__ == "__main__":
    main()