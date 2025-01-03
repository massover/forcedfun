from django import template


register = template.Library()


@register.simple_tag(name="zip")
def zip_tag(x, y):  # type: ignore
    return zip(x, y)
