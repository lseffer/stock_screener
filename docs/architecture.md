# Architecture

## Overview

The stock screener is a batch pipeline that runs weekly in GitHub Actions. It has no running services — it fetches data, computes scores, and produces static output.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (weekly)                       │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────────┐  │
│  │ Restore DB   │──▶│ Run ETL      │──▶│ Generate site       │  │
│  │ (artifact)   │   │ pipeline     │   │ (HTML + JSON + DB)  │  │
│  └──────────────┘   └──────┬───────┘   └─────────┬──────────┘  │
│                            │                     │              │
│                     ┌──────┴───────┐      ┌──────┴──────┐      │
│                     │   SQLite     │      │  _site/     │      │
│                     │  stocks.db   │      │  ├ index.html│      │
│                     └──────────────┘      │  ├ data.json │      │
│                                           │  ├ stocks.db │      │
│                                           │  └ css/js/   │      │
│                                           └─────────────┘      │
│                                                 │              │
│                                          ┌──────┴──────┐      │
│                                          │ GitHub Pages │      │
│                                          └─────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline stages

### 1. Stock discovery (`StockInfoETL`)

Uses `yfinance.screen()` with `EquityQuery('is-in', ['exchange', code])` for each Nordic exchange (STO, CPH, HEL, OSL). Paginates in batches of 250. Each stock is committed to the DB immediately after fetch.

**Source**: Yahoo Finance equity screener API (via yfinance)
**Output**: `stocks` table

### 2. Price/valuation data (`StockValuationETL`)

For each stock needing a price update (not updated in last 5 days), fetches `yf.Ticker(symbol).info` and extracts: current price, target price, PE ratios, market cap, EBITDA, EV/EBITDA, analyst opinions.

**Source**: Yahoo Finance quote data (via yfinance)
**Output**: `prices` table
**Incremental**: Skips stocks with a `prices` record within the last 5 days.

### 3. Financial statements (`StockFinancialStatementsETL`)

For each stock missing current-year financials, fetches annual income statement, balance sheet, and cash flow via `yf.Ticker(symbol).income_stmt`, `.balance_sheet`, `.cashflow`. These return pandas DataFrames with dates as columns and line items as rows. The `FIELD_MAP` on each model class handles label mapping.

**Source**: Yahoo Finance fundamentals (via yfinance)
**Output**: `income_statements`, `balance_sheet_statements`, `cash_flow_statements` tables
**Incremental**: Skips stocks that already have data for the last fiscal year (fundamentals change quarterly at most).

### 4. Scoring (`scoring.py`)

Loads all financial data into pandas, computes:
- **Piotroski F-Score** (9 binary criteria, summed to 0-9): profitability, leverage, liquidity, operating efficiency signals
- **Magic Formula**: ROIC × (1/EV/EBITDA), plus valuation ratios (P/S, P/CF, NCAV, shareholder yield)

Year-over-year comparisons use `groupby('isin').shift(1)` for lagged values.

### 5. Site generation

Filters scores to the last fiscal year, serializes to JSON, generates `index.html` with Tabulator.js table, copies static assets and SQLite DB to `_site/`.

## Database schema

All tables use `isin` (which stores the yahoo ticker, e.g. `ERIC-B.ST`) as the primary key or part of a composite key.

| Table | Primary Key | Description |
|-------|-------------|-------------|
| `stocks` | `isin` | Stock master data (name, symbol, currency, sector) |
| `prices` | `(isin, market_date)` | Price and valuation snapshot |
| `income_statements` | `(isin, report_date)` | Annual income statement |
| `balance_sheet_statements` | `(isin, report_date)` | Annual balance sheet |
| `cash_flow_statements` | `(isin, report_date)` | Annual cash flow statement |

## Robustness model

- Each ETL phase is wrapped in try/except — a failure in stock discovery doesn't block price fetching
- Prices are committed per-stock; financial statements per-stock-batch
- The workflow uploads the database artifact with `if: always()` — even a half-finished run preserves its data for next time
- Incremental queries ensure the next run picks up where the last one left off
- `session.merge()` provides upsert semantics — re-running is safe

## Data flow for a single stock

```
yfinance screener → Stock record → stocks table
                                        │
                     yf.Ticker.info ─────┼──→ Price record → prices table
                                        │
                     yf.Ticker.income_stmt ──→ IncomeStatement records ──┐
                     yf.Ticker.balance_sheet ─→ BalanceSheet records ────┼──→ scoring.py
                     yf.Ticker.cashflow ──────→ CashFlow records ───────┘        │
                                                                          screen_results
                                                                                │
                                                                          data.json → index.html
```
