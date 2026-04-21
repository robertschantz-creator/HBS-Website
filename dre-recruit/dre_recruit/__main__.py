"""CLI entry: python -m dre_recruit run [--source PATH] [--month YYYY-MM]"""
import argparse
import sys
from datetime import date
from pathlib import Path

from . import download, parse, filter as filt, enrich, export

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_DIR = ROOT / "data"
OUTPUT = ROOT / "output"


def cmd_run(args: argparse.Namespace) -> int:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    if args.source:
        raw_path = Path(args.source)
        if not raw_path.exists():
            print(f"ERROR: --source file not found: {raw_path}", file=sys.stderr)
            return 2
        print(f"Using local source file: {raw_path}")
    else:
        raw_path = download.fetch_latest(DATA_RAW, month=args.month)

    df = parse.parse_file(raw_path)
    print(f"Parsed {len(df):,} records")

    sd_zips = filt.load_sd_zips(DATA_DIR / "san_diego_zips.csv")
    sd = filt.filter_san_diego(df, sd_zips)
    print(f"Filtered to San Diego County: {len(sd):,} records")

    sd = filt.classify_affiliation(sd)
    counts = sd["affiliation_status"].value_counts().to_dict()
    print(
        f"Unaffiliated: {counts.get('UNAFFILIATED', 0)}  |  "
        f"Affiliated: {counts.get('AFFILIATED', 0)}  |  "
        f"Brokers: {counts.get('BROKER', 0)}"
    )

    sd = enrich.add_search_urls(sd)

    out_dir = OUTPUT / date.today().isoformat()
    paths = export.write_csvs(sd, out_dir)
    for p in paths:
        print(f"Wrote {p}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dre_recruit")
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Download, filter, classify, export")
    run.add_argument("--source", help="Use a local DRE file instead of downloading")
    run.add_argument("--month", help="Target month YYYY-MM (default: current)")
    run.set_defaults(func=cmd_run)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
