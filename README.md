# sunbiz

Convert `.xlsx` files to JSON.

## Structure

```
sunbiz/
├── data/
│   ├── original_files/   # source .xlsx files
│   └── json_files/       # generated .json files (used as scraper input)
├── src/
│   └── converter.py
├── env/            # python 3.11 venv (gitignored)
├── main.py
└── requirements.txt
```

## Setup

```sh
python3.11 -m venv env
./env/bin/pip install -r requirements.txt
```

## Run

Drop `.xlsx` files into `data/original_files/`, then:

```sh
./env/bin/python main.py
```

JSON files land in `data/json_files/`, one per workbook, keyed by sheet name. These JSONs are the input for the scraping step.
