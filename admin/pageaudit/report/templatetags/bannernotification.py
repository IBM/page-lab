from django import template

from report.models import BannerNotification

register = template.Library()


##
##  Gets all active banners and displays them at page top, using the 'banner_notification.html' template.
##
@register.inclusion_tag("partials/banner_notification.html")
def bannerNotification():
    return {"banners": BannerNotification.objects.filter(active=True)}

