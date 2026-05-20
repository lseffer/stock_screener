import { useState } from 'react';
import type { PresetId } from '../types';
import { presets } from '../columns';

interface ToolbarProps {
  generatedAt: string;
  totalRows: number;
  visibleRows: number;
  search: string;
  onSearch: (s: string) => void;
  preset: PresetId;
  onPreset: (p: PresetId) => void;
  minPScore: number | null;
  onMinPScore: (v: number | null) => void;
  sector: string | null;
  sectors: string[];
  onSector: (s: string | null) => void;
  onDownloadCsv: () => void;
  isMobile: boolean;
  columnPicker?: React.ReactNode;
}

export function Toolbar({
  generatedAt,
  totalRows,
  visibleRows,
  search,
  onSearch,
  preset,
  onPreset,
  minPScore,
  onMinPScore,
  sector,
  sectors,
  onSector,
  onDownloadCsv,
  isMobile,
  columnPicker,
}: ToolbarProps) {
  const [filtersOpen, setFiltersOpen] = useState(false);

  return (
    <header className="toolbar">
      <div className="toolbar-top">
        <div className="brand">
          <h1>Nordic Stock Screener</h1>
          <span className="generation-date">Updated {generatedAt}</span>
        </div>
        <div className="toolbar-actions">
          <button
            className="btn btn-ghost"
            onClick={() => setFiltersOpen((v) => !v)}
            aria-expanded={filtersOpen}
            aria-controls="filter-panel"
          >
            {filtersOpen ? 'Hide filters' : 'Filters'}
          </button>
          <button className="btn btn-primary" onClick={onDownloadCsv}>
            Download CSV
          </button>
          {!isMobile && (
            <a className="btn btn-ghost" href="stocks.db" download>
              Download DB
            </a>
          )}
        </div>
      </div>

      <div className="toolbar-search">
        <input
          type="search"
          inputMode="search"
          placeholder="Search company, symbol, or sector…"
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          aria-label="Search"
        />
        <span className="result-count">
          {visibleRows.toLocaleString()} / {totalRows.toLocaleString()}
        </span>
      </div>

      <div className="preset-chips" role="tablist" aria-label="Metric preset">
        {(Object.keys(presets) as PresetId[]).map((id) => (
          <button
            key={id}
            role="tab"
            aria-selected={preset === id}
            className={`chip ${preset === id ? 'chip-active' : ''}`}
            onClick={() => onPreset(id)}
          >
            {presets[id].label}
          </button>
        ))}
      </div>

      {filtersOpen && (
        <div className="filter-panel" id="filter-panel">
          <label className="filter-field">
            <span>Min Piotroski</span>
            <select
              value={minPScore ?? ''}
              onChange={(e) =>
                onMinPScore(e.target.value === '' ? null : Number(e.target.value))
              }
            >
              <option value="">Any</option>
              {[3, 4, 5, 6, 7, 8, 9].map((n) => (
                <option key={n} value={n}>
                  ≥ {n}
                </option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span>Sector</span>
            <select
              value={sector ?? ''}
              onChange={(e) => onSector(e.target.value || null)}
            >
              <option value="">All sectors</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          {columnPicker && <div className="filter-field">{columnPicker}</div>}
        </div>
      )}
    </header>
  );
}
