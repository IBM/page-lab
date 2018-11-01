"""pageaudit URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth.views import logout
from django.views.generic import RedirectView
from django.urls import reverse_lazy

handler404 = 'report.views.custom_404'
handler500 = 'report.views.custom_500'

from report.views import collect_report, get_urls

urlpatterns = [
    ## Django overall admin.
    url('admin/', admin.site.urls),
    
    ## Node URLs for running reports and posting them to us.
    url(r'^collect/report/$', collect_report, name='collect_report'),
    url(r'^queue/$', get_urls, name='get_urls'),

    ## Report app URLs namespace. All URLs are in reports/urls.py
    url(r'^report/', include(('report.urls', 'plr'))),

    ## Redirect /pagelab/ to real app home page.
    url(r'^(/)?$', RedirectView.as_view(url=reverse_lazy('plr:home'))),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

