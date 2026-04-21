"""Parse a DRE licensee data file into a normalized DataFrame.

DRE has shipped this file as both fixed-width text and as a delimited CSV
across the years. We auto-detect by extension and by sniffing the first few
lines, then normalize to a common schema.

Normalized columns (all strings unless noted):
    license_number              str   (digits only, leading zeros preserved)
    license_type                str   ('Salesperson' | 'Broker' | 'Other')
    first_name                  str
    middle_name                 str
    last_name                   str
    mailing_street              str
    mailing_city                str
    mailing_state               str
    mailing_zip                 str   (5 digits, no extension)
    issue_date                  pd.Timestamp or NaT
    expiration_date             pd.Timestamp or NaT
    employing_broker_license    str   ('' if none)
    employing_broker_name       str   ('' if none)

If DRE changes the column layout, update LAYOUT (fixed-width) or
``_CSV_COLUMN_MAP`` (CSV).
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd

# ---------------------------------------------------------------------------
# Fixed-width layout (best-effort — verify against DRE's record-layout PDF on
# first run by spot-checking a few rows). Each value is (start, length) using
# 1-based start positions to match DRE documentation, converted internally.
# ---------------------------------------------------------------------------
LAYOUT: dict[str, tuple[int, int]] = {
    "license_number":           (1, 8),
    "license_type":             (9, 1),    # 'B' broker, 'S' salesperson, etc.
    "last_name":                (10, 30),
    "first_name":               (40, 20),
    "middle_name":              (60, 20),
    "mailing_street":           (80, 40),
    "mailing_city":             (120, 25),
    "mailing_state":            (145, 2),
    "mailing_zip":              (147, 9),   # zip + zip4
    "issue_date":               (156, 8),   # YYYYMMDD
    "expiration_date":          (164, 8),   # YYYYMMDD
    "employing_broker_license": (172, 8),
    "employing_broker_name":    (180, 50),
}

# ---------------------------------------------------------------------------
# CSV column-name map (DRE's headers vary in case/spelling). Keys are the
# normalized name; values are candidate header strings to match (case-
# insensitive, whitespace-insensitive).
# ---------------------------------------------------------------------------
_CSV_COLUMN_MAP: Mapping[str, tuple[str, ...]] = {
    "license_number":           ("license id", "license_id", "license number", "licensenumber", "lic id"),
    "license_type":             ("license type", "lic type", "type"),
    "last_name":                ("last name", "lastname", "last"),
    "first_name":               ("first name", "firstname", "first"),
    "middle_name":              ("middle name", "middlename", "middle"),
    "mailing_street":           ("mailing address", "mail address", "address", "street"),
    "mailing_city":             ("city", "mailing city"),
    "mailing_state":            ("state", "mailing state"),
    "mailing_zip":              ("zip", "zip code", "mailing zip", "postal code"),
    "issue_date":               ("issue date", "license issue date", "issued"),
    "expiration_date":          ("expiration date", "expire date", "expires"),
    "employing_broker_license": ("employing broker license", "broker license id", "responsible broker license"),
    "employing_broker_name":    ("employing broker", "broker name", "responsible broker"),
}

NORMALIZED_COLUMNS = list(LAYOUT.keys())


def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".txt", ".dat"}:
        with open(path, "r", encoding="latin-1", errors="replace") as fh:
            head = fh.readline()
        # CSV-ish if commas significantly outnumber spaces
        if head.count(",") >= 5:
            return "csv"
        return "fixed"
    if suffix == ".zip":
        raise NotImplementedError(
            "Zipped DRE archive received. Unzip manually and pass --source <unzipped file>."
        )
    # Default: try CSV first, fall back to fixed.
    return "csv"


def _parse_fixed(path: Path) -> pd.DataFrame:
    colspecs = []
    names = []
    for name, (start, length) in LAYOUT.items():
        colspecs.append((start - 1, start - 1 + length))
        names.append(name)
    df = pd.read_fwf(
        path,
        colspecs=colspecs,
        names=names,
        dtype=str,
        encoding="latin-1",
        keep_default_na=False,
    )
    return df


def _parse_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="latin-1", keep_default_na=False)
    # Map DRE's headers to our normalized names.
    header_lookup = {_norm(c): c for c in df.columns}
    rename: dict[str, str] = {}
    for normalized, candidates in _CSV_COLUMN_MAP.items():
        for cand in candidates:
            key = _norm(cand)
            if key in header_lookup:
                rename[header_lookup[key]] = normalized
                break
    df = df.rename(columns=rename)
    # Add any missing normalized columns as empty so downstream code is uniform.
    for col in NORMALIZED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[NORMALIZED_COLUMNS]


def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in NORMALIZED_COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # license_number: digits only, preserve leading zeros for display
    df["license_number"] = df["license_number"].str.replace(r"\D", "", regex=True)

    # license_type: map single-letter codes to readable names
    type_map = {"S": "Salesperson", "B": "Broker"}
    df["license_type"] = df["license_type"].apply(
        lambda v: type_map.get(v.strip().upper()[:1], v.strip().title() or "Other")
    )

    # zip: take first 5 digits
    df["mailing_zip"] = df["mailing_zip"].str.replace(r"\D", "", regex=True).str[:5]

    # dates: YYYYMMDD or various string forms
    df["issue_date"] = pd.to_datetime(df["issue_date"], errors="coerce", format="mixed")
    df["expiration_date"] = pd.to_datetime(df["expiration_date"], errors="coerce", format="mixed")

    # employing-broker license: digits only, blank if empty or all-zero
    df["employing_broker_license"] = (
        df["employing_broker_license"]
        .str.replace(r"\D", "", regex=True)
        .apply(lambda v: "" if (not v or set(v) == {"0"}) else v)
    )
    return df


def parse_file(path: Path) -> pd.DataFrame:
    fmt = _detect_format(path)
    print(f"Parsing {path.name} as {fmt}")
    if fmt == "csv":
        df = _parse_csv(path)
    else:
        df = _parse_fixed(path)
    df = _coerce(df)
    return df
