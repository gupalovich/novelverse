from django import template

import re

register = template.Library()


@register.filter(name='ifinlist')
def ifinlist(value, list):
    return True if value in list else False


@register.filter(name='sliceintchar')
def sliceintchar(value):
    return re.split('([a-z]+)', str(value).strip())


@register.filter(name='htmlfree')
def htmlfree(html_text):
    regex = re.compile('<.*?>')
    cleantext = re.sub(regex, '', html_text)
    cleantext = '. '.join(cleantext.strip().split('.'))
    return cleantext
