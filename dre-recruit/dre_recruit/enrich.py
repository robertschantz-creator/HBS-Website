"""Build OSINT search URLs for each record.

These are plain search links — nothing is fetched, no APIs are called.
Paste the exported CSV into a spreadsheet and the URLs become clickable.
"""
from __future__ import annotations

from urllib.parse import quote_plus

import pandas as pd


def _google_url(first: str, last: str, city: str) -> str:
    q = f'"{first} {last}" "{city or "San Diego"}" real estate'
    return f"https://www.google.com/search?q={quote_plus(q)}"


def _linkedin_url(first: str, last: str, city: str) -> str:
    q = f"{first} {last} {city or 'San Diego'} real estate"
    return f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(q)}"


def _facebook_url(first: str, last: str, city: str) -> str:
    q = f"{first} {last} {city or 'San Diego'}"
    return f"https://www.facebook.com/search/people/?q={quote_plus(q)}"


def _instagram_url(first: str, last: str) -> str:
    handle = (first + last).lower()
    handle = "".join(c for c in handle if c.isalnum())
    return f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(handle)}"


def _dre_verify_url(license_number: str) -> str:
    if not license_number:
        return ""
    return (
        "https://www2.dre.ca.gov/PublicASP/pplinfo.asp"
        f"?License_id={quote_plus(license_number)}"
    )


def add_search_urls(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    first = df["first_name"].fillna("")
    last = df["last_name"].fillna("")
    city = df["mailing_city"].fillna("")
    df["google_url"] = [
        _google_url(f, l, c) for f, l, c in zip(first, last, city)
    ]
    df["linkedin_url"] = [
        _linkedin_url(f, l, c) for f, l, c in zip(first, last, city)
    ]
    df["facebook_url"] = [
        _facebook_url(f, l, c) for f, l, c in zip(first, last, city)
    ]
    df["instagram_url"] = [_instagram_url(f, l) for f, l in zip(first, last)]
    df["dre_verify_url"] = [_dre_verify_url(lic) for lic in df["license_number"]]
    return df
