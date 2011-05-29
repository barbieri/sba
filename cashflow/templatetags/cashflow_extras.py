from django.conf import settings
from django import template

register = template.Library()

@register.filter()
def currency(value):
    thousand_sep = ''
    decimal_sep = ','
    try:
        thousand_sep = settings.THOUSAND_SEPARATOR
        decimal_sep = settings.DECIMAL_SEPARATOR
    except AttributeError:
        thousand_sep = '.'
        decimal_sep = ','

    if value < 0:
        sign = '-'
        value = -value
    else:
        sign = ''

    intpart = int(value)
    decpart = int((value - intpart) * 100)

    if intpart == 0:
        r = ["0"]
    else:
        r = []
        while intpart > 0:
            x = intpart % 1000
            intpart = int(intpart / 1000)
            if intpart > 0:
                r.insert(0, "%03d" % x)
            else:
                r.insert(0, str(x))

    intpart = thousand_sep.join(r)
    return "%s%s%s%02d" % (sign, intpart, decimal_sep, decpart)
