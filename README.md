# Business Lead Scraper

Discovers small businesses in US/UK locations, enriches their public websites with Scrapling, and continuously writes deduplicated leads to Excel.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Commands

```bash
python main.py --country US --city Dallas --category plumber --limit 1000
python main.py --country UK --city London --category cafe --limit 500
python main.py --config config/jobs.json
python main.py --resume
```

## Structure

- `main.py` - CLI entry point
- `lead_scraper/` - discovery, enrichment, cleaning, deduplication, Excel, and checkpoints
- `config/` - optional JSON job configuration
- `tests/` - automated tests
- `output/` - generated workbooks and checkpoints

## Run and resume

Start a CLI or config job. Interrupted jobs can be continued with `python main.py --resume`; progress is saved after each processed result.

Excel files are written to `output/leads.xlsx` by default.
