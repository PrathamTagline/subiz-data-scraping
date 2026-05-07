from pathlib import Path

from src.pipeline import run_sync

ROOT = Path(__file__).parent

run_sync(
    source_json=ROOT / "data" / "json_files" / "Walmart list.json",
    email_file=ROOT / "emails" / "email_2026_q1.txt",
    output_json=ROOT / "data" / "output_json" / "Walmart list.json",
    output_xlsx=ROOT / "data" / "output_xlsx" / "Walmart list.xlsx",
    search_field="Recorded Owner Name",
    concurrency=5,
    retries=2,
)
