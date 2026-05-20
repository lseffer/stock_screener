import { useRef } from 'react';
import { flexRender, type Table } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Stock } from '../types';

interface StockTableProps {
  table: Table<Stock>;
}

const ROW_HEIGHT = 44;

export function StockTable({ table }: StockTableProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rows = table.getRowModel().rows;

  const virtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => containerRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 8,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalSize = virtualizer.getTotalSize();
  const paddingTop = virtualItems[0]?.start ?? 0;
  const paddingBottom = virtualItems.length
    ? totalSize - (virtualItems[virtualItems.length - 1]!.end ?? 0)
    : 0;

  return (
    <div className="table-scroller" ref={containerRef}>
      <table className="data-table">
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id}>
              {hg.headers.map((header) => {
                const canSort = header.column.getCanSort();
                const sorted = header.column.getIsSorted();
                return (
                  <th
                    key={header.id}
                    style={{ width: header.getSize() }}
                    className={canSort ? 'sortable' : ''}
                    onClick={
                      canSort
                        ? header.column.getToggleSortingHandler()
                        : undefined
                    }
                    aria-sort={
                      sorted === 'asc'
                        ? 'ascending'
                        : sorted === 'desc'
                          ? 'descending'
                          : 'none'
                    }
                  >
                    <span className="th-inner">
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                      {sorted === 'asc' && <span className="sort-arrow">↑</span>}
                      {sorted === 'desc' && <span className="sort-arrow">↓</span>}
                    </span>
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {paddingTop > 0 && (
            <tr style={{ height: paddingTop }} aria-hidden>
              <td colSpan={table.getVisibleFlatColumns().length} />
            </tr>
          )}
          {virtualItems.map((vi) => {
            const row = rows[vi.index]!;
            return (
              <tr key={row.id} style={{ height: ROW_HEIGHT }}>
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} style={{ width: cell.column.getSize() }}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
          {paddingBottom > 0 && (
            <tr style={{ height: paddingBottom }} aria-hidden>
              <td colSpan={table.getVisibleFlatColumns().length} />
            </tr>
          )}
          {rows.length === 0 && (
            <tr>
              <td
                colSpan={table.getVisibleFlatColumns().length}
                className="empty-cell"
              >
                No stocks match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
