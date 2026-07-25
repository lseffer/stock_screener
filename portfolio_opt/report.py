"""Self-contained HTML report for the portfolio optimization.

Pure string building: one <style> block, an inline SVG chart, zero JavaScript
and zero external requests, so the report renders fully offline and never
leaks holdings data anywhere.
"""
import html
from typing import List, Sequence, Tuple

import numpy as np

from portfolio_opt.optimizer import OptimizationResult

SVG_W, SVG_H = 760, 480
MARGIN_L, MARGIN_R, MARGIN_T, MARGIN_B = 64, 20, 20, 46

CSS = """
:root {
  color-scheme: light dark;
  --bg: #ffffff; --fg: #1a1d21; --muted: #667085; --line: #e4e7ec;
  --accent: #2563eb; --green: #16a34a; --orange: #ea580c; --asset: #98a2b3;
  --card: #f9fafb;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #101418; --fg: #e6e8eb; --muted: #98a2b3; --line: #2c333a;
    --accent: #60a5fa; --green: #4ade80; --orange: #fb923c; --asset: #667085;
    --card: #171c22;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0 auto; padding: 24px; max-width: 1000px;
  background: var(--bg); color: var(--fg);
  font: 15px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
h1 { font-size: 1.5rem; margin: 0 0 4px; }
h2 { font-size: 1.1rem; margin: 32px 0 12px; }
.meta { color: var(--muted); font-size: 0.85rem; margin-bottom: 20px; }
.summary { display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0; }
.card {
  background: var(--card); border: 1px solid var(--line); border-radius: 8px;
  padding: 12px 16px; min-width: 180px;
}
.card .label { color: var(--muted); font-size: 0.8rem; }
.card .value { font-size: 1.15rem; font-weight: 600; }
.card .sub { color: var(--muted); font-size: 0.8rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.88rem; }
th, td { padding: 6px 10px; text-align: right; border-bottom: 1px solid var(--line); }
th:first-child, td:first-child { text-align: left; }
th { color: var(--muted); font-weight: 600; }
.pos { color: var(--green); } .neg { color: var(--orange); }
.chart-wrap { overflow-x: auto; }
svg text { fill: var(--fg); font: 12px -apple-system, sans-serif; }
svg .axis { stroke: var(--line); }
svg .gridline { stroke: var(--line); stroke-dasharray: 2 3; }
svg .muted { fill: var(--muted); }
.corr td { text-align: center; padding: 4px 6px; }
.note { color: var(--muted); font-size: 0.82rem; }
footer { margin-top: 36px; color: var(--muted); font-size: 0.8rem; border-top: 1px solid var(--line); padding-top: 12px; }
"""


def _pct(x: float, digits: int = 1) -> str:
    return '%.*f%%' % (digits, 100.0 * x)


def _sek(x: float) -> str:
    return '{:,.0f} kr'.format(x).replace(',', ' ')


def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


class _Scale:
    def __init__(self, points: Sequence[Tuple[float, float]]):
        vols = [p[0] for p in points]
        rets = [p[1] for p in points]
        vol_pad = max((max(vols) - min(vols)) * 0.10, 0.01)
        ret_pad = max((max(rets) - min(rets)) * 0.10, 0.01)
        self.x0, self.x1 = max(0.0, min(vols) - vol_pad), max(vols) + vol_pad
        self.y0, self.y1 = min(rets) - ret_pad, max(rets) + ret_pad

    def x(self, vol: float) -> float:
        frac = (vol - self.x0) / (self.x1 - self.x0)
        return MARGIN_L + frac * (SVG_W - MARGIN_L - MARGIN_R)

    def y(self, ret: float) -> float:
        frac = (ret - self.y0) / (self.y1 - self.y0)
        return SVG_H - MARGIN_B - frac * (SVG_H - MARGIN_T - MARGIN_B)


def _ticks(lo: float, hi: float, n: int = 6) -> List[float]:
    if hi <= lo:
        return [lo]
    raw = (hi - lo) / n
    magnitude = 10 ** np.floor(np.log10(raw))
    step = min((s for s in (1, 2, 5, 10) if s * magnitude >= raw), default=10) * magnitude
    first = np.ceil(lo / step) * step
    return list(np.arange(first, hi + step / 2, step))


def frontier_svg(result: OptimizationResult) -> str:
    points = list(result.frontier)
    points.append((result.current.vol, result.current.ret))
    points.append((result.max_sharpe.vol, result.max_sharpe.ret))
    points.append((result.min_variance.vol, result.min_variance.ret))
    for i in range(len(result.labels)):
        points.append((float(result.asset_vols[i]), float(result.mu[i])))
    scale = _Scale(points)

    parts = ['<svg viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
             'aria-label="Efficient frontier">' % (SVG_W, SVG_H, SVG_W, SVG_H)]

    for tick in _ticks(scale.x0, scale.x1):
        x = scale.x(tick)
        parts.append('<line class="gridline" x1="%.1f" y1="%d" x2="%.1f" y2="%d"/>'
                     % (x, MARGIN_T, x, SVG_H - MARGIN_B))
        parts.append('<text class="muted" x="%.1f" y="%d" text-anchor="middle">%s</text>'
                     % (x, SVG_H - MARGIN_B + 18, _pct(tick, 0)))
    for tick in _ticks(scale.y0, scale.y1):
        y = scale.y(tick)
        parts.append('<line class="gridline" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>'
                     % (MARGIN_L, y, SVG_W - MARGIN_R, y))
        parts.append('<text class="muted" x="%d" y="%.1f" text-anchor="end" dy="4">%s</text>'
                     % (MARGIN_L - 8, y, _pct(tick, 0)))

    parts.append('<line class="axis" x1="%d" y1="%d" x2="%d" y2="%d"/>'
                 % (MARGIN_L, SVG_H - MARGIN_B, SVG_W - MARGIN_R, SVG_H - MARGIN_B))
    parts.append('<line class="axis" x1="%d" y1="%d" x2="%d" y2="%d"/>'
                 % (MARGIN_L, MARGIN_T, MARGIN_L, SVG_H - MARGIN_B))
    parts.append('<text x="%d" y="%d" text-anchor="middle">Volatility (annualized)</text>'
                 % ((MARGIN_L + SVG_W - MARGIN_R) // 2, SVG_H - 8))
    parts.append('<text x="14" y="%d" text-anchor="middle" transform="rotate(-90 14 %d)">'
                 'Return (annualized)</text>' % (SVG_H // 2, SVG_H // 2))

    if len(result.frontier) > 1:
        path = ' '.join('%.1f,%.1f' % (scale.x(v), scale.y(r)) for v, r in result.frontier)
        parts.append('<polyline points="%s" fill="none" stroke="var(--accent)" '
                     'stroke-width="2" opacity="0.85"/>' % path)

    for i, label in enumerate(result.labels):
        vol, ret = float(result.asset_vols[i]), float(result.mu[i])
        parts.append(
            '<circle cx="%.1f" cy="%.1f" r="4" fill="var(--asset)" opacity="0.8">'
            '<title>%s — return %s, vol %s</title></circle>'
            % (scale.x(vol), scale.y(ret), _esc(label), _pct(ret), _pct(vol))
        )

    markers = [
        (result.current, 'Current portfolio', 'var(--accent)', 'circle'),
        (result.min_variance, 'Min variance', 'var(--orange)', 'square'),
        (result.max_sharpe, 'Max Sharpe', 'var(--green)', 'diamond'),
    ]
    for point, name, color, shape in markers:
        x, y = scale.x(point.vol), scale.y(point.ret)
        title = ('<title>%s — return %s, vol %s, Sharpe %.2f</title>'
                 % (name, _pct(point.ret), _pct(point.vol), point.sharpe))
        if shape == 'circle':
            parts.append('<circle cx="%.1f" cy="%.1f" r="7" fill="%s" stroke="var(--bg)" '
                         'stroke-width="1.5">%s</circle>' % (x, y, color, title))
        elif shape == 'square':
            parts.append('<rect x="%.1f" y="%.1f" width="12" height="12" fill="%s" '
                         'stroke="var(--bg)" stroke-width="1.5">%s</rect>'
                         % (x - 6, y - 6, color, title))
        else:
            parts.append('<path d="M %.1f %.1f L %.1f %.1f L %.1f %.1f L %.1f %.1f Z" '
                         'fill="%s" stroke="var(--bg)" stroke-width="1.5">%s</path>'
                         % (x, y - 8, x + 8, y, x, y + 8, x - 8, y, color, title))

    legend_x = MARGIN_L + 16
    legend_items = [('var(--accent)', 'Current'), ('var(--green)', 'Max Sharpe'),
                    ('var(--orange)', 'Min variance'), ('var(--asset)', 'Individual assets')]
    for i, (color, text) in enumerate(legend_items):
        y = MARGIN_T + 8 + i * 20
        parts.append('<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (legend_x, y, color))
        parts.append('<text x="%d" y="%d" dy="4">%s</text>' % (legend_x + 12, y, text))

    parts.append('</svg>')
    return ''.join(parts)


def _corr_color(value: float) -> str:
    """Diverging blue (negative) to red (positive) with alpha by magnitude."""
    alpha = min(abs(value), 1.0) * 0.55
    rgb = '220, 38, 38' if value >= 0 else '37, 99, 235'
    return 'rgba(%s, %.2f)' % (rgb, alpha)


def _summary_cards(result: OptimizationResult, total_value_sek: float) -> str:
    cards = [('Portfolio value (optimized subset)', _sek(total_value_sek), '')]
    for name, point in (('Current', result.current), ('Max Sharpe', result.max_sharpe),
                        ('Min variance', result.min_variance)):
        cards.append((name, 'Sharpe %.2f' % point.sharpe,
                      'return %s · vol %s' % (_pct(point.ret), _pct(point.vol))))
    return '<div class="summary">%s</div>' % ''.join(
        '<div class="card"><div class="label">%s</div><div class="value">%s</div>'
        '<div class="sub">%s</div></div>' % (_esc(a), _esc(b), _esc(c))
        for a, b, c in cards
    )


def _weights_table(result: OptimizationResult, names, values_sek, tickers) -> str:
    rows = []
    order = np.argsort(-result.current.weights)
    for i in order:
        delta = result.max_sharpe.weights[i] - result.current.weights[i]
        rows.append(
            '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>'
            '<td class="%s">%+.1f pp</td></tr>'
            % (_esc(names[i]), _esc(tickers[i]), _sek(values_sek[i]),
               _pct(result.current.weights[i]), _pct(result.max_sharpe.weights[i]),
               _pct(result.min_variance.weights[i]),
               'pos' if delta >= 0 else 'neg', 100 * delta)
        )
    return ('<table><thead><tr><th>Holding</th><th>Source</th><th>Value</th>'
            '<th>Current</th><th>Max Sharpe</th><th>Min var</th><th>Δ to max Sharpe</th>'
            '</tr></thead><tbody>%s</tbody></table>' % ''.join(rows))


def _stats_table(result: OptimizationResult, names, rf: float) -> str:
    rows = []
    for i, name in enumerate(names):
        vol = float(result.asset_vols[i])
        sharpe = (float(result.mu[i]) - rf) / vol if vol > 0 else float('nan')
        rows.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%.2f</td></tr>'
                    % (_esc(name), _pct(float(result.mu[i])), _pct(vol), sharpe))
    return ('<table><thead><tr><th>Holding</th><th>Ann. return</th><th>Ann. vol</th>'
            '<th>Sharpe</th></tr></thead><tbody>%s</tbody></table>' % ''.join(rows))


def _corr_table(result: OptimizationResult, short_names) -> str:
    header = ''.join('<th>%s</th>' % _esc(n) for n in short_names)
    rows = []
    for i, name in enumerate(short_names):
        cells = ''.join(
            '<td style="background-color:%s">%.2f</td>'
            % (_corr_color(float(result.corr[i, j])), float(result.corr[i, j]))
            for j in range(len(short_names))
        )
        rows.append('<tr><td>%s</td>%s</tr>' % (_esc(name), cells))
    return ('<div class="chart-wrap"><table class="corr"><thead><tr><th></th>%s</tr>'
            '</thead><tbody>%s</tbody></table></div>' % (header, ''.join(rows)))


def _excluded_section(excluded, total_sek: float) -> str:
    if not excluded:
        return ''
    rows = ''.join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
        % (_esc(h.name), _esc(h.isin), _sek(h.market_value_sek),
           _pct(h.market_value_sek / total_sek if total_sek else 0.0), _esc(reason))
        for h, reason in excluded
    )
    return (
        '<h2>Excluded holdings</h2>'
        '<p class="note">These holdings were left out of the optimization. To include '
        'one, add a line to <code>portfolio/ticker_overrides.csv</code> as '
        '<code>isin,ticker</code> where ticker is a Yahoo ticker or '
        '<code>avanza:&lt;orderbookId&gt;</code>.</p>'
        '<table><thead><tr><th>Holding</th><th>ISIN</th><th>Value</th>'
        '<th>Share of portfolio</th><th>Reason</th></tr></thead>'
        '<tbody>%s</tbody></table>' % rows
    )


def render_report(result: OptimizationResult, names, tickers, values_sek,
                  excluded, total_value_sek: float, rf: float,
                  window_start: str, window_end: str, n_days: int,
                  generated_at: str) -> str:
    short_names = [n if len(n) <= 14 else n[:13] + '…' for n in names]
    excluded_value = sum(h.market_value_sek for h, _ in excluded)
    grand_total = total_value_sek + excluded_value
    excluded_note = ''
    if excluded_value > 0 and grand_total > 0:
        excluded_note = (' Excluded holdings represent %s of total portfolio value.'
                         % _pct(excluded_value / grand_total))
    return (
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Portfolio optimization report</title>'
        '<style>%s</style>'
        '<h1>Portfolio optimization</h1>'
        '<div class="meta">Markowitz mean-variance · long-only · %d holdings · '
        'data window %s → %s (%d trading days) · risk-free rate %s · generated %s</div>'
        '%s'
        '<h2>Efficient frontier</h2>'
        '<div class="chart-wrap">%s</div>'
        '<h2>Weights: current vs optimal</h2>%s'
        '<h2>Per-asset statistics</h2>%s'
        '<h2>Correlation matrix</h2>%s'
        '%s'
        '<footer>Prices: Yahoo Finance and avanza.se public NAV data, native currency; '
        'static FX rates are used only to value current holdings in SEK (FX volatility '
        'is not modeled in the covariance).%s Past performance does not guarantee '
        'future results — mean-variance inputs are historical estimates.</footer>'
        % (CSS, len(names), _esc(window_start), _esc(window_end), n_days, _pct(rf),
           _esc(generated_at), _summary_cards(result, total_value_sek),
           frontier_svg(result), _weights_table(result, names, values_sek, tickers),
           _stats_table(result, names, rf), _corr_table(result, short_names),
           _excluded_section(excluded, grand_total), excluded_note)
    )
