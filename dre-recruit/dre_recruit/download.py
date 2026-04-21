"""Download the monthly DRE new-licensee file.

DRE publishes monthly licensee data files at:
  https://www.dre.ca.gov/Licensees/ExamineeLicenseeListDataFiles.html

The hosted filename has historically followed patterns like
``monthlyrelicstats.txt`` or ``llisYYYYMM.txt`` and the format has shifted
between fixed-width text and delimited CSV. Rather than hard-code one URL
that will rot, this module scrapes the listing page for any link to a file
in the data-files directory and downloads the newest one.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import requests

LISTING_URL = "https://www.dre.ca.gov/Licensees/ExamineeLicenseeListDataFiles.html"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}
TIMEOUT = 60

# Match links to data files on the DRE site. Both .txt and .csv have shipped.
LINK_RE = re.compile(
    r'href=["\']([^"\']+\.(?:txt|csv|zip))["\']', re.IGNORECASE
)


def _list_candidates(html: str) -> list[str]:
    """Return all data-file links on the listing page."""
    return [m.group(1) for m in LINK_RE.finditer(html)]


def _pick_licensee_file(links: list[str]) -> str | None:
    """Pick the link most likely to be the licensee master/new-licensee file.

    We prefer filenames that mention "licens" (covers ``llis``,
    ``licensee``, ``licensees``) over generic data files.
    """
    lic = [l for l in links if "licens" in l.lower() or l.lower().startswith("/llis") or "/llis" in l.lower()]
    if lic:
        return lic[0]
    return links[0] if links else None


def fetch_latest(dest_dir: Path, *, month: str | None = None) -> Path:
    """Download the latest licensee file and return the local path.

    If ``month`` is given (``YYYY-MM``) it is used only to name the cached
    file; DRE's listing page surfaces the current month.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Fetching listing: {LISTING_URL}")
    r = requests.get(LISTING_URL, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()

    candidates = _list_candidates(r.text)
    if not candidates:
        raise RuntimeError(
            "No data-file links found on DRE listing page. "
            "The page layout may have changed; inspect manually."
        )
    chosen = _pick_licensee_file(candidates)
    if chosen is None:
        raise RuntimeError("Could not select a licensee data file.")

    file_url = urljoin(LISTING_URL, chosen)
    suffix = Path(chosen).suffix.lower()
    tag = month or "current"
    out_path = dest_dir / f"{tag}-{Path(chosen).name}"

    if out_path.exists() and out_path.stat().st_size > 0:
        print(f"Cached: {out_path} ({out_path.stat().st_size:,} bytes)")
        return out_path

    print(f"Downloading {file_url}")
    with requests.get(file_url, headers=HEADERS, timeout=TIMEOUT, stream=True) as resp:
        resp.raise_for_status()
        with open(out_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    fh.write(chunk)
    print(f"Downloaded {out_path} ({out_path.stat().st_size:,} bytes), suffix={suffix}")
    return out_path
