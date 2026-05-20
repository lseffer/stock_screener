"""Hardcoded FX rates for converting native currencies to EUR.

Rates are approximate and intended for market-cap classification, not
precision math. Refresh manually when they drift materially.
"""

EUR_RATES = {
    'EUR': 1.0,
    'SEK': 0.087,
    'DKK': 0.134,
    'NOK': 0.086,
    'ISK': 0.0066,
    'USD': 0.92,
    'GBP': 1.17,
}


def to_eur(value, currency):
    """Convert ``value`` from ``currency`` to EUR. Returns None on unknown inputs."""
    if value is None or currency is None:
        return None
    rate = EUR_RATES.get(str(currency).upper())
    if rate is None:
        return None
    return value * rate
