const compact = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
});

const decimal = new Intl.NumberFormat('en-US', {
  maximumFractionDigits: 2,
});

const pct = new Intl.NumberFormat('en-US', {
  style: 'percent',
  maximumFractionDigits: 1,
});

export function fmtCompact(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '–';
  return compact.format(v);
}

export function fmtDecimal(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '–';
  return decimal.format(v);
}

export function fmtPercent(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '–';
  return pct.format(v);
}

export function fmtPrice(
  v: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '–';
  if (!currency) return decimal.format(v);
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 2,
    }).format(v);
  } catch {
    return `${decimal.format(v)} ${currency}`;
  }
}

export function fmtText(v: string | null | undefined): string {
  if (v === null || v === undefined || v === '') return '–';
  return v;
}

const eurCompact = new Intl.NumberFormat('en-IE', {
  notation: 'compact',
  style: 'currency',
  currency: 'EUR',
  maximumFractionDigits: 1,
});

export function fmtEUR(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '–';
  return eurCompact.format(v);
}
