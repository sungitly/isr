# -*- coding: utf-8 -*-
import datetime

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from isoweek import Week

CN_DATE_CHARS = (u'年', u'月', u'日')


def get_first_day_of_month(date, months_delta=0):
    return date + relativedelta(months=months_delta, day=1)


def get_last_day_of_month(date, months_delta=0):
    return date + relativedelta(day=1, months=months_delta + 1, days=-1)


def get_last_monday(date):
    last_week = date + relativedelta(weeks=-1)
    date_cal = last_week.isocalendar()
    isoweek = Week(date_cal[0], date_cal[1])
    return isoweek.monday()


def get_last_sunday(date):
    last_week = date + relativedelta(weeks=-1)
    date_cal = last_week.isocalendar()
    isoweek = Week(date_cal[0], date_cal[1])
    return isoweek.sunday()


def get_start_end_date_by_duration_desc(duration):
    now = datetime.datetime.now()
    start = now
    end = now
    if duration == 'yesterday':
        yesterday = now + relativedelta(days=-1)
        start = yesterday
        end = yesterday
    elif duration == 'last_week':
        start = get_last_monday(now)
        end = get_last_sunday(now)
    elif duration == 'last_month':
        start = get_first_day_of_month(now, months_delta=-1)
        end = get_last_day_of_month(now, months_delta=-1)

    return start, end


def get_dates_between(start, end):
    dates = []
    while start <= end:
        dates.append(start)
        start = start + datetime.timedelta(days=1)

    return dates


# noinspection PyBroadException
def parse_date(date_param, default=None):
    try:
        if isinstance(date_param, datetime.datetime):
            return date_param.date()
        elif isinstance(date_param, datetime.date):
            return date_param
        elif isinstance(date_param, unicode) and is_chinese_date_str(date_param):
            return parse_chinese_date(date_param, default=default)
        else:
            result = parse(date_param)
            if result and isinstance(result, datetime.datetime):
                return result.date()
    except Exception:
        pass

    return default


def is_chinese_date_str(date_str):
    return all(c in date_str for c in CN_DATE_CHARS)


def parse_chinese_date(date_str, default=None):
    if is_chinese_date_str(date_str):
        return datetime.datetime.strptime(date_str.encode('utf-8'), u'%Y年%m月%d日'.encode('utf-8'))


def format_date_zh(p_date):
    return p_date.strftime(u'%Y年%m月%d日'.encode('utf-8')).decode('utf-8')
