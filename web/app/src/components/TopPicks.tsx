import type { Stock } from '../types';
import { computeTopPicks, type PickBucket, type PickMetric } from '../topPicks';
import { fmtDecimal, fmtPercent } from '../format';

interface TopPicksProps {
  rows: Stock[];
}

function formatMetric(stock: Stock, metric: PickMetric): string {
  const raw = stock[metric.key];
  const value = typeof raw === 'number' ? raw : null;
  if (metric.type === 'pct') return fmtPercent(value);
  return fmtDecimal(value);
}

function pillTone(score: number | null | undefined): 'good' | 'mid' | 'bad' | null {
  if (typeof score !== 'number') return null;
  if (score >= 7) return 'good';
  if (score >= 5) return 'mid';
  return 'bad';
}

function PickRow({ stock, rank, primary, secondary }: {
  stock: Stock;
  rank: number;
  primary: PickMetric;
  secondary: PickMetric;
}) {
  const name = stock.company_name ?? stock.isin;
  const symbol = stock.symbol ?? stock.isin;
  const href = `https://www.google.com/search?q=${encodeURIComponent(`${name} ${symbol} stock`)}`;

  const isPiotroskiSecondary = secondary.key === 'p_score';
  const secondaryValue = stock[secondary.key];
  const tone = isPiotroskiSecondary ? pillTone(secondaryValue as number | null) : null;

  return (
    <li className="pick-item">
      <span className="pick-rank">{rank}</span>
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        className="pick-link"
      >
        <span className="pick-name">{name}</span>
        <span className="pick-sub">
          {symbol}
          {stock.sector ? <span className="pick-sector"> · {stock.sector}</span> : null}
        </span>
      </a>
      <span className="pick-metrics">
        <span className="pick-primary">{formatMetric(stock, primary)}</span>
        <span className="pick-secondary">
          {secondary.label}:{' '}
          {tone ? (
            <span className={`pill pill-${tone}`}>{secondaryValue as number}</span>
          ) : (
            formatMetric(stock, secondary)
          )}
        </span>
      </span>
    </li>
  );
}

function Bucket({ bucket }: { bucket: PickBucket }) {
  return (
    <section className="pick-bucket" aria-labelledby={`bucket-${bucket.id}`}>
      <header className="pick-bucket-header">
        <h2 id={`bucket-${bucket.id}`}>{bucket.title}</h2>
        <p>{bucket.description}</p>
        <span className="pick-bucket-metric">Ranked by {bucket.primary.label}</span>
      </header>
      {bucket.picks.length === 0 ? (
        <p className="pick-empty">No stocks meet these criteria in the current filter.</p>
      ) : (
        <ol className="pick-list">
          {bucket.picks.map((stock, i) => (
            <PickRow
              key={stock.isin}
              stock={stock}
              rank={i + 1}
              primary={bucket.primary}
              secondary={bucket.secondary}
            />
          ))}
        </ol>
      )}
    </section>
  );
}

export function TopPicks({ rows }: TopPicksProps) {
  const buckets = computeTopPicks(rows);
  return (
    <div className="top-picks-grid">
      {buckets.map((b) => (
        <Bucket key={b.id} bucket={b} />
      ))}
    </div>
  );
}
