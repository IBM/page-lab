from django import template
from django.conf import settings

register = template.Library()

# settings value
@register.simple_tag(takes_context=True)
def highlight_nav_item(context, url):
    isMatch = False
    
    scriptPrefix = getattr(settings, "FORCE_SCRIPT_NAME", "")
    requestPath = context['request'].path
    thisPagePath = "%s%s%s" % (scriptPrefix, "/report/pages", url)
    
    if requestPath == thisPagePath:
        isMatch = True
    
    return isMatch
