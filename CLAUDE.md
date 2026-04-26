# Nordic Stock Screener

## Quick reference

- **Language**: Python 3.12, no type checker currently enforced
- **Dependencies**: `yfinance`, `sqlalchemy`, `pandas`, `requests` (see `requirements.txt`)
- **Database**: SQLite (`stocks.db`), created automatically on first run
- **Entry point**: `python generate_site.py`
- **Tests**: `python -m unittest discover tests/ -v`
- **Output**: `_site/` directory (static HTML + JSON + SQLite db)

## What this project does

Screens Nordic stocks (Stockholm, Copenhagen, Helsinki, Oslo) using Piotroski F-Score and Magic Formula investing strategies. Runs as a weekly GitHub Actions job that fetches data via yfinance, computes scores, and deploys a static site to GitHub Pages.

## Project structure

```
generate_site.py          Entry point. Orchestrates: init DB → run ETL → compute scores → generate site
scoring.py                Piotroski F-Score and Magic Formula computation (pandas)
utils/
  config.py               SQLite engine, Session factory, logger, constants (DB_PATH, OUTPUT_DIR)
  etl_base.py             Abstract ETL base with load_record() and load_records()
  queries.py              Incremental queries: which stocks need price/financial updates
  stock_info_etl.py       Stock discovery via yfinance screener API (EquityQuery by exchange)
  stock_valuation_etl.py  Price/valuation data via yfinance Ticker.info
  stock_financial_statements_etl.py  Financial statements via yfinance Ticker.income_stmt/balance_sheet/cashflow
  models/
    base.py               SQLAlchemy DeclarativeBase
    stocks.py             Stock master table (PK: isin, which stores the yahoo ticker)
    prices.py             Current price/valuation data
    income_statements.py  Income statement data (with FIELD_MAP for yfinance label mapping)
    balance_sheet_statements.py
    cash_flow_statements.py
web/static/               Source CSS, JS, images (copied to _site/ during generation)
.github/workflows/screener.yml  Weekly GitHub Actions pipeline
```

## Key design decisions

- **isin column stores yahoo ticker** (e.g. `ERIC-B.ST`), not a real ISIN. The old Nasdaq Nordic scraper that provided ISINs is dead. The yahoo ticker is the natural key since all data fetching uses it.
- **Incremental ETL**: Prices skip stocks updated within 5 days. Financials skip stocks with data for the current fiscal year. The SQLite DB is restored from the previous run's artifact.
- **Robustness**: Each ETL phase is wrapped in try/except. Prices commit per-stock. Financial statements commit per-stock batch. Partial failures still produce output. Workflow uses `if: always()` on upload steps.
- **Scoring in Python**: Piotroski and Magic Formula scores are computed in pandas, replacing the old PostgreSQL materialized views. See `scoring.py`.
- **yfinance field mapping**: Financial statement models have a `FIELD_MAP` dict that maps yfinance DataFrame row labels to our column names. yfinance labels vary across stocks/versions, so maps include multiple aliases.

## Running locally

```bash
pip install -r requirements.txt
python generate_site.py              # full pipeline
python generate_site.py --skip-etl   # regenerate site from existing DB
python generate_site.py --etl-only   # just populate DB
```

Environment variables (all optional):
- `STOCK_SCREENER_DB` — SQLite path (default: `stocks.db`)
- `STOCK_SCREENER_OUTPUT` — site output dir (default: `_site`)

## Common tasks

**Add a new exchange**: Add its Yahoo Finance exchange code to `NORDIC_EXCHANGES` in `utils/stock_info_etl.py`.

**Add a new financial metric**: Add the column to the relevant model, add yfinance label(s) to its `FIELD_MAP`, and update `scoring.py` if it affects screening.

**Change screening logic**: Edit `compute_piotroski_scores()` or `compute_magic_formula_scores()` in `scoring.py`.

**Debug a specific stock**: `python -c "import yfinance as yf; t = yf.Ticker('ERIC-B.ST'); print(t.info)"` to check what yfinance returns.
