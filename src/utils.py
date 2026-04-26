from urllib.parse import urlparse, urlunparse
import os
import pandas as pd


def append_row_to_csv(row: dict, output_path) -> None:
    df = pd.DataFrame([row])

    file_exists = os.path.exists(output_path)

    df.to_csv(
        output_path,
        mode="a",
        header=not file_exists,
        index=False,
        encoding="utf-8-sig",
    )


def normalize_url(url: str) -> str:
    url = str(url).strip()

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    scheme = "https"
    netloc = parsed.netloc.lower().replace("www.", "")
    path = parsed.path.rstrip("/")

    return urlunparse((scheme, netloc, path, "", "", ""))


def get_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().replace("www.", "")


def ensure_output_dir(path) -> None:
    os.makedirs(path, exist_ok=True)


def save_to_csv(rows: list[dict], output_path) -> None:
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def save_dataframe_to_csv(df: pd.DataFrame, output_path) -> None:
    df.to_csv(output_path, index=False, encoding="utf-8-sig")


def load_contacted_domains(file_path) -> set[str]:
    if not os.path.exists(file_path):
        return set()

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    domains = {
        line.strip().lower().replace("www.", "")
        for line in lines
        if line.strip()
    }

    return domains