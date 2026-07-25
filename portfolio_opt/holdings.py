"""Parse broker position exports (Avanza, Nordea, or a generic format) into holdings.

All parsers return a list of Holding. Rows without a valid ISIN or market value
(cash rows, summary rows) are skipped with a warning. Numbers are parsed
Swedish-style ("1 234,56") as well as plain ("1234.56").
"""
import csv
import io
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from utils.fx import EUR_RATES

ISIN_RE = re.compile(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$')

# Thousands separators seen in Nordic exports: space, NBSP, narrow NBSP, apostrophe.
_THOUSANDS = str.maketrans('', '', '   ’\'')


@dataclass(frozen=True)
class Holding:
    name: str
    isin: str
    quantity: float
    market_value: float  # in native currency
    currency: str
    account: str


@dataclass
class MergedHolding:
    name: str
    isin: str
    quantity: float
    market_value_sek: float
    currencies: List[str] = field(default_factory=list)
    accounts: List[str] = field(default_factory=list)


def sek_rate(currency: str) -> Optional[float]:
    """SEK per one unit of ``currency``, derived from the static EUR rates."""
    eur = EUR_RATES.get(str(currency).upper())
    if eur is None:
        return None
    return eur / EUR_RATES['SEK']


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ('utf-8-sig', 'utf-16', 'latin-1'):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode('latin-1', errors='replace')


def _parse_number(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    text = value.strip()
    # Strip trailing currency codes like "1 234,56 SEK".
    text = re.sub(r'\s*[A-Za-z]{3}$', '', text)
    if text in ('', '-', '--'):
        return None
    text = text.translate(_THOUSANDS)
    if ',' in text and '.' in text:
        # "1.234,56" -> dot is thousands separator
        text = text.replace('.', '').replace(',', '.')
    else:
        text = text.replace(',', '.')
    try:
        return float(text)
    except ValueError:
        return None


AVANZA_ALIASES = {
    'name': ['namn', 'värdepapper', 'värdepapper/beskrivning'],
    'quantity': ['volym', 'antal'],
    'market_value': ['marknadsvärde'],
    'isin': ['isin'],
    'currency': ['valuta'],
    'account': ['kontonummer', 'konto'],
}

NORDEA_ALIASES = {
    'name': ['namn', 'instrument', 'värdepapper'],
    'quantity': ['antal', 'volym', 'mängd'],
    'market_value': ['marknadsvärde', 'marknadsvärde sek', 'värde'],
    'isin': ['isin', 'isin-kod'],
    'currency': ['valuta'],
    'account': ['konto', 'kontonummer', 'depå'],
}

GENERIC_HEADER = ['name', 'isin', 'quantity', 'market_value', 'currency']


def _header_fields(text: str, delimiter: str) -> List[str]:
    first_line = text.lstrip('﻿').splitlines()[0] if text.strip() else ''
    return [h.strip().strip('"').lower() for h in first_line.split(delimiter)]


def _detect_delimiter(text: str) -> str:
    first_line = text.splitlines()[0] if text.strip() else ''
    return ';' if first_line.count(';') >= first_line.count(',') else ','


def _parse_with_aliases(text: str, delimiter: str, aliases: Dict[str, Sequence[str]],
                        broker: str, log) -> List[Holding]:
    reader = csv.DictReader(io.StringIO(text.lstrip('﻿')), delimiter=delimiter)
    if reader.fieldnames is None:
        return []
    normalized = {name.strip().strip('"').lower(): name for name in reader.fieldnames}

    columns = {}
    for target, candidates in aliases.items():
        for candidate in candidates:
            if candidate in normalized:
                columns[target] = normalized[candidate]
                break

    missing = [k for k in ('isin', 'market_value') if k not in columns]
    if missing:
        raise ValueError(
            '%s file is missing required column(s) %s; found headers: %s'
            % (broker, missing, list(normalized))
        )

    holdings = []
    for row in reader:
        isin = (row.get(columns['isin']) or '').strip().upper()
        market_value = _parse_number(row.get(columns['market_value']))
        name = (row.get(columns.get('name', ''), '') or '').strip()
        if not ISIN_RE.match(isin) or market_value is None or market_value <= 0:
            if any((v or '').strip() for v in row.values()):
                log.warning('Skipping %s row without valid ISIN/market value: %r', broker, name or isin)
            continue
        quantity = _parse_number(row.get(columns.get('quantity', ''), '')) or 0.0
        currency = (row.get(columns.get('currency', ''), '') or 'SEK').strip().upper() or 'SEK'
        account = (row.get(columns.get('account', ''), '') or '').strip()
        holdings.append(Holding(
            name=name or isin,
            isin=isin,
            quantity=quantity,
            market_value=market_value,
            currency=currency,
            account='%s:%s' % (broker, account) if account else broker,
        ))
    return holdings


def parse_avanza(text: str, log) -> List[Holding]:
    return _parse_with_aliases(text, _detect_delimiter(text), AVANZA_ALIASES, 'avanza', log)


def parse_nordea(text: str, log) -> List[Holding]:
    return _parse_with_aliases(text, _detect_delimiter(text), NORDEA_ALIASES, 'nordea', log)


def parse_generic(text: str, log) -> List[Holding]:
    aliases = {k: [k] for k in GENERIC_HEADER}
    aliases['account'] = ['account']
    return _parse_with_aliases(text, _detect_delimiter(text), aliases, 'generic', log)


def detect_and_parse(path: Path, log) -> List[Holding]:
    text = _read_text(path)
    if not text.strip():
        log.warning('Skipping empty file %s', path)
        return []
    delimiter = _detect_delimiter(text)
    headers = _header_fields(text, delimiter)

    if all(h in headers for h in ('name', 'isin', 'quantity', 'market_value')):
        parser, broker = parse_generic, 'generic'
    elif 'volym' in headers or 'kontonummer' in headers:
        parser, broker = parse_avanza, 'Avanza'
    elif any(h in headers for h in ('isin', 'isin-kod')):
        parser, broker = parse_nordea, 'Nordea'
    else:
        raise ValueError(
            'Cannot detect format of %s. Found headers %s. Expected an Avanza or '
            'Nordea positions export, or the generic format: %s'
            % (path.name, headers, ','.join(GENERIC_HEADER + ['account']))
        )
    log.info('Parsing %s as %s export', path.name, broker)
    return parser(text, log)


def load_holdings(portfolio_dir: Path, log) -> List[Holding]:
    csv_files = sorted(p for p in portfolio_dir.glob('*.csv') if p.name != 'ticker_overrides.csv')
    if not csv_files:
        raise FileNotFoundError(
            'No holdings CSV files found in %s/. Export your positions from '
            'Avanza (Min ekonomi -> Innehav -> export) and/or Nordea and drop the '
            'CSV files there, or create one in the generic format: %s'
            % (portfolio_dir, ','.join(GENERIC_HEADER + ['account']))
        )
    holdings: List[Holding] = []
    for path in csv_files:
        holdings.extend(detect_and_parse(path, log))
    return holdings


def merge_holdings(holdings: List[Holding], log) -> List[MergedHolding]:
    """Merge rows for the same ISIN across accounts/brokers, valued in SEK."""
    merged: Dict[str, MergedHolding] = {}
    for holding in holdings:
        rate = sek_rate(holding.currency)
        if rate is None:
            log.warning('Unknown currency %s for %s; skipping', holding.currency, holding.name)
            continue
        value_sek = holding.market_value * rate
        entry = merged.get(holding.isin)
        if entry is None:
            merged[holding.isin] = MergedHolding(
                name=holding.name,
                isin=holding.isin,
                quantity=holding.quantity,
                market_value_sek=value_sek,
                currencies=[holding.currency],
                accounts=[holding.account],
            )
        else:
            entry.quantity += holding.quantity
            entry.market_value_sek += value_sek
            if holding.currency not in entry.currencies:
                entry.currencies.append(holding.currency)
            if holding.account not in entry.accounts:
                entry.accounts.append(holding.account)
    return sorted(merged.values(), key=lambda m: -m.market_value_sek)
