import json
from urllib import parse

from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Avg, Max, Min, Q, Sum, F
from collections import namedtuple

from .helpers import *


## Custom Url object filters mapped to functions.
## These are chainable preset filters instead of using .all or .filter() all the time

##
## URL preset chainable queries.
##
class UrlQueryset(models.QuerySet):
    """
    Get all URLs that are set to 'active'. Omits 'inactive' URLs.
    Usage:
        Url.objects.allActive()

    Get all URLs that have at least 1 valid run.
    No runs == no averages, and it would show improper percentages.
    Usage:
        Url.objects.withValidRuns()
    """

    def allActive(self):
        return self.filter(inactive=False)

    def withValidRuns(self):
        return self.filter(lighthouse_run__isnull=False, lighthouse_run__number_network_requests__gt=1, lighthouse_run__performance_score__gt=5, lighthouse_run__invalid_run=False)

class UrlManger(models.Manager):
    def get_queryset(self):
        return UrlQueryset(self.model, using=self._db)  ## IMPORTANT KEY ITEM.

    def allActive(self):
        return self.get_queryset().allActive()

    def withValidRuns(self):
        return self.get_queryset().withValidRuns()


##
## LighthouseRun preset chainable queries.
##
class LighthouseRunQueryset(models.QuerySet):
    """
    Filter out runs that are invalid.
    Usage:
        LighthouseRun.objects.validRuns()
    """

    def validRuns(self):
        return self.filter(number_network_requests__gt=1, performance_score__gt=5, invalid_run=False)

class LighthouseRunManger(models.Manager):
    def get_queryset(self):
        return LighthouseRunQueryset(self.model, using=self._db)  ## IMPORTANT KEY ITEM.

    def validRuns(self):
        return self.get_queryset().validRuns()


class LighthouseRun(models.Model):
    """
    Main pointer for a lighthouse run. Each run for a URL creates one of these with
    relationship to the URL it was for. Allows you to get averages for all runs
    associated with a given URL.
    The Url.object has a specific relationship to it's latest LighthouseRun.
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

    ## Sets up custom queries at top.
    objects = LighthouseRunManger()

    class Meta:
        ordering = ['-created_date']

        indexes = [
            models.Index(fields=['created_date',]),
            models.Index(fields=['url',]),
        ]

    def __str__(self):
        return 'perf: %s - requests: %s' % (self.performance_score, self.number_network_requests,)


class UrlOwner(models.Model):
    """
    An owner entity of a url: department, company, team.
    """

    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    modified_date = models.DateTimeField(auto_now=True, editable=False)
    owner_name = models.CharField(max_length=64)
    owner_email = models.EmailField(blank=True, null=True)
    owner_description = models.TextField(null=True, blank=True)
    owner_homepage = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['owner_name',]

    def __str__(self):
        return "%s" % (self.owner_name,)


class Url(models.Model):
    """
    A Url to test.
    Points to it's latest LighthouseRun and UrlKpiAverage object.
    It can be set to 'inactive' so it can be kept, but not currently tested,
    and is split into parts for URL report filtering/search capabilities.
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
                                       null=True,
                                       blank=True)
    url_kpi_average = models.ForeignKey('UrlKpiAverage',
                                        related_name='url_url_kpi_average',
                                        on_delete=models.SET_NULL,
                                        null=True,
                                        blank=True)
    inactive = models.BooleanField(default=False)
    sequence = models.PositiveIntegerField(default=0)
    owner = models.ForeignKey(UrlOwner,
                              related_name='url_owner_url',
                              on_delete=models.SET_NULL,
                              null=True,
                              blank=True)

    # based on https://developer.mozilla.org/en-US/docs/Web/API/Location
    protocol = models.CharField(max_length=8, blank=True)
    host = models.CharField(max_length=255, blank=True)
    hostname = models.CharField(max_length=255, blank=True)
    port = models.IntegerField(default=None, null=True, blank=True)
    pathname = models.CharField(max_length=255, null=True, blank=True)
    search = models.CharField(max_length=255, null=True, blank=True)
    hash = models.CharField(max_length=255, null=True, blank=True)
    # Note: not supporting username password as we don't want to persist
    # that data in the database
    origin = models.CharField(max_length=255, blank=True)
    parsed_url = models.URLField(blank=True)

    url_paths = models.ManyToManyField('UrlPath', blank=True)
    search_key_vals = models.ManyToManyField('SearchKeyVal', blank=True)
    
    ## Sets up custom queries at top.
    objects = UrlManger()

    class Meta:
        ordering = ['url']

        indexes = [
            models.Index(fields=['url',]),
        ]

    def __str__(self):
        return "%s" % (self.url,)

    def save(self, *args, **kwargs):
        """
        Override save to populate the location data.
        """
        if self.url != self.parsed_url:
            # We parse the url and save each location bit
            loc = parse.urlparse(self.url)
            self.protocol = loc.scheme
            self.host = loc.netloc
            self.hostname = loc.hostname
            self.port = loc.port
            self.pathname = loc.path
            self.search = loc.query
            self.hash = loc.fragment
            self.origin = '%s://%s' % (loc.scheme, loc.netloc,)
            self.parsed_url = self.url

            super(Url, self).save(*args, **kwargs) # save this now
            # replace any existing SearchKeyVal and UrlPath objects in m2m
            self.url_paths.all().delete()
            self.search_key_vals.all().delete()
            # now re-save them
            pathSegments = loc.path.split('/')
            i = 0
            for seg in pathSegments:
                if seg is not '':
                    path = UrlPath.objects.create(sequence=i, path=seg)
                    self.url_paths.add(path)
                    i = i + 1
            self.save() # save added m2m records

            for query in loc.query.split('&'):
                kv = query.split('=')
                try:
                    key = kv[0]
                except:
                    continue
                try:
                    val = kv[1]
                except:
                    val = None
                search_key = SearchKeyVal.objects.create(key=key, val=val)
                self.search_key_vals.add(search_key)
            self.save() # save added m2m records
        else:
            super(Url, self).save(*args, **kwargs)

    def getUrls(options):
        """
        Get a list of URLs, sorted, and return only ones with at least 1 valid run in the book.
        Otherwise you could have a list of a bunch of URLs that don't have any runs yet.

        """

        allowedSortby = {
            'url': 'url',
            'date': 'lighthouse_run__created_date',
            'a11yscore': 'url_kpi_average__accessibility_score',
            'perfscore': 'url_kpi_average__performance_score',
            'seoscore': 'url_kpi_average__seo_score',
        }

        defSortby = "date"
        defSortorder = "-"
        defUrlIds = []

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

        try:
            urlIds = options['ids']
        except Exception as ex:
            urlIds = defUrlIds

        ## Map sortorder field to proper query filter condition.
        querySortorder = "" if userSortorder == "asc" else defSortorder


        urls = Url.objects.prefetch_related("lighthouse_run").prefetch_related("url_kpi_average")
        
        ## Do a special sorting procedure to put null values first if ascending, last if order is descending.
        ## By default, Django always puts null date fields first no matter what.
        if querySortorder == "":
            urls = urls.order_by(F(querySortby).asc(nulls_first=True))
        else:
            urls = urls.order_by(F(querySortby).desc(nulls_last=True))
        
        if len(urlIds) > 0:
            urls = urls.filter(id__in=urlIds)
        
        return urls

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


class UrlPath(models.Model):
    """
    Url path 'segments' and order.
    """

    created_date = models.DateTimeField(auto_now_add=True)
    sequence = models.IntegerField(default=0, null=True, blank=True)
    path = models.CharField(max_length=255)

    class Meta:
        ordering = ['path',]

        indexes = [
            models.Index(fields=['path', 'sequence',]),
        ]

    def __str__(self):
        return '%s: %s' % (self.path, self.sequence,)


class SearchKeyVal(models.Model):
    """
    url.location.search key -> val.
    """

    created_date = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=128)
    val = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['key',]

        indexes = [
            models.Index(fields=['key', 'val',]),
        ]

    def __str__(self):
        return '%s: %s' % (self.key, self.val,)


class Team(models.Model):
    """
    Person, team, department, whatever that might be responsible for a
    user timing measure or URL.
    """

    created_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)


    class Meta:
        ordering = ['name']

    def __str__(self):
        return '%s' % (self.name,)


class UserTimingMeasureName(models.Model):
    """
    A user-timing measure name. Used as name pointer for timing measures.
    Allows for easy global average calculation and prevents massive
    duplication of timing mark names across every run.
    """

    created_date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    team = models.ForeignKey('Team',
                            related_name='user_timing_measure_name_team',
                            on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['name']

        indexes = [
            models.Index(fields=['created_date', 'name',]),
        ]

    def __str__(self):
        return '%s' % (self.name,)


class UserTimingMeasure(models.Model):
    """
    A user-timing measure extracted from the related lighthouse run.
    Dynamically generated on LighthouseDataRaw save by simply looping
    thru the report user-timing object.
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

        indexes = [
            models.Index(fields=['created_date', 'url', 'name',]),
        ]

    def __str__(self):
        return '%s : %s' % (self.name, self.duration)


class UserTimingMeasureAverage(models.Model):
    """
    The average of a particular user-timing for a particular URL.
    These are dynamically generated on LighthouseDataRaw save, by simply
    averaging all the same user-timings for the given URL.
    Only runs that are 'valid' are counted in the average.
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

        indexes = [
            models.Index(fields=['created_date', 'url', 'name',]),
        ]

    def __str__(self):
        return '%s : %s' % (self.name, self.duration)


class UrlKpiAverage(models.Model):
    """
    Stored running average of each KPI for a given URL.
    This is created on LighthouseDataRaw save.
    Only runs that are 'valid' are counted in the average.
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

    class Meta:
        indexes = [
            models.Index(fields=['created_date', 'url',]),
        ]

    def __str__(self):
        return '%s' % (self.url.url,)

    def getFilteredAverages(urls):
        try:
          return UrlKpiAverage.objects.filter(url_id__in=list(urls.values_list('id', flat=True)))
        except Exception as ex:
          return UrlKpiAverage.objects.all()


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
    The raw data object as collected from Lighthouse.
    This is used by passing it to the lighthouse-viewer page to
    view the actual Lighthouse report.
    """

    created_date = models.DateTimeField(auto_now_add=True)
    lighthouse_run = models.ForeignKey('LighthouseRun',
                            related_name='lighthouse_data_raw_lighthouse_run',
                            on_delete=models.PROTECT)
    report_data = JSONField()


    class Meta:
        verbose_name_plural = "Lighthouse data raw"

        indexes = [
            models.Index(fields=['created_date', 'lighthouse_run',]),
        ]

    def __str__(self):
        return "%s - %s" % (self.lighthouse_run, self.created_date,)

    def save_report(self, raw_data):
        """
        Save the posted raw report data object to the database.

        """

        ## Initially set run to be 'valid'. If the report contains a 400+ header
        ##  then we set this to 'false' so we don't bother re-calculating averages.
        validRun = True
        raw_report = json.loads(raw_data.decode('utf-8'))

        ## Set the raw data JSON and get the URL object so we can
        ##  process and create all the other models.
        report_data = json.loads(raw_report['report'])
        url = Url.objects.get(url=report_data['requestedUrl'])


        ## 1. Create this new LighthouseRun object (the main pointer/parent).
        this_run = LighthouseRun(url=url)
        this_run.save()


        ## 2. Change the Url object to point to this Run as the new/latest one.
        url.lighthouse_run = this_run
        url.save()


        ## 3. Create this raw data object and point to the Run it's associated with (created in #2)
        lighthouse_data_raw = LighthouseDataRaw(lighthouse_run=this_run,
                                                report_data=report_data,)
        lighthouse_data_raw.save()

        ## From https://blog.dareboost.com/en/2018/06/lighthouse-tool-chrome-devtools/
        # First ContentFul Paint: First contentful paint marks the time at which the first text/image is painted.
        # First Meaningful Paint: First Meaningful Paint measures when the primary content of a page is visible.
        # Speed Index: Speed Index shows how quickly the contents of a page are visibly populated.
        # First CPU Idle: First CPU Idle marks the first time at which the page’s main thread is quiet enough to handle input.
        # Time to Interactive: Interactive marks the time at which the page is fully interactive.

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
        ## Otherwise we would use: LighthouseRun...filter().update(...) as it's more performant in Django.
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
        ## Flag variable is used below so we don't re-calc averages if we don't have to.
        try:
            statusCode = report_data['audits']['network-requests']['details']['items'][0]['statusCode']
            if statusCode > 399:
                this_run.invalid_run = True
                this_run.http_error_code = statusCode
                validRun = False
        except Exception as ex:
            pass

        ## Save the run object with populated fields.
        this_run.save()
        
        
        if validRun:
            ## 5. Get/Create the average model object and re-calc new averages including the run we just saved.
            urlRuns = LighthouseRun.objects.filter(url=url).validRuns()

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
                    ## Should log this after logging model is setup.
                    pass


                ## Now re-calculate the average for this user-timing item, FOR THIS URL.
                ## User-timings only happen if the page actually loaded and executed properly.
                ## IOW: A report that was invalid and returned a 400+ HTTP response code
                ##   won't contain the user-timings so this averaging step won't even run.
                ## Zero to no risk of averaging an 'invalid' user-timing # here.
                if validRun:
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
    Stores the Lighthouse report 'user-timing' JSON object that contains all the
    user-timings for the associated LighthouseRun.
    """

    created_date = models.DateTimeField(auto_now_add=True)
    lighthouse_run = models.ForeignKey('LighthouseRun',
                            related_name='lighthouse_data_usertiming_lighthouse_run',
                            on_delete=models.PROTECT)
    report_data = JSONField()

    class Meta:
        indexes = [
            models.Index(fields=['created_date', 'lighthouse_run',]),
        ]

    def __str__(self):
        return "%s - %s" % (self.lighthouse_run, self.created_date,)


class BannerNotification(models.Model):
    """
    Allows you to create a site-wide banner at the top of the page for site-wide
    notifications, i.e. site maintenance, problems, important updates, etc.
    """

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
    """
    Basic page view tracking. Primarily allow you to see what pages/features are used most.
    """

    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    modified_date = models.DateTimeField(auto_now=True, editable=False)
    url = models.CharField(max_length=2000, unique=True)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-view_count']

    def __str__(self):
        return "%s : %s" % (self.view_count, self.url)


class UrlFilterPart(models.Model):
    """
    A filter part: e.g.: { 'hostname': 'www.foo.com' }
                         { 'pathname': 'bar' }
                         { 'query_string': { 'baz': '22' } }
    One or many UrlFilterParts will we used to query for urls.

    """

    LOCATION_PROPS = (
        ('protocol', 'protocol',),
        ('host', 'host',),
        ('hostname', 'hostname',),
        ('port', 'port',),
        ('pathname', 'pathname',),
        ('path_segment', 'path_segment',),
        ('search', 'search',),
        ('search_key', 'search_key',),
        ('hash', 'hash',),
        ('origin', 'origin',),
    )
    prop = models.CharField(max_length=16, choices=LOCATION_PROPS)
    # Key will only be used when one is filtering for a specific search_key
    filter_key = models.CharField(max_length=128, null=True, blank=True)
    filter_path_index = models.IntegerField(null=True, blank=True)
    filter_val = models.CharField(max_length=128)
    url_filter = models.ForeignKey('UrlFilter',
                                   related_name='url_filter_part_url_filter',
                                   on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['prop',]

        indexes = [
            models.Index(fields=[
                'prop',
                'filter_key',
                'filter_path_index',
                'filter_val',
            ]),
        ]

    def __str__(self):
        return "%s: %s => %s" % (self.prop, self.filter_key or None, self.filter_val,)


class UrlFilter(models.Model):
    """
    A named UrlFilter. Allows users to create and save a filter for reuse and shared usage.
    """

    FILTER_MODES = (
        ('AND', 'AND',),
        ('OR', 'OR',),
    )

    created_date = models.DateTimeField(auto_now_add=True, editable=False)
    modified_date = models.DateTimeField(auto_now=True, editable=False)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    slug = models.SlugField(unique=True)
    mode = models.CharField(max_length=16, choices=FILTER_MODES)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return "%s" % (self.name)

    def get_filter_safe(filter_slug):
        try:
            return UrlFilter.objects.get(slug=filter_slug)
        except UrlFilter.DoesNotExist:
            return None

    def run_query(self):
        """
        Get all of the filter parts and create a set of urls
        to do dashboard operations on.
        """
        filter_parts = UrlFilterPart.objects.filter(url_filter=self)
        filter_map = {'OR': Q.OR, 'AND': Q.AND}

        and_condition = Q()
        
        for part in filter_parts:
            query_obj = self.make_query_object(part)
            and_condition.add(Q(**query_obj), filter_map[self.mode])

        query_set = Url.objects.filter(and_condition).distinct()

        return query_set

    def make_query_object(self, part):
        """
        Create an object that can be used in a Q() and_condition.
        """
        if part.prop == 'path_segment':
            # return a path_segment object to query aginst
            # the M2M relationship
            if part.filter_path_index is not None:
                obj = {
                    'url_paths__sequence': part.filter_path_index,
                    'url_paths__path': part.filter_val
                }

                return obj
            else:
                # this should match any path segment in any sequence
                obj = {
                    'url_paths__path': part.filter_val
                }

                return obj
        elif part.prop == 'search_key':
            # TODO: not supporting search_key until required
            #       by issues, enhancement requests
            return {}
        else:
            obj = {}
            obj[part.prop] = part.filter_val

            return obj

