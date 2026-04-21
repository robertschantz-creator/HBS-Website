"""San Diego filter + brokerage-affiliation classifier."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

# Secondary city-based safety net for ZIPs that straddle county lines.
SD_CITIES = {
    "alpine", "bonita", "boulevard", "campo", "cardiff by the sea", "carlsbad",
    "chula vista", "coronado", "del mar", "descanso", "dulzura", "el cajon",
    "encinitas", "escondido", "fallbrook", "guatay", "imperial beach",
    "jacumba", "jamul", "julian", "la jolla", "la mesa", "lakeside",
    "lemon grove", "mount laguna", "national city", "oceanside", "pala",
    "palomar mountain", "pauma valley", "pine valley", "potrero", "poway",
    "ramona", "ranchita", "rancho santa fe", "san diego", "san luis rey",
    "san marcos", "san ysidro", "santa ysabel", "santee", "solana beach",
    "spring valley", "tecate", "valley center", "vista", "warner springs",
    "bonsall", "camp pendleton",
}


def load_sd_zips(path: Path) -> set[str]:
    df = pd.read_csv(path, dtype=str)
    zips = set(df["zip"].str.strip().str.zfill(5))
    if not zips:
        raise RuntimeError(f"No ZIPs loaded from {path}")
    return zips


def filter_san_diego(df: pd.DataFrame, sd_zips: set[str]) -> pd.DataFrame:
    zip_match = df["mailing_zip"].str.zfill(5).isin(sd_zips)
    city_match = df["mailing_city"].str.strip().str.lower().isin(SD_CITIES)
    return df[zip_match | city_match].copy()


def classify_affiliation(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def _status(row: pd.Series) -> str:
        lt = (row["license_type"] or "").strip().lower()
        if lt.startswith("broker"):
            return "BROKER"
        if lt.startswith("salesperson"):
            return "UNAFFILIATED" if not row["employing_broker_license"] else "AFFILIATED"
        return "OTHER"

    df["affiliation_status"] = df.apply(_status, axis=1)
    return df
