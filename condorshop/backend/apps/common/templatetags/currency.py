from django import template

from apps.common.utils import format_clp

register = template.Library()


@register.filter(name="clp")
def clp(value):
    return format_clp(value)

