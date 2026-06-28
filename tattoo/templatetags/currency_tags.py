from django import template
from django.utils.safestring import mark_safe
from ..rates import get_exchange_rates, CURRENCY_SYMBOLS, CURRENCY_FLAGS, CURRENCY_DESCS

register = template.Library()


@register.filter
def get_item(d, key):
    return d.get(key)


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(is_safe=True)
def multi_currency(value):
    if value is None:
        return ''
    try:
        value = float(value)
    except (ValueError, TypeError):
        return ''
    rates = get_exchange_rates()
    parts = []
    for code in ['USD', 'EUR', 'SGD', 'AUD', 'RUB']:
        rate = rates.get(code)
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
    if value is None:
        return ''
    try:
        value = float(value)
    except (ValueError, TypeError):
        return ''
    rates = get_exchange_rates()

    currencies = [
        ('IDR', rates['IDR']),
        ('USD', rates['USD']),
        ('EUR', rates['EUR']),
        ('SGD', rates['SGD']),
        ('AUD', rates['AUD']),
        ('RUB', rates['RUB']),
    ]

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
