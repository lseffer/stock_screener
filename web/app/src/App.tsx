import { useEffect, useMemo, useState } from 'react';
import {
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
  type VisibilityState,
} from '@tanstack/react-table';
import type { DataPayload, PresetId, Stock } from './types';
import { columns, presets, visibilityForPreset } from './columns';
import { Toolbar } from './components/Toolbar';
import { StockTable } from './components/StockTable';
import { StockCards } from './components/StockCards';
import { ColumnPicker } from './components/ColumnPicker';
import { TopPicks } from './components/TopPicks';
import { useDebounced, useMediaQuery } from './hooks';
import { downloadCsv } from './csv';
import { computeTopPicks, unionPicks } from './topPicks';

const MOBILE_QUERY = '(max-width: 768px)';

const PRESET_SORT: Record<PresetId, SortingState> = {
  top_picks: [{ id: 'magic_formula_score', desc: true }],
  overview: [{ id: 'magic_formula_score', desc: true }],
  piotroski: [{ id: 'p_score', desc: true }],
  magic: [{ id: 'magic_formula_score', desc: true }],
  value: [{ id: 'shareholder_yield_stock', desc: true }],
  all: [{ id: 'magic_formula_score', desc: true }],
};

const PRIMARY_METRIC: Record<PresetId, { key: keyof Stock; label: string; type: 'pct' | 'num' | 'score' }> = {
  top_picks: { key: 'magic_formula_score', label: 'Magic F', type: 'num' },
  overview: { key: 'magic_formula_score', label: 'Magic F', type: 'num' },
  piotroski: { key: 'p_score', label: 'Piotroski', type: 'score' },
  magic: { key: 'magic_formula_score', label: 'Magic F', type: 'num' },
  value: { key: 'shareholder_yield_stock', label: 'SH Yield', type: 'pct' },
  all: { key: 'magic_formula_score', label: 'Magic F', type: 'num' },
};

export function App() {
  const isMobile = useMediaQuery(MOBILE_QUERY);
  const [payload, setPayload] = useState<DataPayload | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [preset, setPreset] = useState<PresetId>('overview');
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounced(search, 120);
  const [minPScore, setMinPScore] = useState<number | null>(null);
  const [sector, setSector] = useState<string | null>(null);
  const [sorting, setSorting] = useState<SortingState>(PRESET_SORT.overview);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(
    visibilityForPreset('overview'),
  );

  useEffect(() => {
    let cancelled = false;
    fetch('data.json', { cache: 'no-cache' })
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((raw: unknown) => {
        if (cancelled) return;
        // Tolerate both array-of-rows (legacy) and {generated_at, rows} envelope
        if (Array.isArray(raw)) {
          setPayload({ generated_at: '', rows: raw as Stock[] });
        } else {
          setPayload(raw as DataPayload);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(String(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const rows = payload?.rows ?? [];

  const sectors = useMemo(() => {
    const set = new Set<string>();
    for (const r of rows) if (r.sector) set.add(r.sector);
    return Array.from(set).sort();
  }, [rows]);

  const filteredRows = useMemo(() => {
    const q = debouncedSearch.trim().toLowerCase();
    return rows.filter((r) => {
      if (minPScore !== null && (r.p_score ?? -1) < minPScore) return false;
      if (sector && r.sector !== sector) return false;
      if (q) {
        const hay = `${r.company_name ?? ''} ${r.symbol ?? ''} ${r.sector ?? ''} ${r.isin}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [rows, debouncedSearch, minPScore, sector]);

  const table = useReactTable({
    data: filteredRows,
    columns,
    state: { sorting, columnVisibility },
    onSortingChange: setSorting,
    onColumnVisibilityChange: setColumnVisibility,
    getRowId: (row) => row.isin,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  const sortedRows = useMemo(
    () => table.getRowModel().rows.map((r) => r.original),
    [table, sorting, filteredRows],
  );

  const topPickRows = useMemo(
    () => (preset === 'top_picks' ? unionPicks(computeTopPicks(filteredRows)) : []),
    [preset, filteredRows],
  );

  const displayRows = preset === 'top_picks' ? topPickRows : sortedRows;

  const handlePreset = (p: PresetId) => {
    setPreset(p);
    setSorting(PRESET_SORT[p]);
    setColumnVisibility(visibilityForPreset(p));
  };

  const downloadAll = () => downloadCsv(displayRows);

  return (
    <div className="app-root">
      <Toolbar
        generatedAt={payload?.generated_at || ''}
        totalRows={rows.length}
        visibleRows={displayRows.length}
        search={search}
        onSearch={setSearch}
        preset={preset}
        onPreset={handlePreset}
        minPScore={minPScore}
        onMinPScore={setMinPScore}
        sector={sector}
        sectors={sectors}
        onSector={setSector}
        onDownloadCsv={downloadAll}
        isMobile={isMobile}
        columnPicker={!isMobile ? <ColumnPicker table={table} /> : undefined}
      />

      <main className="content">
        {loadError && (
          <div className="error-banner">
            Failed to load stock data: {loadError}
          </div>
        )}
        {!loadError && !payload && (
          <div className="loading">Loading screening results…</div>
        )}
        {payload && preset === 'top_picks' && <TopPicks rows={filteredRows} />}
        {payload &&
          preset !== 'top_picks' &&
          (isMobile ? (
            <StockCards rows={sortedRows} primaryMetric={PRIMARY_METRIC[preset]} />
          ) : (
            <StockTable table={table} />
          ))}
      </main>

      <footer className="site-footer">
        <span>
          {presets[preset].label} · {displayRows.length.toLocaleString()} stocks
        </span>
        <a href="https://github.com/lseffer/stock_screener" target="_blank" rel="noreferrer">
          Source on GitHub ↗
        </a>
      </footer>
    </div>
  );
}
