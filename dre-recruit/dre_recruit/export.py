"""Write dated CSVs: unaffiliated (hot list), affiliated, brokers."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

EXPORT_COLUMNS = [
    "license_number",
    "license_type",
    "affiliation_status",
    "first_name",
    "middle_name",
    "last_name",
    "issue_date",
    "days_since_licensed",
    "mailing_street",
    "mailing_city",
    "mailing_state",
    "mailing_zip",
    "employing_broker_license",
    "employing_broker_name",
    "google_url",
    "linkedin_url",
    "facebook_url",
    "instagram_url",
    "dre_verify_url",
    "outreach_status",
    "notes",
]


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    today = pd.Timestamp(date.today())
    df["days_since_licensed"] = (today - df["issue_date"]).dt.days
    df["outreach_status"] = ""
    df["notes"] = ""
    # Sort newest-first so freshest prospects are at the top.
    df = df.sort_values("issue_date", ascending=False, na_position="last")
    for col in EXPORT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[EXPORT_COLUMNS]


def write_csvs(df: pd.DataFrame, out_dir: Path, prefix: str = "san_diego") -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    df = _prepare(df)

    buckets = {
        f"{prefix}_unaffiliated.csv": df[df["affiliation_status"] == "UNAFFILIATED"],
        f"{prefix}_affiliated.csv":   df[df["affiliation_status"] == "AFFILIATED"],
        f"{prefix}_brokers.csv":      df[df["affiliation_status"] == "BROKER"],
    }
    written: list[Path] = []
    for name, part in buckets.items():
        p = out_dir / name
        part.to_csv(p, index=False)
        print(f"  {name}: {len(part):,} rows")
        written.append(p)
    return written
