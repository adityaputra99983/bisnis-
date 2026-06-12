from django import template
from django.utils.safestring import mark_safe

register = template.Library()

EXCHANGE_RATES = {
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
    'EUR': 'Prix estimé en Euros',
    'SGD': 'Anggaran Dolar Singapura',
    'AUD': 'Estimated in AU Dollars',
    'RUB': 'Цена в рублях (RU)',
}


@register.filter
def get_item(d, key):
    return d.get(key)


@register.filter
def mul(value, arg):
    """Multiplies the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(is_safe=True)
def multi_currency(value):
    if value is None:
        return ''
    parts = []
    for code in ['USD', 'EUR', 'SGD', 'AUD', 'RUB']:
        rate = EXCHANGE_RATES.get(code)
        if not rate:
            continue
        converted = value / rate
        symbol = CURRENCY_SYMBOLS.get(code, code)
        if converted >= 1:
            fmt = f'{symbol}{converted:,.2f}'
        else:
            fmt = f'{symbol}{converted:,.4f}'
        parts.append(
            f'<span class="currency-item" data-currency="{code}">'
            f'{CURRENCY_FLAGS[code]} '
            f'{fmt}</span>'
        )
    return mark_safe('&nbsp;&nbsp;'.join(parts))


@register.filter(is_safe=True)
def multi_currency_detail(value):
    """Smart region-aware chip with a richer responsive conversion panel."""
    if value is None:
        return ''

    currencies = [
        ('IDR', EXCHANGE_RATES['IDR']),
        ('USD', EXCHANGE_RATES['USD']),
        ('EUR', EXCHANGE_RATES['EUR']),
        ('SGD', EXCHANGE_RATES['SGD']),
        ('AUD', EXCHANGE_RATES['AUD']),
        ('RUB', EXCHANGE_RATES['RUB']),
    ]

    # Pre-build all conversions for the hover panel, including local IDR
    intl_rows = []
    for code, rate in currencies:
        converted = value / rate
        symbol = CURRENCY_SYMBOLS.get(code, code)
        flag = CURRENCY_FLAGS.get(code, '')
        if code == 'IDR':
            fmt = f'Rp {value:,.0f}'
        elif converted >= 1:
            fmt = f'{symbol}{converted:,.2f}'
        else:
            fmt = f'{symbol}{converted:,.4f}'
        intl_rows.append(
            f'<div class="pc-intl-row">'
            f'  <span class="pc-intl-flag">{flag}</span>'
            f'  <span class="pc-intl-code">{code}</span>'
            f'  <span class="pc-intl-val">{fmt}</span>'
            f'</div>'
        )
    hover_panel = (
        '<div class="pc-hover-reveal" aria-hidden="true">'
        '  <div class="pc-hover-head">'
        '    <div>'
        '      <div class="pc-hover-kicker">Auto Estimate</div>'
        '      <div class="pc-hover-title">Konversi Internasional</div>'
        '    </div>'
        '    <span class="pc-hover-badge">Live</span>'
        '  </div>'
        '  <div class="pc-hover-subtitle">Perbandingan kurs dibuat lebih jelas untuk bantu lihat estimasi harga dengan cepat.</div>'
        '  <div class="pc-intl-list">'
        + ''.join(intl_rows) +
        '  </div>'
        '  <div class="pc-hover-note"><i class="bi bi-info-circle"></i><span>Kurs bersifat estimasi dan dapat berubah saat pembayaran akhir.</span></div>'
        '</div>'
    )

    items = []
    for code, rate in currencies:
        converted = value / rate
        symbol = CURRENCY_SYMBOLS.get(code, code)
        short_flag = code[:2]

        if code == 'IDR':
            fmt = f'Rp {value:,.0f}'
        elif converted >= 1:
            fmt = f'{symbol}{converted:,.2f}'
        else:
            fmt = f'{symbol}{converted:,.4f}'

        active_class = 'region-price-active' if code == 'IDR' else 'region-price-hidden'

        items.append(
            f'<div class="price-chip region-price-chip {active_class}" data-currency="{code}" tabindex="0" role="button" aria-expanded="false">'
            f'  <div class="pc-inner">'
            f'    <div class="pc-flag-short">{short_flag}</div>'
            f'    <div class="pc-info">'
            f'      <span class="pc-code">{code}</span>'
            f'      <span class="pc-value">{fmt}</span>'
            f'    </div>'
            f'    <div class="pc-expand-icon"><i class="bi bi-chevron-down"></i></div>'
            f'  </div>'
            + hover_panel +
            f'</div>'
        )

    return mark_safe(
        '<div class="price-region-display">' + ''.join(items) + '</div>'
    )
