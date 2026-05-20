import { useState } from 'react';
import type { CapTier, PresetId } from '../types';
import { presets } from '../columns';

export interface Filters {
  capTiers: Set<CapTier>;
  minPScore: number | null;
  sector: string | null;
  minMagicFormula: number | null;
  minRoic: number | null;             // percent (user-facing)
  minShareholderYield: number | null; // percent (user-facing)
  maxEvEbitda: number | null;
  maxTrailingPe: number | null;
  maxPriceToSales: number | null;
  minNcavRatio: number | null;
  minMarketCapEurM: number | null;    // millions of EUR
}

export const DEFAULT_FILTERS: Filters = {
  capTiers: new Set(),
  minPScore: null,
  sector: null,
  minMagicFormula: null,
  minRoic: null,
  minShareholderYield: null,
  maxEvEbitda: null,
  maxTrailingPe: null,
  maxPriceToSales: null,
  minNcavRatio: null,
  minMarketCapEurM: null,
};

export function activeFilterCount(f: Filters): number {
  let n = 0;
  if (f.capTiers.size > 0) n += 1;
  if (f.minPScore !== null) n += 1;
  if (f.sector) n += 1;
  if (f.minMagicFormula !== null) n += 1;
  if (f.minRoic !== null) n += 1;
  if (f.minShareholderYield !== null) n += 1;
  if (f.maxEvEbitda !== null) n += 1;
  if (f.maxTrailingPe !== null) n += 1;
  if (f.maxPriceToSales !== null) n += 1;
  if (f.minNcavRatio !== null) n += 1;
  if (f.minMarketCapEurM !== null) n += 1;
  return n;
}

const CAP_TIERS: { id: CapTier; label: string }[] = [
  { id: 'large', label: 'Large' },
  { id: 'mid', label: 'Mid' },
  { id: 'small', label: 'Small' },
  { id: 'micro', label: 'Micro' },
];

interface ToolbarProps {
  generatedAt: string;
  totalRows: number;
  visibleRows: number;
  search: string;
  onSearch: (s: string) => void;
  preset: PresetId;
  onPreset: (p: PresetId) => void;
  filters: Filters;
  onFilters: (f: Filters) => void;
  activeFilterCount: number;
  sectors: string[];
  onDownloadCsv: () => void;
  isMobile: boolean;
  columnPicker?: React.ReactNode;
}

function parseNumber(value: string): number | null {
  if (value === '') return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function Toolbar({
  generatedAt,
  totalRows,
  visibleRows,
  search,
  onSearch,
  preset,
  onPreset,
  filters,
  onFilters,
  activeFilterCount,
  sectors,
  onDownloadCsv,
  isMobile,
  columnPicker,
}: ToolbarProps) {
  const [filtersOpen, setFiltersOpen] = useState(false);

  const update = <K extends keyof Filters>(key: K, value: Filters[K]) =>
    onFilters({ ...filters, [key]: value });

  const toggleCapTier = (tier: CapTier) => {
    const next = new Set(filters.capTiers);
    if (next.has(tier)) next.delete(tier);
    else next.add(tier);
    update('capTiers', next);
  };

  const reset = () => onFilters(DEFAULT_FILTERS);

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
            {activeFilterCount > 0 && (
              <span className="filter-badge">{activeFilterCount}</span>
            )}
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
          <div className="filter-field filter-field-wide">
            <span>Cap tier</span>
            <div className="cap-tier-chips" role="group" aria-label="Market cap tier">
              {CAP_TIERS.map((t) => {
                const active = filters.capTiers.has(t.id);
                return (
                  <button
                    key={t.id}
                    type="button"
                    className={`chip ${active ? 'chip-active' : ''}`}
                    aria-pressed={active}
                    onClick={() => toggleCapTier(t.id)}
                  >
                    {t.label}
                  </button>
                );
              })}
            </div>
          </div>

          <label className="filter-field">
            <span>Min Piotroski</span>
            <select
              value={filters.minPScore ?? ''}
              onChange={(e) => update('minPScore', e.target.value === '' ? null : Number(e.target.value))}
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
              value={filters.sector ?? ''}
              onChange={(e) => update('sector', e.target.value || null)}
            >
              <option value="">All sectors</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>

          <NumberInput
            label="Min Magic Formula"
            value={filters.minMagicFormula}
            onChange={(v) => update('minMagicFormula', v)}
            step="0.1"
          />
          <NumberInput
            label="Min ROIC (%)"
            value={filters.minRoic}
            onChange={(v) => update('minRoic', v)}
            step="1"
          />
          <NumberInput
            label="Min SH Yield (%)"
            value={filters.minShareholderYield}
            onChange={(v) => update('minShareholderYield', v)}
            step="1"
          />
          <NumberInput
            label="Max EV/EBITDA"
            value={filters.maxEvEbitda}
            onChange={(v) => update('maxEvEbitda', v)}
            step="1"
          />
          <NumberInput
            label="Max P/E (TTM)"
            value={filters.maxTrailingPe}
            onChange={(v) => update('maxTrailingPe', v)}
            step="1"
          />
          <NumberInput
            label="Max P/Sales"
            value={filters.maxPriceToSales}
            onChange={(v) => update('maxPriceToSales', v)}
            step="0.5"
          />
          <NumberInput
            label="Min NCAV"
            value={filters.minNcavRatio}
            onChange={(v) => update('minNcavRatio', v)}
            step="0.1"
          />
          <NumberInput
            label="Min Mkt Cap (€M)"
            value={filters.minMarketCapEurM}
            onChange={(v) => update('minMarketCapEurM', v)}
            step="50"
          />

          {columnPicker && <div className="filter-field filter-field-wide">{columnPicker}</div>}

          <div className="filter-field filter-field-reset">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={reset}
              disabled={activeFilterCount === 0}
            >
              Reset filters
            </button>
          </div>
        </div>
      )}
    </header>
  );
}

function NumberInput({
  label,
  value,
  onChange,
  step,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  step?: string;
}) {
  return (
    <label className="filter-field">
      <span>{label}</span>
      <input
        type="number"
        inputMode="decimal"
        step={step}
        value={value ?? ''}
        onChange={(e) => onChange(parseNumber(e.target.value))}
        placeholder="Any"
      />
    </label>
  );
}
