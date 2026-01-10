# main/templatetags/cart_extras.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(str(key))
