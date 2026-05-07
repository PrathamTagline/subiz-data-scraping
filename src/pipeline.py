import asyncio
import json
import time
from pathlib import Path

from src.email_lookup import build_email_map
from src.scraper import scrape_terms
from src.xlsx_writer import dict_to_xlsx


def _str_term(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


async def run(
    source_json: Path,
    email_file: Path,
    output_json: Path,
    output_xlsx: Path,
    search_field: str = "Recorded Owner Name",
    concurrency: int = 5,
    retries: int = 2,
):
    if not source_json.exists():
        raise SystemExit(f"missing input: {source_json}")
    if not email_file.exists():
        raise SystemExit(f"missing email file: {email_file}")

    with source_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    sheet_name = next(iter(data))
    rows = data[sheet_name]
    print(f"Loaded {len(rows)} rows from {source_json.name} (sheet: {sheet_name!r})")

    targets = [(i, _str_term(r.get(search_field))) for i, r in enumerate(rows)]
    valid = [(i, t) for i, t in targets if t]
    print(f"{len(valid)} rows have a non-empty {search_field!r}")

    terms = [t for _, t in valid]
    t0 = time.time()
    results = await scrape_terms(terms, concurrency=concurrency, retries=retries)
    print(f"Scraping finished in {time.time() - t0:.1f}s")

    for (idx, _), result in zip(valid, results):
        row = rows[idx]
        if isinstance(result, dict) and result.get("document_number"):
            row["Document Number"] = result["document_number"]
            row["Matched Corporate Name"] = result.get("matched_corporate_name")
            row["Sunbiz Status"] = result.get("status")
        else:
            row["Document Number"] = None
            row["Matched Corporate Name"] = None
            row["Sunbiz Status"] = None
            if isinstance(result, dict) and result.get("error"):
                row["Sunbiz Error"] = result["error"]

    doc_numbers = [r.get("Document Number") for r in rows if r.get("Document Number")]
    print(f"Looking up emails for {len(doc_numbers)} document numbers...")
    t0 = time.time()
    email_map = build_email_map(email_file, doc_numbers)
    print(f"Found {len(email_map)} email matches in {time.time() - t0:.1f}s")

    for r in rows:
        doc = r.get("Document Number")
        r["Email"] = email_map.get(doc) if doc else None

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {output_json}")

    dict_to_xlsx(data, output_xlsx)
    print(f"Wrote {output_xlsx}")

    matched = sum(1 for r in rows if r.get("Document Number"))
    emailed = sum(1 for r in rows if r.get("Email"))
    print(
        f"Summary: {matched}/{len(rows)} doc-numbers found, "
        f"{emailed}/{len(rows)} emails attached"
    )


def run_sync(**kwargs):
    asyncio.run(run(**kwargs))
