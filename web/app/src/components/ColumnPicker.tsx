import type { Table } from '@tanstack/react-table';
import type { Stock } from '../types';
import { COLUMN_LABELS } from '../columns';

interface ColumnPickerProps {
  table: Table<Stock>;
}

export function ColumnPicker({ table }: ColumnPickerProps) {
  return (
    <details className="column-picker">
      <summary>Columns</summary>
      <div className="column-list">
        {table.getAllLeafColumns().map((col) => {
          if (!col.getCanHide()) return null;
          return (
            <label key={col.id} className="column-toggle">
              <input
                type="checkbox"
                checked={col.getIsVisible()}
                onChange={col.getToggleVisibilityHandler()}
              />
              <span>{COLUMN_LABELS[col.id] ?? col.id}</span>
            </label>
          );
        })}
      </div>
    </details>
  );
}
