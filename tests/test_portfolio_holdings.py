import logging
import tempfile
import unittest
from pathlib import Path

from portfolio_opt.holdings import (
    Holding,
    _parse_number,
    detect_and_parse,
    merge_holdings,
    parse_avanza,
    parse_generic,
    parse_nordea,
    sek_rate,
)

log = logging.getLogger('test_portfolio_holdings')
log.addHandler(logging.NullHandler())
log.propagate = False

AVANZA_CSV = (
    '﻿Kontonummer;Namn;Volym;Marknadsvärde;ISIN;Valuta\n'
    '1234567;Ericsson B;100;8 512,50;SE0000108656;SEK\n'
    '1234567;Avanza Zero;50,5;12 345,67;SE0001718388;SEK\n'
    '1234567;Novo Nordisk B;10;7 890,00;DK0062498333;DKK\n'
    ';Summa;;28 748,17;;\n'
)

NORDEA_CSV = (
    'Instrument,ISIN-kod,Antal,Värde,Valuta\n'
    'Nordea Global Passiv,FI4000058870,200,"15 000,00",EUR\n'
    'Ericsson B,SE0000108656,40,"3 405,00",SEK\n'
)

GENERIC_CSV = (
    'name,isin,quantity,market_value,currency,account\n'
    'Ericsson B,SE0000108656,100,8512.50,SEK,manual\n'
)


class TestParseNumber(unittest.TestCase):
    def test_swedish_decimal_comma(self):
        self.assertAlmostEqual(_parse_number('1 234,56'), 1234.56)

    def test_nbsp_thousands(self):
        self.assertAlmostEqual(_parse_number('1 234,56'), 1234.56)
        self.assertAlmostEqual(_parse_number('1 234,56'), 1234.56)

    def test_plain_decimal_point(self):
        self.assertAlmostEqual(_parse_number('1234.56'), 1234.56)

    def test_dot_thousands_comma_decimal(self):
        self.assertAlmostEqual(_parse_number('1.234,56'), 1234.56)

    def test_missing_values(self):
        self.assertIsNone(_parse_number('-'))
        self.assertIsNone(_parse_number(''))
        self.assertIsNone(_parse_number(None))
        self.assertIsNone(_parse_number('abc'))

    def test_trailing_currency(self):
        self.assertAlmostEqual(_parse_number('1 234,56 SEK'), 1234.56)


class TestParseAvanza(unittest.TestCase):
    def test_parses_rows_and_skips_summary(self):
        holdings = parse_avanza(AVANZA_CSV, log)
        self.assertEqual(len(holdings), 3)
        eric = holdings[0]
        self.assertEqual(eric.isin, 'SE0000108656')
        self.assertAlmostEqual(eric.market_value, 8512.50)
        self.assertAlmostEqual(eric.quantity, 100)
        self.assertEqual(eric.currency, 'SEK')
        self.assertEqual(eric.account, 'avanza:1234567')

    def test_decimal_comma_quantity(self):
        holdings = parse_avanza(AVANZA_CSV, log)
        zero = next(h for h in holdings if h.isin == 'SE0001718388')
        self.assertAlmostEqual(zero.quantity, 50.5)

    def test_missing_required_columns_raises(self):
        with self.assertRaises(ValueError):
            parse_avanza('Namn;Volym\nfoo;1\n', log)


class TestParseNordea(unittest.TestCase):
    def test_alternate_headers(self):
        holdings = parse_nordea(NORDEA_CSV, log)
        self.assertEqual(len(holdings), 2)
        fund = holdings[0]
        self.assertEqual(fund.isin, 'FI4000058870')
        self.assertAlmostEqual(fund.market_value, 15000.0)
        self.assertEqual(fund.currency, 'EUR')


class TestDetectAndParse(unittest.TestCase):
    def _write(self, name, content, encoding='utf-8'):
        path = Path(self.tmp.name) / name
        path.write_bytes(content.encode(encoding))
        return path

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_detects_avanza(self):
        path = self._write('avanza.csv', AVANZA_CSV)
        self.assertEqual(len(detect_and_parse(path, log)), 3)

    def test_detects_nordea(self):
        path = self._write('nordea.csv', NORDEA_CSV)
        self.assertEqual(len(detect_and_parse(path, log)), 2)

    def test_detects_generic(self):
        path = self._write('mine.csv', GENERIC_CSV)
        holdings = detect_and_parse(path, log)
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].account, 'generic:manual')

    def test_utf16_avanza(self):
        path = self._write('avanza16.csv', AVANZA_CSV, encoding='utf-16')
        self.assertEqual(len(detect_and_parse(path, log)), 3)

    def test_unknown_format_raises(self):
        path = self._write('junk.csv', 'foo;bar\n1;2\n')
        with self.assertRaises(ValueError):
            detect_and_parse(path, log)


class TestMerge(unittest.TestCase):
    def test_merges_same_isin_across_brokers_with_fx(self):
        holdings = parse_avanza(AVANZA_CSV, log) + parse_nordea(NORDEA_CSV, log)
        merged = merge_holdings(holdings, log)
        by_isin = {m.isin: m for m in merged}
        self.assertEqual(len(merged), 4)
        eric = by_isin['SE0000108656']
        self.assertAlmostEqual(eric.quantity, 140)
        self.assertAlmostEqual(eric.market_value_sek, (8512.50 + 3405.00) * sek_rate('SEK'))
        self.assertEqual(sorted(eric.accounts), ['avanza:1234567', 'nordea'])
        novo = by_isin['DK0062498333']
        self.assertAlmostEqual(novo.market_value_sek, 7890.0 * sek_rate('DKK'))

    def test_unknown_currency_skipped(self):
        holdings = [Holding('X', 'SE0000000001', 1, 100.0, 'XXX', 'a')]
        self.assertEqual(merge_holdings(holdings, log), [])

    def test_sorted_by_value_desc(self):
        holdings = parse_avanza(AVANZA_CSV, log)
        merged = merge_holdings(holdings, log)
        values = [m.market_value_sek for m in merged]
        self.assertEqual(values, sorted(values, reverse=True))


if __name__ == '__main__':
    unittest.main()
