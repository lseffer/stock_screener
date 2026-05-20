# Nordic Stock Screener

## Quick reference

- **Language**: Python 3.12, no type checker currently enforced
- **Dependencies**: `yfinance`, `sqlalchemy`, `polars`, `pandas` (yfinance dep), `requests` (see `requirements.txt`)
- **Database**: SQLite (`stocks.db`), created automatically on first run
- **Entry point**: `python generate_site.py` (auto-builds the frontend if `web/app/dist` is missing)
- **Frontend**: React + TypeScript + TanStack Table (`web/app/`). Build with `npm ci && npm run build` inside `web/app/`.
- **Tests**: `python -m unittest discover tests/ -v`
- **Output**: `_site/` directory (built frontend + JSON data + SQLite db)

## What this project does

Screens Nordic stocks (Stockholm, Copenhagen, Helsinki, Oslo) using Piotroski F-Score and Magic Formula investing strategies. Runs as a weekly GitHub Actions job that fetches data via yfinance, computes scores, and deploys a static site to GitHub Pages.

## Project structure

```
generate_site.py          Entry point. Orchestrates: init DB → run ETL → compute scores → generate site
scoring.py                Piotroski F-Score and Magic Formula computation (polars)
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
web/app/                  Vite + React + TypeScript frontend (TanStack Table + Virtual)
  src/
    App.tsx               Top-level component, owns filter/sort/preset state, fetches data.json
    columns.tsx           Column definitions, presets (Overview/Piotroski/Magic Formula/Value/All)
    components/
      StockTable.tsx      Desktop virtualized table (TanStack React Table + React Virtual)
      StockCards.tsx      Mobile virtualized card list with expand-for-details
      Toolbar.tsx         Search, preset chips, filter panel, CSV export button
      ColumnPicker.tsx    Desktop column visibility toggle (inside filter panel)
    csv.ts                Client-side CSV export of the currently-sorted/filtered rows
    format.ts             Intl-based number/currency/percent formatters
    hooks.ts              useMediaQuery, useDebounced
    styles.css            Single CSS file with light/dark theme via prefers-color-scheme
  public/favicon.png      Favicon copied verbatim into dist/
  dist/                   Build output (gitignored). Copied into _site/ by generate_site.py.
.github/workflows/screener.yml  Weekly GitHub Actions pipeline (Python + Node build)
```

## Key design decisions

- **isin column stores yahoo ticker** (e.g. `ERIC-B.ST`), not a real ISIN. The old Nasdaq Nordic scraper that provided ISINs is dead. The yahoo ticker is the natural key since all data fetching uses it.
- **Incremental ETL**: Prices skip stocks updated within 5 days. Financials skip stocks with data for the current fiscal year. The SQLite DB is restored from the previous run's artifact.
- **Robustness**: Each ETL phase is wrapped in try/except. Prices commit per-stock. Financial statements commit per-stock batch. Partial failures still produce output. Workflow uses `if: always()` on upload steps.
- **Scoring in polars**: Piotroski and Magic Formula scores are computed in polars using expression-based column operations, replacing the old pandas `apply()` approach. See `scoring.py`. Pandas is still a dependency because yfinance returns pandas DataFrames in the ETL layer.
- **yfinance field mapping**: Financial statement models have a `FIELD_MAP` dict that maps yfinance DataFrame row labels to our column names. yfinance labels vary across stocks/versions, so maps include multiple aliases.
- **Frontend data contract**: `_site/data.json` is `{ generated_at: string, rows: Stock[] }`. Adding a metric means adding it to the polars output in `scoring.py`, the `Stock` TypeScript interface in `web/app/src/types.ts`, and (usually) a new column entry in `web/app/src/columns.tsx`.

## Running locally

```bash
pip install -r requirements.txt
(cd web/app && npm ci && npm run build)   # one-time / when frontend changes
python generate_site.py                   # full pipeline
python generate_site.py --skip-etl        # regenerate site from existing DB
python generate_site.py --etl-only        # just populate DB

# Frontend dev with live reload — run `python generate_site.py --skip-etl`
# first to produce _site/data.json, then copy it into web/app/public/data.json
# and start the dev server:
cp _site/data.json web/app/public/data.json && (cd web/app && npm run dev)
```

Environment variables (all optional):
- `STOCK_SCREENER_DB` — SQLite path (default: `stocks.db`)
- `STOCK_SCREENER_OUTPUT` — site output dir (default: `_site`)

## Common tasks

**Add a new exchange**: Add its Yahoo Finance exchange code to `NORDIC_EXCHANGES` in `utils/stock_info_etl.py`.

**Add a new financial metric**: Add the column to the relevant model, add yfinance label(s) to its `FIELD_MAP`, and update `scoring.py` if it affects screening.

**Change screening logic**: Edit `compute_piotroski_scores()` or `compute_magic_formula_scores()` in `scoring.py`.

**Debug a specific stock**: `python -c "import yfinance as yf; t = yf.Ticker('ERIC-B.ST'); print(t.info)"` to check what yfinance returns.
