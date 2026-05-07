from pathlib import Path

from src.pipeline import run_sync

ROOT = Path(__file__).parent

run_sync(
    source_json=ROOT / "data" / "json_files" / "Publix 3.json",
    email_file=ROOT / "emails" / "email_2026_q1.txt",
    output_json=ROOT / "data" / "output_json" / "Publix 3.json",
    output_xlsx=ROOT / "data" / "output_xlsx" / "Publix 3.xlsx",
    search_field="Recorded Owner Name",
    concurrency=5,
    retries=2,
)
