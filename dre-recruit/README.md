# dre-recruit

Recruiting pipeline for a San Diego brokerage. Pulls the California DRE's
monthly licensee file, filters to San Diego County, flags whether each
licensee has "hung" their license under a broker yet, and writes CSVs with
pre-built Google/LinkedIn/Facebook/Instagram search URLs so you can find
contact info manually in a few seconds per person.

## Install

```
cd dre-recruit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```
python -m dre_recruit run
```

Output lands in `output/YYYY-MM-DD/`:
- `san_diego_unaffiliated.csv` — newly licensed salespeople with no broker
  yet. This is your hot list.
- `san_diego_affiliated.csv` — salespeople already hung with a broker.
- `san_diego_brokers.csv` — newly licensed brokers (different pitch: they
  can either hang their own shop or join yours).

Each row has:
- Name, license number, issue date, days since licensed
- Mailing address / city / ZIP
- Employing broker (if any)
- `google_url`, `linkedin_url`, `facebook_url`, `instagram_url` — click to
  look them up
- `dre_verify_url` — click to confirm current DRE status
- `outreach_status`, `notes` — blank columns for you to fill in

## Using a local file (offline, or if DRE's site blocks you)

Download the file manually from
<https://www.dre.ca.gov/Licensees/ExamineeLicenseeListDataFiles.html>
and pass it in:

```
python -m dre_recruit run --source /path/to/licensees.txt
```

## Maintenance

Two things can break, both easy to fix:

**1. DRE changes the file format.** Open `dre_recruit/parse.py`:
- If it's fixed-width, update the `LAYOUT` dict (1-based start positions
  and lengths per DRE's published record layout).
- If it's CSV, update `_CSV_COLUMN_MAP` with the new header strings.

**2. A ZIP is mis-assigned.** Edit `data/san_diego_zips.csv` to add/remove
ZIPs. Source of truth: HUD's USPS ZIP-county crosswalk or the SD County
website.

## Legal / compliance reminders (for you, not the tool)

- **CAN-SPAM**: any commercial email needs a real physical address and a
  working unsubscribe. Honor opt-outs.
- **TCPA / DNC**: do not cold-call or text cell phones from this list
  without checking the federal DNC registry and getting prior express
  written consent for SMS. Email and social DMs are lower-risk.
- **DRE Article 12**: California DRE has rules about soliciting licensees.
  Read them before sending.
- **CCPA**: if a California resident asks to be deleted, remove their row.

## Layout

```
dre-recruit/
├── dre_recruit/
│   ├── __main__.py   # CLI: python -m dre_recruit run
│   ├── download.py   # fetch DRE monthly file
│   ├── parse.py      # fixed-width or CSV → normalized DataFrame
│   ├── filter.py     # SD ZIP filter + affiliation classifier
│   ├── enrich.py     # build OSINT search URLs
│   └── export.py     # write dated CSVs
├── data/
│   ├── san_diego_zips.csv   # SD County ZIPs
│   └── raw/                 # cached downloads (gitignored)
├── output/                  # dated CSVs (gitignored)
├── requirements.txt
└── README.md
```
