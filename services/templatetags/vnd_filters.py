from django import template

register = template.Library()


@register.filter
def vnd(value):
    try:
        number = int(value)
        formatted = f'{number:,}'.replace(',', '.')
        return f'{formatted} VND'
    except (ValueError, TypeError):
        return '0 VND'