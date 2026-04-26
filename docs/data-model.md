# Data Model

## Tables

### stocks

Master table of tracked stocks. One row per stock.

| Column | Type | Notes |
|--------|------|-------|
| `isin` | String (PK) | Stores yahoo ticker (e.g. `ERIC-B.ST`), not a real ISIN |
| `name` | String | Company long name from yfinance |
| `symbol` | String | Ticker without exchange suffix (e.g. `ERIC-B`) |
| `currency` | String | Trading currency (SEK, DKK, EUR, NOK) |
| `sector` | String | Sector from Yahoo Finance |
| `yahoo_ticker` | String | Full yahoo ticker (same as isin) |
| `dw_created` | DateTime | Row creation timestamp |
| `dw_modified` | DateTime | Last update timestamp |

### prices

Price and valuation snapshot. One row per stock per market date.

| Column | Type | Notes |
|--------|------|-------|
| `isin` | String (PK) | FK to stocks |
| `market_date` | Date (PK) | Date of price observation |
| `price` | Float | Current price (`info['currentPrice']`) |
| `target_median_price` | Float | Analyst median target |
| `recommendation` | Float | Analyst recommendation mean (1=strong buy, 5=sell) |
| `number_of_analyst_opinions` | Float | Count of analyst opinions |
| `ebitda` | Float | Trailing EBITDA |
| `market_cap` | Float | Market capitalization |
| `trailing_pe` | Float | Trailing P/E ratio |
| `forward_pe` | Float | Forward P/E ratio |
| `ev_ebitda_ratio` | Float | Enterprise value to EBITDA |

### income_statements

Annual income statement. One row per stock per fiscal year end.

| Column | Type | Source yfinance labels |
|--------|------|----------------------|
| `isin` | String (PK) | |
| `report_date` | Date (PK) | Column date from `Ticker.income_stmt` |
| `total_revenue` | Float | `Total Revenue` |
| `cost_of_revenue` | Float | `Cost Of Revenue` |
| `gross_profit` | Float | `Gross Profit` |
| `operating_income` | Float | `Operating Income` |
| `ebit` | Float | `EBIT` |
| `interest_expense` | Float | `Interest Expense` |
| `income_before_tax` | Float | `Pretax Income` / `Income Before Tax` |
| `income_tax_expense` | Float | `Tax Provision` / `Income Tax Expense` |
| `net_income` | Float | `Net Income` |
| ... | Float | See `IncomeStatement.FIELD_MAP` for full mapping |

### balance_sheet_statements

Annual balance sheet. One row per stock per fiscal year end.

| Column | Type | Source yfinance labels |
|--------|------|----------------------|
| `isin` | String (PK) | |
| `report_date` | Date (PK) | |
| `cash` | Float | `Cash And Cash Equivalents` |
| `total_current_assets` | Float | `Current Assets` / `Total Current Assets` |
| `total_assets` | Float | `Total Assets` |
| `total_current_liabilities` | Float | `Current Liabilities` |
| `long_term_debt` | Float | `Long Term Debt` / `Long Term Debt And Capital Lease Obligation` |
| `total_liab` | Float | `Total Liabilities Net Minority Interest` |
| `total_stockholder_equity` | Float | `Stockholders Equity` |
| ... | Float | See `BalanceSheetStatement.FIELD_MAP` for full mapping |

### cash_flow_statements

Annual cash flow statement. One row per stock per fiscal year end.

| Column | Type | Source yfinance labels |
|--------|------|----------------------|
| `isin` | String (PK) | |
| `report_date` | Date (PK) | |
| `net_income` | Float | `Net Income` |
| `total_cash_from_operating_activities` | Float | `Operating Cash Flow` |
| `capital_expenditures` | Float | `Capital Expenditure` |
| `dividends_paid` | Float | `Common Stock Dividend Paid` |
| `repurchase_of_stock` | Float | `Repurchase Of Capital Stock` |
| `issuance_of_stock` | Float | `Common Stock Issuance` |
| ... | Float | See `CashFlowStatement.FIELD_MAP` for full mapping |

## yfinance field mapping

Each financial statement model has a `FIELD_MAP` class attribute that maps yfinance DataFrame row labels to our column names. yfinance labels are inconsistent across stocks and library versions, so maps include multiple aliases for the same field. First match wins (via `if our_field not in record` guard in `from_yfinance_column()`).

Example from `IncomeStatement.FIELD_MAP`:
```python
{
    'Pretax Income': 'income_before_tax',
    'Income Before Tax': 'income_before_tax',  # alias
    'Tax Provision': 'income_tax_expense',
    'Income Tax Expense': 'income_tax_expense',  # alias
}
```

## Screening output columns

The final JSON output (`data.json`) contains these fields per stock:

| Column | Source | Description |
|--------|--------|-------------|
| `isin` | stocks | Yahoo ticker as identifier |
| `company_name` | stocks | Company name |
| `symbol` | stocks | Ticker symbol |
| `currency` | stocks | Trading currency |
| `sector` | stocks | Industry sector |
| `yahoo_ticker` | stocks | Yahoo Finance ticker |
| `report_date` | financials | Fiscal year end date |
| `market_date` | prices | Price observation date |
| `p_score` | scoring | Piotroski F-Score (0-9) |
| `roic` | scoring | Return on invested capital |
| `ev_ebitda_ratio_inv` | scoring | 1 / EV/EBITDA |
| `shareholder_yield_stock` | scoring | Buyback yield |
| `shareholder_yield_dividends` | scoring | Dividend yield |
| `price_to_sales` | scoring | Market cap / revenue |
| `price_to_cash_flow` | scoring | Market cap / operating cash flow |
| `ncav_ratio` | scoring | (Current assets - total liabilities) / market cap |
| `price` | prices | Current stock price |
| `target_median_price` | prices | Analyst target price |
| `number_of_analyst_opinions` | prices | Analyst coverage count |
| `ebitda` | prices | Trailing EBITDA |
| `market_cap` | prices | Market capitalization |
| `trailing_pe` | prices | Trailing P/E |
| `forward_pe` | prices | Forward P/E |
| `ev_ebitda_ratio` | prices | EV/EBITDA |
| `magic_formula_score` | scoring | ROIC × (1/EV/EBITDA) composite |
