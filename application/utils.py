# -*- coding: utf-8 -*-
import datetime
import inspect
import os
import time
from decimal import Decimal
from urlparse import urlparse

import phonenumbers
from dateutil.parser import parse
from flask.helpers import locked_cached_property
from flask.json import JSONEncoder

DATE_FORMAT = '%Y-%m-%d'
DATE_FORMAT_SHORT_MONTH_DAY = '%m/%d'
DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_TIME_FORMAT_WO_SEC = '%Y-%m-%d %H:%M'
TIME_FORMAT = '%H:%M:%S'
TIME_FORMAT_WO_SEC = '%H:%M'
WEEK_FORMAT = '%YW%V'

SECONDS_OF_DAY = 3600 * 24

SOURCES = {'isr': 'isr', 'frt': 'frt'}


class CustomizedEncoder(JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__dict__"):
            return obj_to_dict(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        elif isinstance(obj, Decimal):
            return str(obj)
        return super(CustomizedEncoder, self).encode(obj)


def obj_to_dict(obj):
    data = dict([(key, value)
                 for key, value in obj.__dict__.iteritems()
                 if not callable(value) and not key.startswith('_')])

    properties = inspect.getmembers(obj.__class__,
                                    lambda attr: isinstance(attr, property) or isinstance(attr, locked_cached_property))

    if len(properties) > 0:
        for prop_name, prop in properties:
            data[prop_name] = getattr(obj, prop_name)

    return data


def add_location_header(headers, location):
    if headers is None:
        headers = dict()

    headers['Location'] = location
    return headers


# noinspection PyBroadException
def calc_duration_until_now(start):
    if not isinstance(start, datetime.datetime):
        try:
            start = parse(start)
        except:
            return 0

    return (datetime.datetime.now() - start).seconds


def calc_duration(start, end):
    if not isinstance(start, datetime.datetime):
        try:
            start = parse(start)
        except:
            return 0

    if not isinstance(end, datetime.datetime):
        try:
            end = parse(end)
        except:
            return 0
    return (end - start).seconds


def validate_mobile(number):
    if '000' == number:
        return True
    else:
        try:
            m = phonenumbers.parse(number, 'CN')
        except:
            return False

        if m and phonenumbers.is_valid_number(m):
            return True
        else:
            return False


def is_valid_date(p_date):
    if not p_date:
        return False

    if isinstance(p_date, datetime.date) or isinstance(p_date, datetime.date):
        return True

    if parse(p_date):
        return True

    return False


def set_attr_ignore_error(p_object, name, value):
    try:
        setattr(p_object, name, value)
    except AttributeError:
        pass


def get_dates_by_week_year(year, week):
    startdate = time.asctime(time.strptime('%d %d 1' % (year, week), '%Y %W %w'))
    startdate = datetime.datetime.strptime(startdate, '%a %b %d %H:%M:%S %Y')
    dates = [startdate]
    for i in range(1, 7):
        dates.append(startdate + datetime.timedelta(days=i))
    return dates


def get_sales_selection(store_id):
    from application.models.user import User

    selections = [('all', u'销售顾问')]
    sales = User.get_all_sales_by_store_from_cache(long(store_id))
    selections.extend([(user.id, user.username) for user in sales])
    return selections


def get_selections_by_lookup_name(store_id, lookup_name):
    from application.models.lookup import LookupValue
    lookupvalues_list = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id),
                                                                                        lookup_name).values()
    lookupvalues_list.sort(key=lambda value: value.id)
    return [(value.code, value.value) for value in lookupvalues_list]


def get_stores_selection():
    from application.models.store import Store

    selections = [('', u'选择4S店')]
    # stores = User.find_all_stores()
    stores = Store.find_all()
    for store in stores:
        selections.append((store.id, store.name))
    return selections


def remove_empty_storename(selections):
    try:
        for storeinfo in selections:
            if storeinfo[0] != '' and int(storeinfo[0]) < 0:
                selections.remove(storeinfo)
    except Exception:
        pass
    finally:
        return selections


def get_stores_descriptions(store_id):
    from application.models.lookup import Lookup

    selections = Lookup.get_descriptions_by_store_id(store_id)
    return selections


def get_stores_descriptions_and_lookupvalues(lookup_id=None):
    from application.models.lookup import Lookup

    descriptions = dict()
    descriptions["description"] = u"意向车型"
    descriptions["id"] = u"序号"
    descriptions["code"] = u"代号"
    descriptions["value"] = u"意向车型"
    descriptions["orders"] = u"次序"
    descriptions["section"] = u"类别"
    descriptions["version"] = u"版本"

    if lookup_id is not None:
        try:
            description = Lookup.get_description_by_store_id(lookup_id).description
            descriptions["description"] = description.strip()
            descriptions["value"] = description.strip()
        except Exception:
            pass

    return descriptions


def convert_changevalues(data):
    changevalues = []
    data = dict(data)

    for i in range(len(data['value'])):
        changevalue = dict()
        for v in ['section', 'orders', 'value']:
            if v == 'orders':
                try:
                    changevalue[v] = int(data[v][i])
                except:
                    changevalue[v] = data[v][i]
            else:
                changevalue[v] = data[v][i]
        changevalues.append(changevalue)

    return changevalues


def parse_comma_seperated_args(args):
    if not args:
        return []
    elif ',' in args:
        return [unicode(x).strip() for x in args.split(',')]
    else:
        return [unicode(args).strip()]


def format_mobile(mobile):
    if mobile and mobile != '000':
        m = None
        try:
            m = phonenumbers.parse(mobile, 'CN')
        except:
            pass

        if m and phonenumbers.is_valid_number(m):
            if m.country_code == 86:
                return unicode(m.national_number)
            else:
                return phonenumbers.format_number(m, phonenumbers.PhoneNumberFormat.E164)

    return mobile


def convert_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def convert_dict_key_lower_case(data_dict):
    return {str(k).lower(): v for k, v in data_dict.iteritems()}


def run_sql_file(filename):
    if 'DATABASE_URL' not in os.environ:
        print 'Please define DATABASE_URL in environment variable!'
        return

    url = urlparse(os.getenv('DATABASE_URL'))

    from subprocess import Popen, PIPE
    process = Popen(["mysql", "--user=%s" % url.username, "--password=%s" % url.password, url.path[1:]],
                    stdout=PIPE, stdin=PIPE)
    output = process.communicate(file(filename).read())[0]
    print output


def str_random(length):
    import random
    import string
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))


def underscore_join_str(str_param):
    if str_param and isinstance(str_param, basestring):
        return u'_'.join(str_param.split())
    else:
        return u''
