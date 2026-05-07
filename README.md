# subiz-data-scraping

Pipeline that takes property-owner spreadsheets, looks up each owner on
[sunbiz.org](https://search.sunbiz.org/Inquiry/CorporationSearch/ByName) to
find the active Florida corporate filing, attaches contact emails from a
local doc-number → email file, and writes the enriched data back as both
JSON and XLSX.

## Pipeline

```
data/original_files/*.xlsx
            │
            │  main.py  (openpyxl)
            ▼
data/json_files/*.json
            │
            │  scrape_<list>.py  (Playwright + asyncio)
            │  └─ for each row: search "Recorded Owner Name" on sunbiz,
            │     pick the first row whose status is "Active",
            │     record the Document Number
            │
            │  email_lookup.py  (streams emails/email_2026_q1.txt)
            │  └─ map Document Number → email
            ▼
data/output_json/*.json
data/output_xlsx/*.xlsx
```

## Project structure

```
.
├── data/
│   ├── original_files/   # source .xlsx files (gitignored)
│   ├── json_files/       # output of main.py (gitignored)
│   ├── output_json/      # enriched JSON (gitignored)
│   └── output_xlsx/      # enriched XLSX (gitignored)
├── emails/
│   └── email_2026_q1.txt # doc# → email csv-style file (gitignored, ~396MB)
├── src/
│   ├── converter.py      # xlsx → dict
│   ├── scraper.py        # async Playwright sunbiz scraper
│   ├── email_lookup.py   # streams email file, builds lookup dict
│   ├── pipeline.py       # orchestrates scrape + email enrichment
│   └── xlsx_writer.py    # dict → xlsx
├── env/                  # python 3.11 venv (gitignored)
├── main.py               # xlsx → json for every file in data/original_files/
├── scrape_publix1.py     # per-list scraper wrappers
├── scrape_publix2.py
├── scrape_publix3.py
├── scrape_aldi.py
├── scrape_walmart.py
└── requirements.txt
```

## Setup

Requires Python 3.11.

```sh
python3.11 -m venv env
./env/bin/pip install -r requirements.txt
./env/bin/playwright install chromium
```

The scraper uses a real Chromium browser via Playwright — Cloudflare blocks
plain HTTP clients on sunbiz.

## Usage

### 1. Convert all xlsx to json

Drop `.xlsx` files into `data/original_files/`, then:

```sh
./env/bin/python main.py
```

JSON files land in `data/json_files/`, one per workbook, keyed by sheet
name.

### 2. Scrape sunbiz + attach emails

Place your email mapping file at `emails/email_2026_q1.txt` (format:
`<DocumentNumber>,<email>` per line — the script streams it, so size is
not a concern).

Run the wrapper for the list you want:

```sh
./env/bin/python scrape_publix1.py
./env/bin/python scrape_publix2.py
./env/bin/python scrape_publix3.py
./env/bin/python scrape_aldi.py
./env/bin/python scrape_walmart.py
```

Or run all of them in sequence:

```sh
for s in scrape_publix1 scrape_publix2 scrape_publix3 scrape_aldi scrape_walmart; do
  ./env/bin/python $s.py
done
```

Each run prints live progress and ends with a summary like:

```
Summary: 312/325 doc-numbers found, 47/325 emails attached
```

Outputs:
- `data/output_json/<list>.json` — original rows plus `Document Number`,
  `Matched Corporate Name`, `Sunbiz Status`, `Email`
- `data/output_xlsx/<list>.xlsx` — same data as a spreadsheet

### Tunables

Open any `scrape_*.py` to adjust:

| field         | default | meaning                                           |
| ------------- | ------- | ------------------------------------------------- |
| `concurrency` | 5       | parallel browser contexts hitting sunbiz          |
| `retries`     | 2       | per-row retry count on transient errors           |
| `search_field`| `Recorded Owner Name` | column in the source JSON used as the query |

Bump concurrency to 8–10 to go faster; drop it if you start seeing
Cloudflare blocks.

## Adding a new list

1. Drop `<New List>.xlsx` into `data/original_files/`.
2. Run `./env/bin/python main.py` to convert it.
3. Copy any `scrape_*.py`, change the four paths and the list name.

That's it — everything shared lives in `src/pipeline.py`.

## Notes

- The scraper picks the first row in sunbiz results whose status is
  `Active`. There is no fuzzy name verification — if the owner name in
  the source spreadsheet matches multiple unrelated active corporations,
  the alphabetically-first one wins.
- The email file is read once per script run; only doc numbers present
  in the current list are kept in memory.
- `data/`, `emails/`, and `env/` are gitignored — the repository ships
  the code only.
