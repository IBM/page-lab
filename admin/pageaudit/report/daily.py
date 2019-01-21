import csv
import datetime
import time

TODAY = datetime.datetime.today()
YESTERDAY = TODAY - datetime.timedelta(1)

DAILY_DUMP_PATH = '/data/reports/pagelab/daily'

field_names=['url', 'url2', 'views', 'hist', 'sequence',]

import django

from pageaudit.settings import *

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Avg, Max, Min, Q, Sum

from report.models import (
    Url,
    LighthouseRun,
    LighthouseDataRaw,
    LighthouseDataUsertiming,
    UserTimingMeasureName,
    UserTimingMeasure,
    UserTimingMeasureAverage
)

superuser = User.objects.get(id=1)

def report_yesterday_data():
    """
    Get the data generated yesterday
    """
    include_user_timing = True
    timestr = time.strftime("%Y-%m-%d-%H%M%S")
    path = "%s/%s.csv" % (DAILY_DUMP_PATH, timestr,)
    file = open(path, 'w')
    writer = csv.writer(file)

    with file:
        writer.writerow([
            "test_id",
            "url_id",
            "created_date",
            "url",
            "performance_score",
            "total_byte_weight",
            "number_network_requests",
            "time_to_first_byte",
            "first_contentful_paint",
            "first_meaningful_paint",
            "dom_content_loaded",
            "dom_loaded",
            "interactive",
            "masthead_onscreen",
            "redirect_hops",
            "redirect_wasted_ms",
            "sequence",
            "user_timing_data"
        ])

        run_data = LighthouseRun.objects.filter(
            created_date__date=YESTERDAY.date()
        )

        for run in run_data:
            if include_user_timing:
                try:
                    user_timing_data = str(LighthouseDataUsertiming.objects.get(lighthouse_run=run).report_data)
                except Exception as ex:
                    user_timing_data = ''
            else:
                user_timing_data = ''
            try:
                writer.writerow([
                    run.id,
                    run.url.id,
                    run.created_date,
                    run.url.url,
                    run.performance_score,
                    run.total_byte_weight,
                    run.number_network_requests,
                    run.time_to_first_byte,
                    run.first_contentful_paint,
                    run.first_meaningful_paint,
                    run.dom_content_loaded,
                    run.dom_loaded,
                    run.interactive,
                    run.masthead_onscreen,
                    run.redirect_hops,
                    run.redirect_wasted_ms,
                    run.url.id,
                    user_timing_data
                ])
            except Exception as ex:
                print(ex)
