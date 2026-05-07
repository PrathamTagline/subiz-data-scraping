from pathlib import Path

from src.converter import convert_directory, workbook_to_dict

ROOT = Path(__file__).parent
INPUT_DIR = ROOT / "data" / "original_files"
OUTPUT_DIR = ROOT / "data" / "json_files"


def main():
    if not INPUT_DIR.exists():
        raise SystemExit(f"input dir not found: {INPUT_DIR}")

    results = convert_directory(INPUT_DIR, OUTPUT_DIR)
    if not results:
        print(f"no .xlsx files found in {INPUT_DIR}")
        return

    for src, out in results:
        data = workbook_to_dict(src)
        total = sum(len(rows) for rows in data.values())
        print(f"{src.name} -> {out.relative_to(ROOT)} ({len(data)} sheet(s), {total} row(s))")


if __name__ == "__main__":
    main()
