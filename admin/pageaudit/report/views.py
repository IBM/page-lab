
import calendar
import json
import sys

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.mail import mail_admins, send_mail
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers import serialize
from django.core.validators import validate_email
from django.db.models import Avg, Max, Min, Q, Sum
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.crypto import get_random_string
from django.utils.text import capfirst
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.edit import CreateView, UpdateView, DeleteView


from pageaudit.settings import ADMINS_EMAIL_TO_SMS
from .helpers import *
from .models import LighthouseDataRaw, LighthouseRun, Url, UrlKpiAverage

ERROR = 'error'
SUCCESS = 'success'



########################################################################
########################################################################
##
##  WSRs for Node app
##
########################################################################
########################################################################


##
##  /collect/report/
##
##
@csrf_exempt
def collect_report(request):
    """
    Web service URL where Lighthouse report data is POST'd and saved in Django.
    """
    
    if request.method == 'GET':
        return HttpResponseNotAllowed('GET')
    elif request.method == 'POST':
        raw_report = request.body
        # import ipdb; ipdb.set_trace()
        if not raw_report:
            return JsonResponse({
                'status': ERROR,
                'message': 'Report value missing in request'
            })
        else:
            try:
                lhd = LighthouseDataRaw()
                lhd.save_report(raw_data=raw_report)
                
                return JsonResponse({
                    'status': SUCCESS,
                    'message': 'Report data accepted %s' % lhd.id
                })
            except Exception as ex:
                #print(str(ex))
                return JsonResponse({
                    'status': ERROR,
                    'message': str(ex)
                })


##
##  /queue/
##
##
def get_urls(request):
    """
    Web service URL to get a list of URLS to process by the Lighthouse test queue.
    Only URLs that are "active" are returned to be tested.
    """
    
    urls = []
    qs = Url.objects.allActive().order_by('id')
    
    for url in qs:
        urls.append({'url': url.url, 'id': url.id})
    
    return JsonResponse({
        'status': SUCCESS,
        'message': urls,
    })
            


########################################################################
########################################################################
##
##  APIs 
##
########################################################################
########################################################################


##
##  /api/lighthousedata/<id>/
##  
##  Get the Lighthouse report's raw data object for the given LighthouseRun ID.
##
##
def api_lighthouse_data(request, id):
    """
    Takes a given LighthouseRun ID and returns it's raw report data object.
    If none exists, returns empty results object.
    """
    
    lightouseData = {}
    
    try:
        lightouseData['rawData'] = LighthouseRun.objects.get(id=id).lighthouse_data_raw_lighthouse_run.get().report_data
    except Exception as ex:
        pass
    
    return JsonResponse({
        'results': lightouseData 
    })


##
##  /api/urltypeahead/?q=<search string>
##
##
def api_url_typeahead(request):
    """
    Takes a given string and returns 6 URLs that contain it.
    """
    
    textString = request.GET.get('q', '')
    
    urlList = []

    if textString != '':
        urlList = list(Url.objects.filter(url__contains=textString)[:6].values('id', 'url'))
    
    return JsonResponse({
        'results': urlList 
    })


##
##  /api/urlid/?url=<search string>
##
##
def api_urlid(request):
    """
    Takes a given URL and returns the ID. Used by home page search.
    When you type/select a URL, the ID is retrieved and sends you to that page.
    """
    
    url = request.GET.get('url', '')
    
    try:
        urlid = Url.objects.get(url=url).id
    except Exception as ex:
        urlid = None
    
    return JsonResponse({
        'results': { 'urlid': urlid } 
    })


##
##  /api/compareinfo/?id=<id>
##
##
def api_compareinfo(request):
    """
    Takes a given URL id and returns the info for it, used by the compare tray.
    """
    
    id = request.GET.get('id', '')
    html = None
    
    
    ## Get the URL via ID they requested.
    try:
        urlObj = Url.objects.prefetch_related("lighthouse_run").get(id=id)
    except Exception as ex:
        urlObj = None
    
    
    ## Create the HTML snippet.
    ## Firefox started rendering line returns as spaces so strip line returns.
    if urlObj:
        html = render_to_string('partials/compare_item.html', {'url':urlObj}).replace('\n','')
    
    
    ## Send it back to the requestor.
    return JsonResponse({
        'results': {
            'id': id,
            'resultsHtml': html
        } 
    })


##
##  /api/home/items/page/?<GET params>
##
##  Lazy loader.
##  Called by 'load more' button on bottom of page.
##
##
def api_home_items(request):
    """
    Used by home page "more" button at bottom.
    Gets 20 'more' report cards, with offset/pagination, and returns the cards HTML
    to inject at the bottom of the page.
    """
    
    urls = Url.getUrls({
        'sortby': request.GET.get('sortby'),
        'sortorder': request.GET.get('sortorder'),
    })
    
    
    page = request.GET.get('page')
    urlPaginator = Paginator(urls, 20) # Show 20 'cards' per request.
    urlsToShow = urlPaginator.get_page(page)
    viewData = request.GET.get('viewdata', 'perfscore')
    
    context = {
        'urls': urlsToShow,
        'viewdata': viewData
    }
    
    
    html = render_to_string('partials/home_load_items.html', context)
    
    return JsonResponse({
            'pageNum': urlsToShow.number,
            'hasNextPage': urlsToShow.has_next(),
            'resultsHtml': html
        })


##
##  /report/
##
##  Home page.
##
##
def home(request):
    """
    Site home page.
    """
    
    context = {}
    
    return render(request, 'home.html', context)


##
##  /report/browse/
##
##
def reports_browse(request):
    """
    Browse page showing list of report cards.
    """
    
    urls = Url.getUrls({
        'sortby': request.GET.get('sortby'),
        'sortorder': request.GET.get('sortorder'),
    })
    
    ## Pagination is AWESOME:  https://docs.djangoproject.com/en/2.0/topics/pagination/
    
    urlPaginator = Paginator(urls, 20) # Show 20 'cards' per request.
    page = request.GET.get('page')
    urlsToShow = urlPaginator.get_page(page)
    viewData = request.GET.get('viewdata', 'perfscore')
    
    context = {
        'urlPaginator': urlPaginator,
        'urls': urlsToShow,
        'sortby': request.GET.get('sortby', 'date'),
        'sortorder': request.GET.get('sortorder', 'desc'),
        'viewdata': viewData,
        'hasNextPage': urlsToShow.has_next(),
    }
    
    return render(request, 'reports_browse.html', context)


##
##  /report/dashboard/
##
##
def reports_dashboard(request):
    """
    High-level page that shows key averages and overview #s.
    """
    
    reportBuckets = {
        'fcp': {
            'fast': 1.6,
            'slow': 2.4
        },
        'fmp': {
            'fast': 2,
            'slow': 3
        },
        'tti': {
            'fast': 3,
            'slow': 4.5
        },
    }
    
    ## Vars here allow for easy future update to scope data to any set of URLs, instead of all.
    ## This way NONE OF THE THINGS IN "CONTEXT" need to be touched.
    ## Simple change the scope/queries of these two vars.
    urls = Url.objects.withValidRuns()
    urlKpiAverages = UrlKpiAverage.objects.all()
    
    ## Get a bunch of counts to chart.
    ## Nothing here should be changed unless we add a new data point to chart.
    context = {
        'urlCountTested': urls.count(),
        
        'urlGlobalPerfAvg': round(urlKpiAverages.aggregate(Avg('performance_score'))['performance_score__avg']) if UrlKpiAverage.objects.all().count() > 0 else 0,
        'urlGlobalA11yAvg': round(urlKpiAverages.aggregate(Avg('accessibility_score'))['accessibility_score__avg']) if UrlKpiAverage.objects.all().count() > 0 else 0,
        'urlGlobalSeoAvg': round(urlKpiAverages.aggregate(Avg('seo_score'))['seo_score__avg']) if UrlKpiAverage.objects.all().count() > 0 else 0,
        
        'urlPerfCountPoor': urls.filter(url_kpi_average__performance_score__gt = 5, url_kpi_average__performance_score__lte=GOOGLE_SCORE_SCALE['poor']['max']).count(),
        'urlPerfCountAvg': urls.filter(url_kpi_average__performance_score__gte=GOOGLE_SCORE_SCALE['average']['min'], url_kpi_average__performance_score__lte=GOOGLE_SCORE_SCALE['average']['max']).count(),
        'urlPerfCountGood': urls.filter(url_kpi_average__performance_score__gte=GOOGLE_SCORE_SCALE['good']['min']).count(),
        
        'urlFcpCountSlow': urls.filter(url_kpi_average__first_contentful_paint__gt=(reportBuckets['fcp']['slow']*1000)).count(),
        'urlFcpCountFast': urls.filter(url_kpi_average__first_contentful_paint__lt=(reportBuckets['fcp']['fast']*1000)).count(),
        'urlFcpCountAvg': urls.filter(url_kpi_average__first_contentful_paint__gte=(reportBuckets['fcp']['fast']*1000), url_kpi_average__first_contentful_paint__lte=(reportBuckets['fcp']['slow']*1000)).count(),

        'urlFmpCountSlow': urls.filter(url_kpi_average__first_meaningful_paint__gt=(reportBuckets['fmp']['slow']*1000)).count(),
        'urlFmpCountFast': urls.filter(url_kpi_average__first_meaningful_paint__lt=(reportBuckets['fmp']['fast']*1000)).count(),
        'urlFmpCountAvg': urls.filter(url_kpi_average__first_meaningful_paint__gte=(reportBuckets['fmp']['fast']*1000), url_kpi_average__first_meaningful_paint__lte=(reportBuckets['fmp']['slow']*1000)).count(),

        'urlFiCountSlow': urls.filter(url_kpi_average__interactive__gt=(reportBuckets['tti']['slow']*1000)).count(),
        'urlFiCountFast': urls.filter(url_kpi_average__interactive__lt=(reportBuckets['tti']['fast']*1000)).count(),
        'urlFiCountAvg': urls.filter(url_kpi_average__interactive__gte=(reportBuckets['tti']['fast']*1000), url_kpi_average__interactive__lte=(reportBuckets['tti']['slow']*1000)).count(),
   }
    
    return render(request, 'reports_dashboard.html', context)


##
##  /report/urls/compare/<id1>/<id2>/<id3>?/
##
##  Compares 2 (required) or optional 3rd URL report side-by-side.
##
##
def reports_urls_compare(request, id1, id2, id3=None):
    """
    Compares average scores and timings in a data table, for either 2 or 3 URLs.
    """
    
    try:
        url1 = Url.objects.prefetch_related("lighthouse_run").prefetch_related("url_kpi_average").get(id=id1)
        url2 = Url.objects.prefetch_related("lighthouse_run").prefetch_related("url_kpi_average").get(id=id2)
    except:
        return redirect(reverse('plr:home'))


    ## 3rd URL to compare with is optional.
    url3 = None
    if id3:
        try:
            url3 = Url.objects.prefetch_related("lighthouse_run").prefetch_related("url_kpi_average").get(id=id3)
        except:
            return redirect(reverse('plr:home'))

    context = {
        'url1': url1,
        'url2': url2,
        'url3': url3,       
    }
    
    return render(request, 'reports_urls_compare.html', context)


##
##  /report/urls/detail/<id>/
##
##  Report detail for a given URL, include run history.
##
##
def reports_urls_detail(request, id):
    """
    URL report detail page for given URL ID. Shows charts, scores, averages and 
    key data from each lighthouse run in a table.
    """
    
    try:
        url1 = Url.objects.get(id=id)
    except:
        return redirect(reverse('plr:home'))
    
    ## Get all runs for this URL
    urlLighthouseRuns = LighthouseRun.objects.filter(url=url1)

    ## Setup arrays of data for the line chart.
    ## Each object is an array that is simply passed to D3 and each represents a line on the chart.
    lineChartData = {
        'dates': ['x'],
        'perfScores': ['Performance score'],
        'a11yScores': ['Accessibility score'],
        'seoScores': ['SEO score'],
    }
    
    ## Get list of field values as array data and add to our arrays setup above for each line.
    lhRunsPerfScores = urlLighthouseRuns.values_list('performance_score', flat=True)
    lhRunsA11yScores = urlLighthouseRuns.values_list('accessibility_score', flat=True)
    lhRunsSeoScores = urlLighthouseRuns.values_list('seo_score', flat=True)
    
    ## Add the data values array for each line we want to chart.
    lineChartData['perfScores'].extend(list(lhRunsPerfScores))
    lineChartData['a11yScores'].extend(list(lhRunsA11yScores))
    lineChartData['seoScores'].extend(list(lhRunsSeoScores))
    
    ## Add dates, formatted, as x-axis array data.
    for runData in urlLighthouseRuns:
        lineChartData['dates'].append(runData.created_date.strftime('%d-%m-%Y'))
        
    context = {
        'url1': url1,
        'lighthouseRuns': urlLighthouseRuns,
        'lineChartData': lineChartData,
    }
    
    
    if urlLighthouseRuns.count() > 1:
        return render(request, 'reports_urls_detail_withruns.html', context)
    else:
        return render(request, 'reports_urls_detail_noruns.html', context)


##
##  /report/signin/
##
##  Sign in page.
##
##
def signin(request):
    """
    Custom/nice sign in page instead of Django admin/default sign-in page.
    """
    
    ## If user is already signed in they don't need to be here, so redirect them to home page.
    if request.user.is_authenticated:
        response = redirect(reverse('plr:home'))

    ## GET = They need to see the sign-in form.
    ## POST = They are trying to sign in.
    
    elif request.method == 'GET':
        response = render(request, 'signin.html', {
            'form': AuthenticationForm,
        })
    
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        try:
            user = authenticate(request, username=username, password=password)
        except Exception as ex:
            context = {
                'form': AuthenticationForm,
                'error': 'Uh oh, we were unable to authenticate you. Check your user name and password and try again.',
            }
            
            return render(request, 'signin.html', context)
        
        ## User exists.
        if user is not None:
            login(request, user)
            response = redirect(reverse('plr:home'))
        
        ## User doesn't exists and auth model wasn't able to create new user.
        else:
            context = {
                'form': AuthenticationForm,
                'error': 'Woops! It looks like you are not a valid user in the system. Contact an admin.',
            }
            
            response = render(request, 'signin.html', context)
    
    ## Return whatever response was set.
    return response


##
##  /report/signedout/
##
##  Signed out page.
##
##  Page that shows AFTER you have successfully signed out.
##
##
def signedout(request):
    """
    'Success' page that simply confirms that the user has been signed out successfully.
    """
    
    return render(request, 'signedout.html')


##
##  Custom 404 error
##
##  Sends Slack room hook notification and sends email to admins.
##
##
def custom_404(request, exception=None):
    """
    Custom, 'nice' 404 page. If DJANGO_SLACK_ALERT_URL variable is setup in 
    settings with Slack room hook URL, it will send Slack room message, 
    but only if referrer is from the site (aka a broken link).
    """
    
    referer = request.META.get('HTTP_REFERER', 'None')
    
    if referer != 'None':
        sendSlackAlert('404', '*Requested path:*  ' + request.path + '\n*Referring page:*  ' + referer)
    
    context = {
        ## none yet
    }
    
    return render(request, '404.html', context, status=404)
    
      
##
##  Custom 500 error
##
##  Sends Slack room hook notification and sends email to admins.
##
##
def custom_500(request):
    """
    Custom, 'nice' 500 page. If DJANGO_SLACK_ALERT_URL variable is setup in 
    settings with Slack room hook URL, it will send Slack room message.
    If ADMINS_EMAIL_TO_SMS array of emails is setup in settings, it will send
    you SMS text message via carrier's email-to-text email feature.
    """
    
    exctype, value = sys.exc_info()[:2]
    
    errMsg = value or '(No error provided)'
    errMsg = str(errMsg)
    
    ## Admins automatically get an email on a 500 error when ADMINS email array is setup in settings.py.
    ## Here we want to ALSO send an instant message (because 500 is kinda a big deal),
    ##  via Slack and SMS to the admins.
    sendSlackAlert('500', '*Requested path:*  %s\n*Error msg:*  %s\nCheck email for full debug.' % (request.path, errMsg))
    sendEmailNotification(ADMINS_EMAIL_TO_SMS, 'A 500 occurred', errMsg)
    
    context = {
        ## none yet
    }
    
    return render(request, '500.html', context, status=500)
    

