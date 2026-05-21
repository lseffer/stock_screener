import { useEffect } from 'react';

interface ScreenerInfoProps {
  open: boolean;
  onClose: () => void;
}

export function ScreenerInfo({ open, onClose }: ScreenerInfoProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={onClose}
    >
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="screener-info-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-header">
          <h2 id="screener-info-title">How the screeners work</h2>
          <button
            type="button"
            className="btn btn-ghost modal-close"
            onClick={onClose}
            aria-label="Close"
          >
            ✕
          </button>
        </header>

        <div className="modal-body">
          <p className="modal-intro">
            This screener combines several classic value-investing strategies. Each preset
            highlights a different lens on the same Nordic universe. Scores are recomputed
            from the latest annual filings; <code>null</code> values mean the underlying
            data was missing.
          </p>

          <section className="info-section">
            <h3>Piotroski F-Score</h3>
            <p>
              A 9-point checklist developed by Joseph Piotroski (2000) to separate financially
              strong companies from weak ones. One point is awarded for each of the nine tests
              the company passes — higher is better. Generally <strong>7-9 is strong</strong>,
              <strong> 4-6 is mixed</strong>, and <strong>0-3 is weak</strong>.
            </p>
            <p className="info-subtle">Profitability (4 points):</p>
            <ul>
              <li>Positive return on assets (net income / total assets)</li>
              <li>Positive operating cash flow</li>
              <li>ROA improved year-over-year</li>
              <li>Operating cash flow exceeds net income (earnings quality)</li>
            </ul>
            <p className="info-subtle">Leverage, liquidity &amp; funding (3 points):</p>
            <ul>
              <li>Long-term debt decreased year-over-year</li>
              <li>Current ratio improved year-over-year</li>
              <li>No new shares issued (net buyback or flat)</li>
            </ul>
            <p className="info-subtle">Operating efficiency (2 points):</p>
            <ul>
              <li>Gross margin improved year-over-year</li>
              <li>Asset turnover (revenue / avg total assets) improved year-over-year</li>
            </ul>
          </section>

          <section className="info-section">
            <h3>Magic Formula</h3>
            <p>
              Joel Greenblatt's <em>The Little Book That Beats the Market</em> ranks companies
              by combining <strong>quality</strong> (return on invested capital) with{' '}
              <strong>cheapness</strong> (earnings yield). Higher is better.
            </p>
            <p className="info-formula">
              <code>magic_formula_score = ROIC × (EBITDA / EV)</code>
            </p>
            <ul>
              <li>
                <strong>ROIC</strong> = NOPAT / avg invested capital, where{' '}
                <code>NOPAT = EBIT × (1 − tax rate)</code> and invested capital excludes cash
                and non-operating assets.
              </li>
              <li>
                <strong>EBITDA / EV</strong> is the earnings yield (the inverse of EV/EBITDA).
              </li>
              <li>
                Scores are <code>null</code> when both factors are negative — the multiplication
                would otherwise flip sign and look attractive.
              </li>
            </ul>
          </section>

          <section className="info-section">
            <h3>Value metrics</h3>
            <p>
              Classic valuation ratios shown in the <em>Value</em> preset. These are not
              composite scores — each is a single number you can sort and filter on.
            </p>
            <ul>
              <li>
                <strong>P/E (TTM &amp; fwd)</strong> — price / earnings per share. Lower is
                cheaper, but watch for negative or one-off earnings.
              </li>
              <li>
                <strong>P/Sales</strong> = market cap / total revenue. Useful when earnings are
                noisy.
              </li>
              <li>
                <strong>P/CF</strong> = market cap / cash from operations. Less manipulable
                than P/E.
              </li>
              <li>
                <strong>EV/EBITDA</strong> — enterprise value / EBITDA. Capital-structure
                neutral; comparable across debt levels.
              </li>
              <li>
                <strong>NCAV ratio</strong> = (current assets − total liabilities) / market
                cap. Benjamin Graham's "net-net" metric — values above 1 mean the company
                trades below its liquidation value.
              </li>
              <li>
                <strong>Shareholder yield</strong> = buyback yield + dividend yield.
                <ul>
                  <li>
                    <em>Stock</em> = (prev common stock − current common stock) / prev common
                    stock
                  </li>
                  <li>
                    <em>Dividend</em> = |dividends paid| / market cap
                  </li>
                  <li>
                    <em>Total</em> = stock + dividend, treating missing components as 0 when
                    at least one side is reported.
                  </li>
                </ul>
              </li>
            </ul>
          </section>

          <section className="info-section">
            <h3>Top Picks buckets</h3>
            <p>
              The <em>Top Picks</em> tab groups the top 5 stocks in three styles, applied
              after your current filters:
            </p>
            <ul>
              <li>
                <strong>Quality</strong> — Piotroski F-Score ≥ 7 and ROIC &gt; 10%, ranked by
                ROIC.
              </li>
              <li>
                <strong>Value</strong> — Greenblatt's Magic Formula with F-Score ≥ 5 and
                positive ROIC, ranked by Magic Formula score.
              </li>
              <li>
                <strong>Deep Value</strong> — Graham-style net-nets (NCAV ratio &gt; 1) or
                low-multiple contrarians (P/E ≤ 10, F-Score ≥ 5).
              </li>
            </ul>
          </section>

          <section className="info-section">
            <h3>Rank pills &amp; percentiles</h3>
            <p>
              Coloured pills next to ROIC, Magic Formula, and Shareholder Yield show where the
              value sits in the full Nordic universe (<code>p80</code> = better than 80% of
              stocks). Pills are computed before filtering, so the ranking is stable as you
              adjust filters.
            </p>
          </section>

          <section className="info-section info-caveats">
            <h3>Caveats</h3>
            <ul>
              <li>
                Data comes from Yahoo Finance via <code>yfinance</code>. Field labels and
                coverage vary by ticker — missing values are common for micro-caps.
              </li>
              <li>
                Scores are based on the most recent annual filing only; trailing-twelve-month
                figures come from price/valuation snapshots.
              </li>
              <li>
                These are screening tools, not buy recommendations. Always read the filings
                before acting on a result.
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
