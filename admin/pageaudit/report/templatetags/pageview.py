from django import template

from report.models import PageView

register = template.Library()

##
## On page template, increments the hit count to the URL, or creates it as 1.
##
@register.simple_tag(takes_context=True)
def trackPageView(context):
    request = context['request']
    
    try:
        pvObj = PageView.objects.get(url=request.path)
        pvObj.view_count = pvObj.view_count + 1
        pvObj.save()
    
    except Exception as ex:
        PageView.objects.create(
            url = request.path,
            view_count = 1
        )
    
    return ""
