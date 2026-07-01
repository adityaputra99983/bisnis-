import json
import threading
import time
from urllib.request import urlopen, Request
from urllib.error import URLError

FALLBACK_RATES = {
    'IDR': 1,
    'USD': 16500,
    'EUR': 17900,
    'SGD': 12200,
    'AUD': 10700,
    'RUB': 180,
}

CURRENCY_SYMBOLS = {
    'IDR': 'Rp',
    'USD': '&#36;',
    'EUR': '&euro;',
    'SGD': 'S&#36;',
    'AUD': 'A&#36;',
    'RUB': '&#8381;',
}

CURRENCY_FLAGS = {
    'IDR': '\U0001f1ee\U0001f1e9',
    'USD': '\U0001f1fa\U0001f1f8',
    'EUR': '\U0001f1ea\U0001f1fa',
    'SGD': '\U0001f1f8\U0001f1ec',
    'AUD': '\U0001f1e6\U0001f1fa',
    'RUB': '\U0001f1f7\U0001f1fa',
}

CURRENCY_DESCS = {
    'IDR': 'Harga Lokal Terbaik',
    'USD': 'Estimated in US Dollars',
    'EUR': 'Prix estim\u00e9 en Euros',
    'SGD': 'Anggaran Dolar Singapura',
    'AUD': 'Estimated in AU Dollars',
    'RUB': '\u0426\u0435\u043d\u0430 \u0432 \u0440\u0443\u0431\u043b\u044f\u0445 (RU)',
}

CACHE_DURATION = 3600
UPDATE_INTERVAL = 3600

_live_rates = None
_last_fetch = 0
_last_success = 0
_lock = threading.Lock()


def _fetch_from_api():
    headers = {
        'User-Agent': 'BaliInkHub/1.0 (Marketplace)',
        'Accept': 'application/json',
    }
    req = Request('https://open.er-api.com/v6/latest/IDR', headers=headers)
    with urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read().decode())
    if data.get('result') != 'success':
        raise ValueError('API returned non-success result')
    raw = data['rates']
    return {
        'IDR': 1,
        'USD': 1 / raw['USD'] if raw.get('USD') else FALLBACK_RATES['USD'],
        'EUR': 1 / raw['EUR'] if raw.get('EUR') else FALLBACK_RATES['EUR'],
        'SGD': 1 / raw['SGD'] if raw.get('SGD') else FALLBACK_RATES['SGD'],
        'AUD': 1 / raw['AUD'] if raw.get('AUD') else FALLBACK_RATES['AUD'],
        'RUB': 1 / raw['RUB'] if raw.get('RUB') else FALLBACK_RATES['RUB'],
    }


def get_exchange_rates():
    global _live_rates, _last_fetch, _last_success
    now = time.time()
    if _live_rates is not None and (now - _last_fetch) < UPDATE_INTERVAL:
        return _live_rates
    with _lock:
        if _live_rates is not None and (now - _last_fetch) < UPDATE_INTERVAL:
            return _live_rates
        _last_fetch = now
        try:
            rates = _fetch_from_api()
            validated = {}
            for code in ['IDR', 'USD', 'EUR', 'SGD', 'AUD', 'RUB']:
                v = rates.get(code)
                if v and float(v) > 0:
                    validated[code] = float(v)
                else:
                    validated[code] = FALLBACK_RATES[code]
            _live_rates = validated
            _last_success = now
        except Exception:
            if _live_rates is None:
                _live_rates = dict(FALLBACK_RATES)
            _last_fetch = _last_success or now
        return _live_rates
