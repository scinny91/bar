# bar/templatetags/dict_extras.py

from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key, 0)

@register.filter
def replace(value, args):
    old, new = args.split(",")
    return value.replace(old, new)