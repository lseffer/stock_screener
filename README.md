![Stock Screener Pipeline](https://github.com/lseffer/stock_screener/actions/workflows/screener.yml/badge.svg)

# Nordic Stock Screener

A stock screener for Nordic exchanges (Stockholm, Copenhagen, Helsinki, Oslo), running as a weekly GitHub Actions job that produces a static website with an accompanying SQLite database.

**Live site: [lseffer.github.io/stock_screener](https://lseffer.github.io/stock_screener/)**

**Tech stack:** Python 3.12 | SQLite | Polars | React + TypeScript + TanStack Table | Vite

**Screening methods:**

- [Piotroski F-Score](https://en.wikipedia.org/wiki/Piotroski_F-Score) - Financial health evaluation (9 metrics, score 0-9)
- [Magic Formula](https://en.wikipedia.org/wiki/Magic_formula_investing) - Quality + Value investing (ROIC x EV/EBITDA)
- [NCAV](https://www.oldschoolvalue.com/blog/investing-strategy/backtest-graham-nnwc-ncav-screen/) - Net Current Asset Value (Graham deep value)

## Architecture

The screener runs as a scheduled GitHub Actions workflow that:

1. **Discovers** stock listings from Nordic exchanges via the [yfinance](https://github.com/ranaroussi/yfinance) screener API
2. **Fetches** financial data (prices, income statements, balance sheets, cash flows) via yfinance
3. **Computes** Piotroski F-Score and Magic Formula screening scores using Polars
4. **Stores** all data in a SQLite database (incremental — only updates stale records)
5. **Generates** a static website with the screening results
6. **Deploys** to GitHub Pages

The workflow runs weekly (Saturday 06:00 UTC) and can be triggered manually.

## Local development

```bash
pip install -r requirements.txt

# Run full pipeline (ETL + site generation)
python generate_site.py

# Skip ETL, just regenerate site from existing database
python generate_site.py --skip-etl

# Run ETL only (populate database, no site)
python generate_site.py --etl-only
```

Output:
- `_site/` - Static website (HTML, CSS, JS, data.json)
- `_site/stocks.db` - SQLite database with all raw + computed data
- `stocks.db` - Working database

### Frontend development

```bash
# Build the frontend (one-time or when frontend changes)
(cd web/app && npm ci && npm run build)

# For live reload during frontend development:
# 1. Generate data first
python generate_site.py --skip-etl

# 2. Copy data into the dev server's public dir and start Vite
cp _site/data.json web/app/public/data.json
cd web/app && npm run dev
```

### Environment variables

All optional:
- `STOCK_SCREENER_DB` — SQLite path (default: `stocks.db`)
- `STOCK_SCREENER_OUTPUT` — site output dir (default: `_site`)

## Data sources

All data is fetched via [yfinance](https://github.com/ranaroussi/yfinance):
- **Stock listings**: Discovered using the yfinance screener API (`EquityQuery` by exchange) for Stockholm, Copenhagen, Helsinki, and Oslo
- **Financial data**: Prices, income statements, balance sheets, and cash flows via `yfinance.Ticker`

## Running tests

```bash
python -m unittest discover tests/ -v
```
