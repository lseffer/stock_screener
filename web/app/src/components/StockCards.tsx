import { useRef, useState } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Stock } from '../types';
import { fmtCompact, fmtDecimal, fmtPercent, fmtPrice, fmtText } from '../format';

interface StockCardsProps {
  rows: Stock[];
  primaryMetric: { key: keyof Stock; label: string; type: 'pct' | 'num' | 'score' };
}

const CARD_HEIGHT = 132;
const EXPANDED_EXTRA = 220;

function formatMetric(value: unknown, type: 'pct' | 'num' | 'score'): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '–';
  if (type === 'pct') return fmtPercent(value);
  if (type === 'score') return String(value);
  return fmtDecimal(value);
}

function PScorePill({ value }: { value: number | null }) {
  if (value === null || value === undefined) return <span className="muted">–</span>;
  const tone = value >= 7 ? 'good' : value >= 5 ? 'mid' : 'bad';
  return <span className={`pill pill-${tone}`}>P {value}</span>;
}

export function StockCards({ rows, primaryMetric }: StockCardsProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: (i) =>
      expanded.has(rows[i]!.isin) ? CARD_HEIGHT + EXPANDED_EXTRA : CARD_HEIGHT,
    overscan: 6,
  });

  const toggle = (isin: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(isin)) next.delete(isin);
      else next.add(isin);
      return next;
    });
    requestAnimationFrame(() => virtualizer.measure());
  };

  if (rows.length === 0) {
    return <div className="empty-state">No stocks match the current filters.</div>;
  }

  return (
    <div className="card-scroller" ref={containerRef}>
      <div
        style={{
          height: virtualizer.getTotalSize(),
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((vi) => {
          const stock = rows[vi.index]!;
          const isOpen = expanded.has(stock.isin);
          return (
            <div
              key={stock.isin}
              data-index={vi.index}
              ref={virtualizer.measureElement}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                transform: `translateY(${vi.start}px)`,
                padding: '6px 12px',
              }}
            >
              <article className={`card ${isOpen ? 'card-open' : ''}`}>
                <button
                  className="card-header"
                  onClick={() => toggle(stock.isin)}
                  aria-expanded={isOpen}
                >
                  <div className="card-title-block">
                    <div className="card-title">
                      {fmtText(stock.company_name ?? stock.isin)}
                    </div>
                    <div className="card-sub">
                      <span>{fmtText(stock.symbol)}</span>
                      {stock.sector && <span className="dot">·</span>}
                      <span>{fmtText(stock.sector)}</span>
                    </div>
                  </div>
                  <div className="card-primary">
                    <PScorePill value={stock.p_score} />
                    <div className="card-primary-metric">
                      <span className="metric-label">{primaryMetric.label}</span>
                      <span className="metric-value">
                        {formatMetric(stock[primaryMetric.key], primaryMetric.type)}
                      </span>
                    </div>
                  </div>
                </button>

                <div className="card-stats">
                  <Stat label="Price" value={fmtPrice(stock.price, stock.currency)} />
                  <Stat label="ROIC" value={fmtPercent(stock.roic)} />
                  <Stat label="EV/EBITDA" value={fmtDecimal(stock.ev_ebitda_ratio)} />
                  <Stat label="Mkt Cap" value={fmtCompact(stock.market_cap)} />
                </div>

                {isOpen && (
                  <div className="card-detail">
                    <div className="card-stats">
                      <Stat label="Magic Formula" value={fmtDecimal(stock.magic_formula_score)} />
                      <Stat label="P/E (TTM)" value={fmtDecimal(stock.trailing_pe)} />
                      <Stat label="P/E (fwd)" value={fmtDecimal(stock.forward_pe)} />
                      <Stat label="P/Sales" value={fmtDecimal(stock.price_to_sales)} />
                      <Stat label="P/CF" value={fmtDecimal(stock.price_to_cash_flow)} />
                      <Stat label="NCAV" value={fmtDecimal(stock.ncav_ratio)} />
                      <Stat label="SH Yield (stock)" value={fmtPercent(stock.shareholder_yield_stock)} />
                      <Stat label="Div Yield" value={fmtPercent(stock.shareholder_yield_dividends)} />
                      <Stat label="EBITDA" value={fmtCompact(stock.ebitda)} />
                      <Stat label="Target" value={fmtPrice(stock.target_median_price, stock.currency)} />
                      <Stat label="Analysts" value={fmtDecimal(stock.number_of_analyst_opinions)} />
                      <Stat label="Report" value={fmtText(stock.report_date)} />
                    </div>
                    <a
                      className="card-link"
                      href={`https://www.google.com/search?q=${encodeURIComponent(
                        `${stock.company_name ?? ''} ${stock.symbol ?? ''} stock`,
                      )}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Search on Google ↗
                    </a>
                  </div>
                )}
              </article>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}
