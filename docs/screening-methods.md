# Screening Methods

## Piotroski F-Score

Reference: https://en.wikipedia.org/wiki/Piotroski_F-Score

A 9-point scoring system evaluating financial health. Each criterion scores 0 or 1. Higher is better (8-9 = strong, 0-2 = weak).

### Profitability (4 points)

| # | Criterion | Implementation |
|---|-----------|----------------|
| 1 | ROA > 0 | `net_income / total_assets > 0` |
| 2 | Operating cash flow > 0 | `total_cash_from_operating_activities > 0` |
| 3 | ROA improving | `ROA(current) > ROA(prior year)` |
| 4 | Cash flow quality | `operating_cash_flow > net_income` |

### Leverage & Liquidity (3 points)

| # | Criterion | Implementation |
|---|-----------|----------------|
| 5 | Decreasing leverage | `long_term_debt(current) < long_term_debt(prior year)` |
| 6 | Improving liquidity | `current_ratio(current) > current_ratio(prior year)` |
| 7 | No dilution | `net_shares_issued <= 0` (issuance + repurchase) |

### Operating efficiency (2 points)

| # | Criterion | Implementation |
|---|-----------|----------------|
| 8 | Improving gross margin | `gross_margin_pct(current) > gross_margin_pct(prior year)` |
| 9 | Improving asset turnover | `revenue / avg_total_assets` improving year-over-year |

### Implementation notes

- Year-over-year comparisons use pandas `groupby('isin').shift(1)`
- Missing data for a criterion scores 0 (conservative)
- Average total assets = `(current + prior) / 2` for asset turnover

## Magic Formula

Reference: https://en.wikipedia.org/wiki/Magic_formula_investing

Ranks stocks by quality (ROIC) and cheapness (earnings yield). The composite score is `ROIC × (1 / EV/EBITDA)`.

### Metrics computed

| Metric | Formula | Purpose |
|--------|---------|---------|
| ROIC | `NOPAT / avg_invested_capital` | Quality: how efficiently capital is deployed |
| EV/EBITDA inverse | `1 / ev_ebitda_ratio` | Cheapness: lower EV/EBITDA = cheaper |
| Shareholder yield (stock) | `(prior_common_stock - common_stock) / prior_common_stock` | Buyback yield |
| Shareholder yield (dividends) | `abs(dividends_paid) / market_cap` | Dividend yield |
| Price to sales | `market_cap / total_revenue` | Revenue valuation |
| Price to cash flow | `market_cap / operating_cash_flow` | Cash flow valuation |
| NCAV ratio | `(current_assets - total_liabilities) / market_cap` | Graham deep value |

### ROIC calculation detail

```
tax_rate = income_tax_expense / income_before_tax
NOPAT = EBIT × (1 - tax_rate)
invested_capital = total_assets - other_assets - current_liabilities - cash
avg_invested_capital = (current + prior) / 2
ROIC = NOPAT / avg_invested_capital
```

### Implementation notes

- Both ROIC and EV/EBITDA inverse negative → score is NULL (avoids false positives from double-negative multiplication)
- EV/EBITDA ratio comes from Yahoo Finance (`enterpriseToEbitda` in ticker.info), not computed from statements
- NCAV ratio > 1.0 means current assets exceed total liabilities by more than market cap (deep value territory)

## Using the screening results

The static site displays all metrics in a Tabulator.js table with column-level filtering. Typical usage:
- Filter `p_score >= 7` for financially healthy stocks
- Sort by `magic_formula_score` descending for quality-at-a-discount
- Filter `ncav_ratio > 0` for Graham net-net candidates
- Combine multiple filters for custom screens
