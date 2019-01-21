#!/usr/bin/env python

import csv
import datetime
import time

TODAY = datetime.datetime.today()
YESTERDAY = TODAY - datetime.timedelta(1)

DAILY_DUMP_PATH = '/data/reports/pagelab/daily'

field_names=['url', 'url2', 'views', 'hist', 'sequence',]

import django

from pageaudit.settings import *

time.sleep(10)

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


def load_urls_into_db(path):
    f = open(path, 'r')

    reader = csv.DictReader(f,fieldnames= field_names)

    row_id = 0

    for row in reader:
        urlObj = Url(
            created_by = superuser,
            edited_by = superuser,
            url = 'https://%s' % row['url'],
            sequence = int(row['sequence'])
        )
        urlObj.save()


def write_report_csv(path, date_since=None, include_user_timing=False):
    if not path:
        print('path is required')
        return

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

        if date_since:
            if date_since['month'] and date_since['day'] and date_since['year']:
                m = date_since['month']
                d = date_since['day']
                y = date_since['year']
                run_data = LighthouseRun.objects.filter(created_date__gte=datetime.date(y, m, d))
            else:
                raise Exception('date_since requires month day and year properties')
        else:
            run_data = LighthouseRun.objects.all()

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


def update_urls(path):
    f = open(path, 'r')
    fields = ['url', 'page_compl_url',]
    reader = csv.DictReader(f, fieldnames=fields)

    for row in reader:
        try:
            urlSet = Url.objects.filter(url='https://%s' % row['url'])
            urlObj = urlSet.first()
            urlObj.save()
        except Exception as ex:
            print(ex)


if __name__ == '__main__':
    report_yesterday_data()
