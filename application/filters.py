# -*- coding: utf-8 -*-
import datetime
from collections import OrderedDict

from application.models.appointment import Appointment
from application.models.lookup import LookupValue
from application.utils import DATE_FORMAT, DATE_TIME_FORMAT, DATE_TIME_FORMAT_WO_SEC, TIME_FORMAT, TIME_FORMAT_WO_SEC, \
    calc_duration_until_now
from isoweek import Week


def human_readable_timedelta(value):
    try:
        timedelta = int(value)
    except:
        return ''

    hours = timedelta / 3600
    minutes = (timedelta % 3600) / 60
    return str(hours).zfill(2) + ':' + str(minutes).zfill(2)


def human_readable_timedelta_until_now(value):
    time_diff_in_sec = calc_duration_until_now(value)
    return human_readable_timedelta(time_diff_in_sec)


def timedelta_in_minutes(value):
    try:
        timedelta = int(value)
    except:
        return ''

    result = u''
    minutes = timedelta / 60
    seconds = timedelta % 60

    if minutes and minutes > 0:
        result = result + unicode(minutes) + u'分'

    return result + unicode(seconds) + u'秒'


def date_str(value):
    if not value:
        return ''
    elif isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
        return value.strftime(DATE_FORMAT)
    else:
        return value


def datetime_str(value, with_seconds=None):
    if not value:
        return ''
    elif isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
        if with_seconds:
            return value.strftime(DATE_TIME_FORMAT)
        else:
            return value.strftime(DATE_TIME_FORMAT_WO_SEC)
    else:
        return value


def time_str(value, with_seconds=None):
    if not value:
        return ''
    elif isinstance(value, datetime.date) or isinstance(value, datetime.datetime):
        if with_seconds:
            return value.strftime(TIME_FORMAT)
        else:
            return value.strftime(TIME_FORMAT_WO_SEC)
    else:
        return value


def gender_str(value):
    if not value:
        return ''
    elif value is True or value > 0:
        return u'男'
    else:
        return u'女'


CUSTOMER_STATUS = {'draft': u'资料待更新', 'formal': u'待跟进', 'enlist': u'跟进中', 'ordered': u'已成交', 'defeated': u'休眠',
                   'cancelled': u'无效客户'}
CUSTOMER_STATUS_CSS = {'draft': 'label-danger', 'formal': 'label-warning', 'enlist': 'label-info',
                       'ordered': 'label-primary', 'defeated': 'label-default', 'cancelled': 'label-default'}


def customer_status_str(value):
    return CUSTOMER_STATUS.get(value, u'')


def customer_status_css(value):
    return CUSTOMER_STATUS_CSS.get(value, '')


def lookup_str(value, store_id, lookup_name):
    if not value:
        return ''

    lookupvalue_dict = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), lookup_name)
    lookupvalue = lookupvalue_dict.get(value, None)
    if not lookupvalue:
        return ''
    elif lookupvalue == 'none':
        return u'无'
    else:
        return lookupvalue.value


def multi_lookup_str(value, store_id, lookup_name):
    if not value:
        return ''

    if ',' not in value:
        return lookup_str(value, store_id, lookup_name)
    else:
        lookupvalues = []
        values = value.split(',')
        for value in values:
            lookupvalues.append(lookup_str(value, store_id, lookup_name))

        return ', '.join(lookupvalues)


def weekly_str(value, year):
    isoweek = Week(year, value)
    monday = isoweek.monday()
    sunday = isoweek.sunday()

    return monday.strftime(DATE_FORMAT) + ' - ' + sunday.strftime(DATE_FORMAT)


def none_str(value):
    if not value:
        return ''
    elif value == 'none':
        return u'无'
    else:
        return value


APPT_STATUS = {'opened': u'未完成', 'closed': u'已完成', 'cancelled': u'已取消'}
APPT_STATUS_CSS = {'opened': 'label-info', 'closed': 'label-success', 'cancelled': 'label-default'}


def hack_cancelled_followup(value, appt_type):
    if value == 'cancelled' and appt_type == 'followup':
        value = 'closed'
    return value


def appt_status_str(value, appt_type):
    value = hack_cancelled_followup(value, appt_type)
    return APPT_STATUS.get(value, u'')


def appt_status_css(value, appt_type):
    value = hack_cancelled_followup(value, appt_type)
    return APPT_STATUS_CSS.get(value, '')


APPT_TYPE = OrderedDict(Appointment.all_types_mapping)


def appt_type_str(value):
    return APPT_TYPE.get(value, u'')


RX_TYPE = {'new': u'首次', 'appt_new': u'首邀', 'appt': u'再次', 'other': u'手续'}


def rx_type_str(value):
    return RX_TYPE.get(value, u'')


RX_STATUS = {'assigned': u'前台分配', 'ongoing': u'接待中', 'completed': u'接待完成', 'cancelled': u'接待取消'}


def rx_status_str(value):
    return RX_STATUS.get(value, u'')


RADAR_STATUS = {'unknown': u'状态未知', 'off': u'无法连接', 'unstable': u'不稳定', 'on': u'连接正常', '0': u'无法连接', '1': u'连接正常'}
RADAR_STATUS_CSS = {'unknown': 'label-default', 'off': 'label-danger', 'unstable': 'label-warning',
                    'on': 'label-primary', '0': 'label-danger', '1': 'label-primary'}


def radar_status_str(value):
    if value:
        value = str(value)
    return RADAR_STATUS.get(value, u'')


def radar_status_css(value):
    if value:
        value = str(value)
    return RADAR_STATUS_CSS.get(value, '')


def bool_str(value):
    if value:
        return u'是'
    else:
        return u'否'


def cond_return_value(value, true_value, false_vale=''):
    if value:
        return true_value
    else:
        return false_vale
