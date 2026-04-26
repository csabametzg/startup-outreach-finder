# Startup Outreach Finder

A Python automation tool that collects startup websites, extracts useful contact and company information, scores companies based on relevance, and generates prioritized outreach lead lists.

The project was built to support targeted outreach for Python automation, API, data processing, and SaaS-related opportunities.

## Features

- Collects startup company websites
- Extracts contact, careers, jobs, and about page links
- Fetches multiple internal pages for analysis
- Extracts public email addresses from company pages
- Combines visible website text for scoring
- Scores companies based on keywords such as Python, automation, API, data, analytics, reporting, ETL, pipeline, and SaaS
- Applies negative scoring for less relevant terms such as senior, architect, infrastructure, or US-only
- Exports leads into prioritized CSV files:
  - high priority leads
  - manual review leads
  - already contacted leads
  - discarded leads

## Tech Stack

- Python
- pandas
- requests
- BeautifulSoup
- Selenium
- webdriver-manager
- lxml

## How It Works

1. Load startup websites from a CSV file.
2. Normalize company URLs and domains.
3. Fetch the homepage and relevant internal pages.
4. Extract contact, careers, jobs, and about links.
5. Extract public emails and visible website text.
6. Score each company based on keyword relevance.
7. Export categorized lead lists into CSV files.

## Example Input

```csv
company_name,website
Example SaaS,https://example.com
```


Example Output
```csv
company_name,website,domain,has_email,has_careers_page,score,outreach_priority,score_reasons
Example SaaS,https://example.com,example.com,True,True,65,HIGH,+ python (25) | + automation (20) | + api (15)
```

