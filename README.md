![Stock Screener Pipeline](https://github.com/lseffer/stock_screener/actions/workflows/screener.yml/badge.svg)

# Nordic Stock Screener

A stock screener for Nasdaq OMX Nordic exchanges, running as a GitHub Actions job that produces a static website with an accompanying SQLite database.

![](app_screenshot.png?raw=true)

**Screening methods:**

- [Piotroski F-Score](https://en.wikipedia.org/wiki/Piotroski_F-Score) - Financial health evaluation (9 metrics, score 0-9)
- [Magic Formula](https://en.wikipedia.org/wiki/Magic_formula_investing) - Quality + Value investing (ROIC x EV/EBITDA)
- [NCAV](https://www.oldschoolvalue.com/blog/investing-strategy/backtest-graham-nnwc-ncav-screen/) - Net Current Asset Value (Graham deep value)

## Architecture

The screener runs as a scheduled GitHub Actions workflow that:

1. **Scrapes** stock listings from Nasdaq OMX Nordic exchanges
2. **Fetches** financial data (prices, statements) via [yfinance](https://github.com/ranaroussi/yfinance)
3. **Computes** Piotroski F-Score and Magic Formula screening scores
4. **Stores** all data in a SQLite database
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

## Data sources

- **Stock listings**: Scraped from [Nasdaq OMX Nordic](https://www.nasdaqomxnordic.com/) (Copenhagen, Helsinki, Stockholm, First North, Norwegian)
- **Financial data**: [yfinance](https://github.com/ranaroussi/yfinance) (prices, income statements, balance sheets, cash flows)

## Running tests

```bash
python -m unittest discover tests/ -v
```
