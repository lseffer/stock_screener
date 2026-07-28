import logging
import tempfile
import unittest
from pathlib import Path

from portfolio_opt.holdings import MergedHolding
from portfolio_opt.resolve import (
    ResolutionCache,
    load_overrides,
    parse_override_value,
    resolve_all,
)

log = logging.getLogger('test_portfolio_resolve')
log.addHandler(logging.NullHandler())
log.propagate = False


def holding(isin, name='X'):
    return MergedHolding(name=name, isin=isin, quantity=1, market_value_sek=100.0)


class TestNameKeyedResolution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = ResolutionCache(Path(self.tmp.name))

    def test_name_only_holding_resolves_and_caches_by_name_key(self):
        calls = []

        def resolver(isin, name, tlog):
            calls.append((isin, name))
            return ('avanza', '325406')

        resolved, excluded = resolve_all(
            [holding('', name='Avanza Zero')], {}, self.cache, log, resolver=resolver,
        )
        self.assertEqual(resolved, {'name:avanza zero': ('avanza', '325406')})
        self.assertEqual(calls, [('', 'Avanza Zero')])
        self.assertEqual(excluded, [])
        reloaded = ResolutionCache(Path(self.tmp.name))
        self.assertEqual(reloaded.get('name:avanza zero'), ('avanza', '325406'))

    def test_override_by_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'ticker_overrides.csv').write_text(
                'isin,ticker\nAvanza Global,avanza:944976\n'
            )
            overrides = load_overrides(Path(tmp), log)
        self.assertEqual(overrides, {'name:avanza global': ('avanza', '944976')})
        resolved, _ = resolve_all(
            [holding('', name='Avanza  GLOBAL')], overrides, self.cache, log,
            resolver=lambda *a: self.fail('resolver should not be called'),
        )
        self.assertEqual(resolved['name:avanza global'], ('avanza', '944976'))


class TestOverrideParsing(unittest.TestCase):
    def test_yahoo_ticker(self):
        self.assertEqual(parse_override_value('ERIC-B.ST'), ('yahoo', 'ERIC-B.ST'))

    def test_avanza_prefix(self):
        self.assertEqual(parse_override_value('avanza:325406'), ('avanza', '325406'))
        self.assertEqual(parse_override_value('AVANZA: 325406'), ('avanza', '325406'))

    def test_empty_means_exclude(self):
        self.assertIsNone(parse_override_value(''))
        self.assertIsNone(parse_override_value('  '))


class TestLoadOverrides(unittest.TestCase):
    def test_load_from_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ticker_overrides.csv'
            path.write_text(
                'isin,ticker\n'
                'SE0000108656,ERIC-B.ST\n'
                'SE0001718388,avanza:325406\n'
                'SE0000000001,\n'
            )
            overrides = load_overrides(Path(tmp), log)
        self.assertEqual(overrides['SE0000108656'], ('yahoo', 'ERIC-B.ST'))
        self.assertEqual(overrides['SE0001718388'], ('avanza', '325406'))
        self.assertIsNone(overrides['SE0000000001'])

    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_overrides(Path(tmp), log), {})


class TestResolutionCache(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = ResolutionCache(Path(tmp))
            cache.put('SE0000108656', ('yahoo', 'ERIC-B.ST'))
            cache.save()
            reloaded = ResolutionCache(Path(tmp))
            self.assertEqual(reloaded.get('SE0000108656'), ('yahoo', 'ERIC-B.ST'))
            self.assertIsNone(reloaded.get('SE0000000001'))

    def test_corrupt_cache_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / '.ticker_cache.json').write_text('{not json')
            cache = ResolutionCache(Path(tmp))
            self.assertIsNone(cache.get('SE0000108656'))


class TestResolveAll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = ResolutionCache(Path(self.tmp.name))

    def test_override_beats_cache_and_resolver(self):
        self.cache.put('SE0000108656', ('yahoo', 'CACHED.ST'))
        calls = []

        def resolver(isin, name, tlog):
            calls.append(isin)
            return ('yahoo', 'AUTO.ST')

        resolved, excluded = resolve_all(
            [holding('SE0000108656')],
            {'SE0000108656': ('yahoo', 'OVERRIDE.ST')},
            self.cache, log, resolver=resolver,
        )
        self.assertEqual(resolved['SE0000108656'], ('yahoo', 'OVERRIDE.ST'))
        self.assertEqual(calls, [])
        self.assertEqual(excluded, [])

    def test_cache_beats_resolver(self):
        self.cache.put('SE0000108656', ('yahoo', 'CACHED.ST'))
        resolved, _ = resolve_all(
            [holding('SE0000108656')], {}, self.cache, log,
            resolver=lambda *a: ('yahoo', 'AUTO.ST'),
        )
        self.assertEqual(resolved['SE0000108656'], ('yahoo', 'CACHED.ST'))

    def test_resolver_result_cached_but_negatives_not(self):
        resolved, excluded = resolve_all(
            [holding('SE0000108656'), holding('SE0000000001')], {}, self.cache, log,
            resolver=lambda isin, name, tlog: ('yahoo', 'AUTO.ST') if isin == 'SE0000108656' else None,
        )
        self.assertEqual(resolved, {'SE0000108656': ('yahoo', 'AUTO.ST')})
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0][0].isin, 'SE0000000001')
        reloaded = ResolutionCache(Path(self.tmp.name))
        self.assertEqual(reloaded.get('SE0000108656'), ('yahoo', 'AUTO.ST'))
        self.assertIsNone(reloaded.get('SE0000000001'))

    def test_empty_override_excludes_without_resolver_call(self):
        resolved, excluded = resolve_all(
            [holding('SE0001718388')], {'SE0001718388': None}, self.cache, log,
            resolver=lambda *a: self.fail('resolver should not be called'),
        )
        self.assertEqual(resolved, {})
        self.assertEqual(excluded[0][1], 'excluded via ticker_overrides.csv')


if __name__ == '__main__':
    unittest.main()
