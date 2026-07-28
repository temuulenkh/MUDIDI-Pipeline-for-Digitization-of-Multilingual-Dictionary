"""
CLI: convert per-page MDF files to a single combined TSV for RStudio.

Usage:
    mudidi-mdf-to-tsv \\
        --stage2-dir outputs/stage-2 \\
        [--output combined.tsv]
"""
import argparse
import csv
import sys
from pathlib import Path


def _key_to_column(key: str) -> str:
    return "_".join(part.capitalize() for part in key.split("_") if part)


def _collect_extra_keys(rows: list[dict]) -> list[str]:
    seen: dict[str, None] = {}
    for row in rows:
        for k in (row.get("extra_fields") or {}).keys():
            if k and k not in seen:
                seen[k] = None
    return list(seen.keys())


def _join(value) -> str:
    if isinstance(value, list):
        return " | ".join(str(v) for v in value if v)
    return str(value) if value else ""


CANONICAL_FIELDS = [
    "Block_ID",
    "Entry_Type",
    "Headword",
    "Parent_Lexeme",
    "Sense_Number",
    "Homonym_Number",
    "Gloss",
    "Gloss_Secondary",
    "Usage_Note",
    "POS",
    "Phonetic",
    "Cross_References",
    "Examples",
    "Example_Glosses",
    "Source_Page",
]


def _make_block_id(row: dict) -> str:
    hw = row.get("headword", "")
    hm = row.get("homonym_number")
    return f"{hw}:{hm}" if hm else hw


def convert(stage2_dir: Path, output: Path) -> int:
    from mudidi.utils.mdf_parser import parse_mdf_text

    if not stage2_dir.exists():
        print(f"ERROR: Stage-2 output directory not found: {stage2_dir}", file=sys.stderr)
        return 1

    mdf_files = sorted(
        stage2_dir.glob("*/*.mdf.txt"),
        key=lambda p: int("".join(filter(str.isdigit, p.parent.name)) or 0),
    )
    if not mdf_files:
        print(f"ERROR: No .mdf.txt files found under {stage2_dir}", file=sys.stderr)
        return 1

    all_rows: list[dict] = []
    for mdf_path in mdf_files:
        source_page = mdf_path.parent.name
        rows = parse_mdf_text(mdf_path.read_text(encoding="utf-8"), source_page=source_page)
        all_rows.extend(rows)

    if not all_rows:
        print("WARNING: No entries parsed from MDF files.", file=sys.stderr)
        return 0

    extra_keys = _collect_extra_keys(all_rows)
    extra_columns = [_key_to_column(k) for k in extra_keys]
    fieldnames = CANONICAL_FIELDS + extra_columns

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for row in all_rows:
            extras = row.get("extra_fields") or {}
            tsv_row = {
                "Block_ID": _make_block_id(row),
                "Entry_Type": row.get("entry_type", "main"),
                "Headword": row.get("headword", ""),
                "Parent_Lexeme": row.get("parent_lexeme", ""),
                "Sense_Number": "" if row.get("sense_number") is None else str(row["sense_number"]),
                "Homonym_Number": "" if row.get("homonym_number") is None else str(row["homonym_number"]),
                "Gloss": row.get("gloss", ""),
                "Gloss_Secondary": row.get("gloss_secondary", ""),
                "Usage_Note": row.get("usage_note", ""),
                "POS": row.get("pos", ""),
                "Phonetic": row.get("phonetic", ""),
                "Cross_References": _join(row.get("cross_references")),
                "Examples": _join(row.get("examples")),
                "Example_Glosses": _join(row.get("example_glosses")),
                "Source_Page": row.get("_source_page", ""),
            }
            for key, col in zip(extra_keys, extra_columns):
                tsv_row[col] = extras.get(key, "")
            writer.writerow(tsv_row)

    print(f"Wrote {len(all_rows)} rows → {output}")
    if extra_columns:
        print(f"Extra columns: {', '.join(extra_columns)}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert per-page MDF files to a single combined TSV for RStudio."
    )
    parser.add_argument(
        "--stage2-dir",
        required=True,
        type=Path,
        dest="stage2_dir",
        help="Path to the stage-2 output directory (e.g. outputs/stage-2).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output TSV path. Default: <stage2-dir>/combined.tsv",
    )
    args = parser.parse_args()

    output = args.output or (args.stage2_dir / "combined.tsv")
    sys.exit(convert(args.stage2_dir, output))


if __name__ == "__main__":
    main()
