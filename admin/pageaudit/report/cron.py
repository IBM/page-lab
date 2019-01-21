from report.daily import report_yesterday_data

def daily_report():
    """
    Kick off the daily report
    """
    DAILY_DUMP_PATH = '/data/reports/pagelab/daily'

    report_yesterday_data(output_path=DAILY_DUMP_PATH)
