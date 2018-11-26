from django.conf.urls import url, include
from django.urls import path
from django.contrib.auth.views import logout
from django.views.generic import RedirectView, TemplateView

from .views import *

## URLS are from context of /report/ so don't include that in here.
## NAMESPACE for these URLS is "plr" (page-lab report). 
## So {% url 'plr:home' %} points to the "/report/" URL using "home" view
urlpatterns = [

    ## APIs.
    url(r'^api/urlid/$', api_urlid, name='api_urlid'),
    url(r'^api/lighthousedata/((?P<id>[\d-]+)/)?$', api_lighthouse_data, name='api_lighthouse_data'),
    url(r'^api/compareinfo/$', api_compareinfo, name='api_compareinfo'),
    url(r'^api/home/items/$', api_home_items, name='api_home_items'),
    url(r'^api/urltypeahead/$', api_url_typeahead, name='api_url_typeahead'),
    
    ## Core pages.
    url(r'^$', home, name='home'),
    url(r'^browse/(?P<filter_slug>\S+)?$', reports_browse, name='reports_browse'),
    url(r'^dashboard/(?P<filter_slug>\S+)?$', reports_dashboard, name='reports_dashboard'),
    url(r'^filters/$', reports_filters, name='reports_filters'),
    url(r'^urls/detail/(?P<id>[\d-]+)/$', reports_urls_detail, name='reports_urls_detail'),
    
    ## Compare page.
    ## First 2 IDs are required, 3rd is optional, more than 3 is wrong.
    ## I know this can be a regex to combine these but it's easier to read and maintain like this.
    url(r'^urls/compare/(?P<id1>[\d-]+)/(?P<id2>[\d-]+)/?$', reports_urls_compare, name='reports_urls_compare'),
    url(r'^urls/compare/(?P<id1>[\d-]+)/(?P<id2>[\d-]+)/(?P<id3>[\d-]+)/$', reports_urls_compare, name='reports_urls_compare'),
    url(r'^urls/compare/(?P<id1>[\d-]+)/(?P<id2>[\d-]+)/(?P<id3>[\d-]+)/(.*)', RedirectView.as_view(url=reverse_lazy('plr:home'))),
    
    ## Lighthouse report data viewer.
    url(r'^lighthouse-viewer/$', TemplateView.as_view(template_name='lighthouse-viewer.html'), name='report_lighthouse_viewer'),
    
    ## Standard across all apps.
    url(r'^signin/$', signin, name='signin'),
    url(r'^signout/$', logout, name='signout'),
    url(r'^signedout/$', signedout, name='signedout'),
    
    ## All flat pages served out of this dir.
    path('pages/', include('django.contrib.flatpages.urls')),
    
    ## Here for dev/testing in debug mode:
    url(r'^404$', custom_404),
    url(r'^500$', custom_500),
]
