"""Parse a DRE Examinee List CSV (people who passed the exam, not licensed).

Schema (April 2026 file format):
    full_name, first_middle_name, last_name, name_suffix,
    address_line_1, address_line_2, city, state,
    zip_or_nation, exam_type

Normalized output columns:
    first_name              str   (taken from first_middle_name; first token)
    middle_name             str   (remaining tokens of first_middle_name)
    last_name               str
    name_suffix             str
    license_type            str   ('Salesperson' | 'Broker' | 'Other')
    mailing_street          str   (address_line_1, plus address_line_2 if present)
    mailing_city            str
    mailing_state           str
    mailing_zip             str   (5 digits when US)
    license_number          str   ('' — examinees aren't licensed yet)
    issue_date              NaT   (no issue date — they haven't been issued one)
    expiration_date         NaT
    employing_broker_license str  ('' — N/A)
    employing_broker_name   str   ('' — N/A)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import parse as licensee_parse  # for NORMALIZED_COLUMNS

_HEADER_MAP = {
    "full_name": "full_name",
    "first_middle_name": "first_middle_name",
    "last_name": "last_name",
    "name_suffix": "name_suffix",
    "address_line_1": "address_line_1",
    "address_line_2": "address_line_2",
    "city": "city",
    "state": "state",
    "zip_or_nation": "zip_or_nation",
    "exam_type": "exam_type",
}


def _norm(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum())


def _split_first_middle(combined: str) -> tuple[str, str]:
    parts = combined.strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def parse_file(path: Path) -> pd.DataFrame:
    print(f"Parsing examinee CSV: {path.name}")
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)

    lookup = {_norm(c): c for c in raw.columns}
    rename: dict[str, str] = {}
    for normalized in _HEADER_MAP:
        key = _norm(normalized)
        if key in lookup:
            rename[lookup[key]] = normalized
    raw = raw.rename(columns=rename)

    for col in _HEADER_MAP:
        if col not in raw.columns:
            raw[col] = ""

    out = pd.DataFrame()
    fm_split = raw["first_middle_name"].fillna("").apply(_split_first_middle)
    out["first_name"] = [a for a, _ in fm_split]
    out["middle_name"] = [b for _, b in fm_split]
    out["last_name"] = raw["last_name"].fillna("").str.strip()
    out["name_suffix"] = raw["name_suffix"].fillna("").str.strip()

    exam = raw["exam_type"].fillna("").str.strip().str.upper()
    out["license_type"] = exam.map(
        {"BROKER": "Broker", "SALESPERSON": "Salesperson"}
    ).fillna("Other")

    street1 = raw["address_line_1"].fillna("").str.strip()
    street2 = raw["address_line_2"].fillna("").str.strip()
    out["mailing_street"] = [
        f"{a} {b}".strip() if b else a for a, b in zip(street1, street2)
    ]
    out["mailing_city"] = raw["city"].fillna("").str.strip()
    out["mailing_state"] = raw["state"].fillna("").str.strip()
    out["mailing_zip"] = (
        raw["zip_or_nation"].fillna("").str.replace(r"\D", "", regex=True).str[:5]
    )

    # Examinees aren't licensed yet — leave these blank/NaT.
    out["license_number"] = ""
    out["issue_date"] = pd.NaT
    out["expiration_date"] = pd.NaT
    out["employing_broker_license"] = ""
    out["employing_broker_name"] = ""

    # Reorder to match the licensee schema so downstream code is uniform.
    for col in licensee_parse.NORMALIZED_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    extras = [c for c in out.columns if c not in licensee_parse.NORMALIZED_COLUMNS]
    return out[licensee_parse.NORMALIZED_COLUMNS + extras]
