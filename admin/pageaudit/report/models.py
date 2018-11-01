import json

from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Avg, Max, Min, Q, Sum
from collections import namedtuple

from .helpers import *


## Custom Url object filters mapped to functions.
## These are chainable preset filters instead of using .all or .filter() all the time
class UrlQueryset(models.QuerySet):
    """
        Gets all active URLs to run.
        USAGE:
            Url.objects.allActive()
    """
    def allActive(self):
        return self.filter(inactive=False)

class UrlManger(models.Manager):
    def get_queryset(self):
        return UrlQueryset(self.model, using=self._db)  ## IMPORTANT KEY ITEM.

    def allActive(self):
        return self.get_queryset().allActive()


class LighthouseRun(models.Model):
    """
    Main pointer for a lighthouse run. Each run for a URL creates one of these with
    relationship to the URL it was for. That way we can get averages for all Runs assoc. with a given URL.
    And the URL has a relationship to the Run that's the 'latest'.
    """
    created_date = models.DateTimeField(auto_now_add=True)
    url = models.ForeignKey('Url',
                            related_name='lighthouse_run_url',
                            on_delete=models.CASCADE)
    
    invalid_run = models.BooleanField(default=False)
    http_error_code = models.PositiveIntegerField(blank=True, null=True)
    lighthouse_error_code = models.CharField(max_length=255, blank=True, null=True)
    lighthouse_error_msg = models.TextField(blank=True, null=True)
      
    ## KPIs go in here for quick, single relationship query and sorting from parent URL.
    ## This is like the ledger line for a run, containing quick-accessable fields we need.
    ## Shit is WAY faster with this here now.
    
    ## Scores
    accessibility_score = models.PositiveIntegerField(default=0)
    performance_score = models.PositiveIntegerField(default=0)
    seo_score = models.PositiveIntegerField(default=0)
    
    ## KPIs
    dom_content_loaded = models.PositiveIntegerField(default=0)
    dom_loaded = models.PositiveIntegerField(default=0)
    first_contentful_paint = models.PositiveIntegerField(default=0)
    first_meaningful_paint = models.PositiveIntegerField(default=0)
    interactive = models.PositiveIntegerField(default=0)
    number_network_requests = models.PositiveIntegerField(default=0)
    redirect_hops = models.PositiveIntegerField(default=0)
    redirect_wasted_ms = models.PositiveIntegerField(default=0)
    seo_score = models.PositiveIntegerField(default=0)
    thumbnail_image = models.TextField(blank=True, null=True)
    time_to_first_byte = models.PositiveIntegerField(default=0)
    total_byte_weight = models.PositiveIntegerField(default=0)
    
    ## REMOVE THIS after new user-timing models are POPULATED WITH THE DATA.
    masthead_onscreen = models.PositiveIntegerField(default=0)

    
    class Meta:
        ordering = ['-created_date']
        
    def __str__(self):
        return 'perf: %s - requests: %s' % (self.performance_score, self.number_network_requests,)


class Url(models.Model):
    """
    A Url to test!
    """
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,
                                   related_name='url_created_by',
                                   on_delete=models.PROTECT)
    edited_date = models.DateTimeField(auto_now=True)
    edited_by = models.ForeignKey(User,
                                  related_name='url_edited_by',
                                  on_delete=models.PROTECT)

    url = models.URLField(unique=True)
    lighthouse_run = models.ForeignKey('LighthouseRun',
                                        related_name='url_lighthouse_run',
                                        on_delete=models.SET_NULL,
                                        null=True, blank=True)
    url_kpi_average = models.ForeignKey('UrlKpiAverage',
                                        related_name='url_url_kpi_average',
                                        on_delete=models.SET_NULL,
                                        null=True, blank=True)
    inactive = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=0)
    
    user_timings_migrated = models.DateTimeField(null=True)
    
    ## Sets up custom queries at top.
    objects = UrlManger()

    
    class Meta:
        ordering = ['url']
    
    def __str__(self):
        return "%s" % (self.url,)
    
    def getUrls(options):
        allowedSortby = {
            "url": "url",
            "date": "lighthouse_run__created_date",
            "a11yscore": "url_kpi_average__accessibility_score",
            "perfscore": "url_kpi_average__performance_score",
            "seoscore": "url_kpi_average__seo_score",
        }
        
        defSortby = "date"
        defSortorder = "-"
        defFilter = None

        ## Sort by.
        try:
            userSortby = options['sortby']
        except Exception as ex:
            userSortby = defSortby

        ## Map sortby field to proper query filter condition.
        try:
            querySortby = allowedSortby[userSortby]
        except Exception as ex:
            querySortby = allowedSortby[defSortby]
        
        
        ## Sort order
        try:
            userSortorder = options['sortorder']
        except Exception as ex:
            userSortorder = defSortorder

        ## Map sortorder field to proper query filter condition.
        querySortorder = "" if userSortorder == "asc" else defSortorder
        
        return Url().haveValidRuns().prefetch_related("lighthouse_run").prefetch_related("url_kpi_average").order_by(querySortorder + querySortby)
    
    def getKpiAverages(self):
        try:
            return UrlKpiAverage.objects.get(url=self)
        except Exception as ex:
            row = {
                'accessibility_score': 0,
                'dom_content_loaded': 0,
                'first_contentful_paint': 0,
                'first_meaningful_paint': 0,
                'interactive': 0,
                'dom_loaded': 0,
                'masthead_onscreen': 0,
                'number_network_requests': 0,
                'performance_score': 0,
                'redirect_wasted_ms': 0,
                'time_to_first_byte': 0,
                'total_byte_weight': 0,
            }
            
            return namedtuple('RowObject', row.keys())(*row.values())
    
    def haveValidRuns(self):
        return Url.objects.filter(lighthouse_run__isnull=False, lighthouse_run__number_network_requests__gt=1, lighthouse_run__performance_score__gt=5, lighthouse_run__invalid_run=False)


class UserTimingMeasureName(models.Model):
    """
    A user-timing measure name. Used as name pointer for timing measures.
    Allows for easy global average calculation and prevents massive duplication of timing mark names across every run.
    """
    created_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    

    class Meta:
        ordering = ['name']

    def __str__(self):
        return '%s' % (self.name,)


class UserTimingMeasure(models.Model):
    """
    A user-timing measure extracted from the related lighthouse run.
    Dynamically generated on LHRawData save, by simply looping thru the user-timing object.
    """
    created_date = models.DateTimeField(auto_now_add=True)
    lighthouse_run = models.ForeignKey('LighthouseRun',
                            related_name='user_timing_measure_lighthouse_run',
                            on_delete=models.CASCADE)
    url = models.ForeignKey('Url',
                            related_name='user_timing_measure_url',
                            on_delete=models.CASCADE)
    name = models.ForeignKey('UserTimingMeasureName',
                            related_name='user_timing_measure_name',
                            on_delete=models.CASCADE)
    duration = models.PositiveIntegerField(default=0)
    start_time = models.PositiveIntegerField(default=0)
    

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return '%s : %s' % (self.name, self.duration)
    

class UserTimingMeasureAverage(models.Model):
    """
    The average of a particular user-timing for a particular URL
    Dynamically generated on LHRawData save, by simply averaging all the 
    same user-timings for the given URL
    """
    created_date = models.DateTimeField(auto_now_add=True)
    url = models.ForeignKey('Url',
                            related_name='user_timing_measure_avg_url',
                            on_delete=models.CASCADE)
    name = models.ForeignKey('UserTimingMeasureName',
                            related_name='user_timing_measure_avg_name',
                            on_delete=models.CASCADE)
    duration = models.PositiveIntegerField(default=0)
    start_time = models.PositiveIntegerField(default=0)
    number_samples = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return '%s : %s' % (self.name, self.duration)


class UrlKpiAverage(models.Model):
    """
    Running average of KPIs, created on save of Raw Data module, just like cache Run is.
    """
    created_date = models.DateTimeField(auto_now_add=True)
    url = models.ForeignKey('Url',
                            related_name='url_kpi_average_url',
                            on_delete=models.CASCADE)
    
    number_samples = models.PositiveIntegerField(default=0)
    invalid_average = models.BooleanField(default=False)
    
    ## Scores
    accessibility_score = models.PositiveIntegerField(default=0)
    performance_score = models.PositiveIntegerField(default=0)
    seo_score = models.PositiveIntegerField(default=0)
    
    ## KPIs
    dom_content_loaded = models.PositiveIntegerField(default=0)
    dom_loaded = models.PositiveIntegerField(default=0)
    first_contentful_paint = models.PositiveIntegerField(default=0)
    first_meaningful_paint = models.PositiveIntegerField(default=0)
    interactive = models.PositiveIntegerField(default=0)
    number_network_requests = models.PositiveIntegerField(default=0)
    redirect_hops = models.PositiveIntegerField(default=0)
    redirect_wasted_ms = models.PositiveIntegerField(default=0)
    seo_score = models.PositiveIntegerField(default=0)
    time_to_first_byte = models.PositiveIntegerField(default=0)
    total_byte_weight = models.PositiveIntegerField(default=0)
    
    ## REMOVE THIS after new user-timing models are POPULATED WITH THE DATA.
    masthead_onscreen = models.PositiveIntegerField(default=0)

    
    
    def __str__(self):
        return '%s' % (self.url.url,)


## FUTURE USE:
# class LighthouseConfig(models.Model):
#     """
#     Stores various config settings to use when running lighthouse tests.
#     """
#     created_date = models.DateTimeField(auto_now_add=True)
#     created_by = models.ForeignKey(User,
#                                    related_name='lighthouse_config_created_by',
#                                    on_delete=models.PROTECT)
#     edited_date = models.DateTimeField(auto_now=True)
#     edited_by = models.ForeignKey(User,
#                                   related_name='lighthouse_config_edited_by',
#                                   on_delete=models.PROTECT)
#     default_config = models.BooleanField(default=False)
#     rtt_ms = models.PositiveIntegerField(default=0)
#     latency_ms = models.PositiveIntegerField(default=0)
#     throughput_kbps = models.PositiveIntegerField(default=0)
#     download_throughput_kbps = models.PositiveIntegerField(default=0)
#     upload_throughput_kbps = models.PositiveIntegerField(default=0)
#     cpu_slowdown_multiplier = models.PositiveIntegerField(default=0)
#     mobile_device_emulation = models.BooleanField(default=True)
# 
# 
#     def save(self, *args, **kwargs):
#         if self.default_config:
#             try:
#                 existingDefault = LighthouseConfig.objects.get(default_config=True)
#                 if self != existingDefault:
#                     raise Exception("There is already a default config selected. You must unselect it first.")
#             except Character.DoesNotExist:
#                 pass
#         
#         # Call the "real" save method.
#         super().save(*args, **kwargs)
#         

class LighthouseDataRaw(models.Model):
    """
    The raw data as collected from Lighthouse
    """
    created_date = models.DateTimeField(auto_now_add=True)
    lighthouse_run = models.ForeignKey('LighthouseRun',
                            related_name='lighthouse_data_raw_lighthouse_run',
                            on_delete=models.PROTECT)
    report_data = JSONField()

    
    class Meta:
        verbose_name_plural = "Lighthouse data raw"
    
    def __str__(self):
        return "%s - %s" % (self.lighthouse_run, self.created_date,)
    
    def save_report(self, raw_data):
        """
        Save the posted report data to the database

        """
        raw_report = json.loads(raw_data.decode('utf-8'))

        ## Set the raw data JSON and get the URL object so we can
        ##  process and create all the other models.
        report_data = json.loads(raw_report['report'])
        url = Url.objects.get(url=report_data['requestedUrl'])


        ## 1. Create this new LighthouseRun object (the main pointer/parent).
        this_run = LighthouseRun(url=url)
        this_run.save()


        ## 2. Change the Url object to point to this Run as the new/latest one.
        ##    (ALA: GDPR app->import_data)
        url.lighthouse_run = this_run
        url.save()


        ## 3. Create this raw data object and point to the Run it's associated with (created in #2)
        lighthouse_data_raw = LighthouseDataRaw(lighthouse_run=this_run,
                                                report_data=report_data,)
        lighthouse_data_raw.save()


        ## 4. Now grab the key fields we want and add them to the LighthouseRun for fast, single query.
        try:
            accessibility_score = int(report_data['categories']['accessibility']['score'] * 100)
            if accessibility_score is None:
                accessibility_score = 0
        except Exception as ex:
            accessibility_score = 0

        try:
            performance_score = int(report_data['categories']['performance']['score'] * 100)
            if performance_score is None:
                performance_score = 0
        except Exception as ex:
            performance_score = 0

        try:
            seo_score = int(report_data['categories']['seo']['score'] * 100)
            if seo_score is None:
                seo_score = 0
        except Exception as ex:
            seo_score = 0

        try:
            total_byte_weight = report_data['audits']['total-byte-weight']['rawValue']
            if total_byte_weight is None:
                total_byte_weight = 0
        except Exception as ex:
            total_byte_weight = 0

        try:
            number_network_requests = report_data['audits']['network-requests']['rawValue']
            if number_network_requests is None:
                number_network_requests = 0
        except Exception as ex:
            number_network_requests = 0

        try:
            time_to_first_byte = report_data['audits']['time-to-first-byte']['rawValue']
            if time_to_first_byte is None:
                time_to_first_byte = 0
        except Exception as ex:
            time_to_first_byte = 0

        try:
            first_meaningful_paint = report_data['audits']['first-meaningful-paint']['rawValue']
            if first_meaningful_paint is None:
                first_meaningful_paint = 0
        except Exception as ex:
            first_meaningful_paint = 0

        try:
            first_contentful_paint = report_data['audits']['first-contentful-paint']['rawValue']
            if first_contentful_paint is None:
                first_contentful_paint = 0
        except Exception as ex:
            first_contentful_paint = 0

        try:
            interactive = report_data['audits']['interactive']['rawValue']
            if interactive is None:
                interactive = 0
        except Exception as ex:
            interactive = 0

        try:
            thumbnail = report_data['audits']['screenshot-thumbnails']['details']['items'][-1]['data']
            if thumbnail is None:
                thumbnail = 0
        except Exception as ex:
            thumbnail = ""      
        
        try:
            dom_content_loaded = report_data['audits']['metrics']['details']['items'][0]['observedDomContentLoaded']
            if dom_content_loaded is None:
                dom_content_loaded = 0
        except Exception as ex:
            dom_content_loaded = 0

        try:
            dom_loaded = report_data['audits']['metrics']['details']['items'][0]['observedLoad']
            if dom_loaded is None:
                dom_loaded = 0
        except Exception as ex:
            dom_loaded = 0

        try:
            redirect_hops = len(report_data['audits']['redirects']['details']['items'])
            if redirect_hops is None:
                redirect_hops = 0
        except Exception as ex:
            redirect_hops = 0

        try:
            redirect_wasted_ms = report_data['audits']['redirects']['rawValue']
            if redirect_wasted_ms is None:
                redirect_wasted_ms = 0
        except Exception as ex:
            redirect_wasted_ms = 0


        mastheadOnscreen = getUserTimingValue("V18-masthead-load", userTimingsObject=report_data['audits']['user-timings'])
        
        ## We only do it this way because we already have this run in memory.
        ## Otherwise we would use: LighthouseRun...filter().update(...) as it's fastest in Django
        this_run.accessibility_score = accessibility_score
        this_run.performance_score = performance_score
        this_run.seo_score = seo_score
        this_run.total_byte_weight = total_byte_weight
        this_run.number_network_requests = number_network_requests
        this_run.time_to_first_byte = time_to_first_byte
        this_run.first_contentful_paint = first_contentful_paint
        this_run.first_meaningful_paint = first_meaningful_paint
        this_run.interactive = interactive
        this_run.masthead_onscreen = mastheadOnscreen['startTime']
        this_run.thumbnail_image = thumbnail
        this_run.redirect_wasted_ms = redirect_wasted_ms
        this_run.redirect_hops = redirect_hops
        this_run.dom_content_loaded = dom_content_loaded
        this_run.dom_loaded = dom_loaded
        
        ## Check if the initial request was a 4xx or 5xx, and set run as invalid.
        try:
            statusCode = report_data['audits']['network-requests']['details']['items'][0]['statusCode']
            if statusCode > 399:
                this_run.invalid_run = True
                this_run.http_error_code = statusCode
        except Exception as ex:
            pass
        
        ## Save the run object with populated fields.
        this_run.save()
        
        
        ## 5. Get/Create the average model object and re-calc new averages including the run we just saved.
        urlRuns = LighthouseRun.objects.filter(url=url, performance_score__gt=5, number_network_requests__gt=1, invalid_run=False)
        
        ## Seo is new, so only get average using runs that have it (>0), and for safety, set to 0 if there are none.
        urlRunsWithSeoScore = urlRuns.filter(seo_score__gt=0)
        try:
            seoAvg = round(urlRunsWithSeoScore.aggregate(Avg('seo_score'))['seo_score__avg'])
        except Exception as ex:
            seoAvg = 0
        
        urlAvg, created = UrlKpiAverage.objects.get_or_create(url=url)
        
        urlAvg.accessibility_score = round(urlRuns.aggregate(Avg('accessibility_score'))['accessibility_score__avg'])
        urlAvg.first_contentful_paint = round(urlRuns.aggregate(Avg('first_contentful_paint'))['first_contentful_paint__avg'])
        urlAvg.first_meaningful_paint = round(urlRuns.aggregate(Avg('first_meaningful_paint'))['first_meaningful_paint__avg'])
        urlAvg.interactive = round(urlRuns.aggregate(Avg('interactive'))['interactive__avg'])
        urlAvg.masthead_onscreen = round(urlRuns.aggregate(Avg('masthead_onscreen'))['masthead_onscreen__avg'])
        urlAvg.number_network_requests = round(urlRuns.aggregate(Avg('number_network_requests'))['number_network_requests__avg'])
        urlAvg.performance_score = round(urlRuns.aggregate(Avg('performance_score'))['performance_score__avg'])
        urlAvg.seo_score = seoAvg
        urlAvg.time_to_first_byte = round(urlRuns.aggregate(Avg('time_to_first_byte'))['time_to_first_byte__avg'])
        urlAvg.total_byte_weight = round(urlRuns.aggregate(Avg('total_byte_weight'))['total_byte_weight__avg'])  
        urlAvg.dom_content_loaded = round(urlRuns.aggregate(Avg('dom_content_loaded'))['dom_content_loaded__avg'])
        urlAvg.dom_loaded = round(urlRuns.aggregate(Avg('dom_loaded'))['dom_loaded__avg'])
        urlAvg.redirect_wasted_ms = round(urlRuns.aggregate(Avg('redirect_wasted_ms'))['redirect_wasted_ms__avg'])
        urlAvg.number_samples = urlRuns.count()
        urlAvg.save()
        
        ## Associate the URL to the average object for it.
        url.url_kpi_average = urlAvg
        url.save()


        ## 6. Now save the user timing section fields to it's model.
        reportUsertiming = LighthouseDataUsertiming(
            lighthouse_run = this_run,
            report_data = {'items': report_data['audits']['user-timings']['details']['items']},
        )
        reportUsertiming.save()

        
        ## Will replace #6 after all data is populated:
        ## 7. Loop thru the user timings object and create an entry for each one for this run.
        for item in report_data['audits']['user-timings']['details']['items']:
            if item['timingType'] == "Measure":
                itemName, created = UserTimingMeasureName.objects.get_or_create(name=item['name'])
                
                if item['startTime'] < 0:
                    continue
                    
                try:
                    UserTimingMeasure.objects.create(
                        url = url,
                        lighthouse_run = this_run,
                        name = itemName,
                        start_time = item['startTime'],
                        duration = item['duration'],
                    )
                except Exception as ex:
                    ## should log this when logging is setup.
                    pass
                    
                ## Now re-calculate the average for this user-timing item, FOR THIS URL.
                urlItemMeasures = UserTimingMeasure.objects.filter(url=url, name=itemName)
                
                itemDurationAvg = round(urlItemMeasures.aggregate(Avg('duration'))['duration__avg'])
                itemStartTimeAvg = round(urlItemMeasures.aggregate(Avg('start_time'))['start_time__avg'])
                
                ## Find or create an Avg record for the user-timing for this URL, then store the new avg #s.
                itemAvgObj, created = UserTimingMeasureAverage.objects.get_or_create(url=url, name=itemName)
                itemAvgObj.duration = itemDurationAvg
                itemAvgObj.start_time = itemStartTimeAvg
                itemAvgObj.number_samples += 1
                itemAvgObj.save()
                
                
    def __str__(self):
        return "%s - %s" % (self.lighthouse_run, self.created_date,)


class LighthouseDataUsertiming(models.Model):
    """
    Specific fields used as key performance indicators.
    """
    created_date = models.DateTimeField(auto_now_add=True)
    lighthouse_run = models.ForeignKey('LighthouseRun',
                            related_name='lighthouse_data_usertiming_lighthouse_run',
                            on_delete=models.PROTECT)
    report_data = JSONField()

    
    def __str__(self):
        return "%s - %s" % (self.lighthouse_run, self.created_date,)


class BannerNotification(models.Model):
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    banner_text = models.CharField(max_length=255)
    banner_type = models.CharField(default="info", choices=[
        ("info","info"),
        ("warn","warn"),
        ("alert","alert"),
    ], max_length=20)

    
    class Meta:
        ordering = ['active','name']
    
    def __str__(self):
        return "%s - %s - %s" % (self.name, self.banner_type, self.active)


class PageView(models.Model):
    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    modified_date = models.DateTimeField(auto_now=True, editable=False)
    url = models.CharField(max_length=2000, unique=True)
    view_count = models.PositiveIntegerField(default=0)


    class Meta:
        ordering = ['-view_count']
    
    def __str__(self):
        return "%s : %s" % (self.view_count, self.url)


