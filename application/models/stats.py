# -*- coding: utf-8 -*-
import datetime

from application.models.appointment import Appointment
from application.models.calllog import Calllog
from application.models.customer import Customer
from application.models.lookup import LookupValue
from application.models.order import Order
from application.models.reception import Reception
from application.models.setting import TaSetting
from application.models.user import User
from application.nutils.date import get_first_day_of_month, get_last_day_of_month, get_dates_between
from application.redisstore import stats_redis_store
from application.utils import WEEK_FORMAT, DATE_FORMAT_SHORT_MONTH_DAY, DATE_FORMAT
from isoweek import Week


class StoreStats(object):
    # redis keys
    weekly_store_stats = 'isr:stats:weekly:%s:store:%s'
    monthly_store_stats = 'isr:stats:monthly:%s:store:%s'

    @staticmethod
    def set_weekly_store_stats(week_year, store_id, key, value):
        '''
        :param week_year: 2015-01
        '''
        name = StoreStats.weekly_store_stats % (week_year, store_id)
        stats_redis_store.hset(name, key, value)

    @staticmethod
    def get_weekly_store_stats(week_year, store_id, key):
        name = StoreStats.weekly_store_stats % (week_year, store_id)
        return stats_redis_store.hget(name, key)


class StoreStatsData(object):
    def __init__(self, category='', data=None):
        self.category = category
        if data:
            self.data = data
        else:
            self.data = dict()


def get_weekly_ta(monday, sunday, store_id):
    tasetting = TaSetting.find_active_weekly_ta(monday.isocalendar()[0], monday.isocalendar()[1], store_id)
    return tasetting.value if tasetting else 0


def count_rr_rx(start, end, store_id):
    result = []
    refered_customers_rx_ids = Reception.count_all_refered_between_dates_in_store(start, end, store_id)

    if len(refered_customers_rx_ids) > 0:
        result.extend(refered_customers_rx_ids)

    reorder_customers_rx_ids = Reception.count_all_reorder_between_dates_in_store(start, end, store_id)

    if len(reorder_customers_rx_ids) > 0:
        result.extend(reorder_customers_rx_ids)

    return len(set(result))


def count_rr_orders(start, end, store_id):
    result = []
    refered_customers_order_ids = Order.count_all_refered_between_dates_in_store(start, end, store_id)

    if len(refered_customers_order_ids) > 0:
        result.extend(refered_customers_order_ids)

    reorder_customers_order_ids = Order.count_all_reorder_between_dates_in_store(start, end, store_id)

    if len(reorder_customers_order_ids) > 0:
        result.extend(reorder_customers_order_ids)

    return len(set(result))


# stats
stats_meta = {
    'total_rx_customer_count': Reception.count_all_distinct_customers_count_between_dates_in_store,
    'total_orders_count': Order.count_all_between_dates_in_store,
    'total_customer_count': Customer.count_all_between_dates_in_store,
    # FIXME test_drive_customer_count is incorrect right now because we don't have test drive creation date
    'test_drive_customer_count': Customer.count_test_drive_customers_between_dates_in_store,
    'test_drive_ordered_customer_count': Customer.count_ordered_test_drive_customers_between_dates_in_store,
    'formal_customer_count': Customer.count_all_formal_between_dates_in_store,
    'instore_appt_count_by_customer': Appointment.count_instore_appts_by_customers_between_dates_in_store,
    'instore_appt_count': Appointment.count_instore_appts_between_dates_in_store,
    'closed_instore_appt_count': Appointment.count_closed_instore_appts_between_dates_in_store,
    'ta_settings': get_weekly_ta,
    'total_rr_rx_count': count_rr_rx,
    'total_rr_order': count_rr_orders,
}


def get_weekly_store_stats_between_dates(start, end, store_id, stats_names=None):
    stats = []
    today = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

    while start <= end and start <= today:
        start_cal = start.isocalendar()
        year, week, weekday = start_cal
        stats.append(
            StoreStatsData(convert_to_catergory_str(year, week),
                           get_weekly_stats(week, year, store_id, stats_names)))
        start = start + datetime.timedelta(weeks=1)
    return stats


def convert_to_catergory_str(year, week):
    isoweek = Week(year, week)
    monday = isoweek.monday()
    sunday = isoweek.sunday()
    return monday.strftime(DATE_FORMAT_SHORT_MONTH_DAY) + '~' + sunday.strftime(DATE_FORMAT_SHORT_MONTH_DAY)


def get_weekly_stats(week, year, store_id, stats_names):
    result = {}

    for stats_name in stats_names:
        weekly_stats = None
        isoweek = Week(year, week)
        monday = isoweek.monday()
        sunday = isoweek.sunday()
        if stats_name != 'ta_settings':
            weekly_stats = StoreStats.get_weekly_store_stats(monday.strftime(WEEK_FORMAT), store_id, stats_name)

        if not weekly_stats:
            weekly_stats = stats_meta.get(stats_name)(monday, sunday, store_id)
            # if the week >= this week, do not cache the result because the result will be changed.
            if week < datetime.datetime.now().isocalendar()[1]:
                StoreStats.set_weekly_store_stats(monday.strftime(WEEK_FORMAT), store_id, stats_name, weekly_stats)

        result[stats_name] = weekly_stats

    return result


sales_stats_meta = {
    'total_rx_customer_count': Reception.count_all_distinct_customers_count_by_sales_between_dates_in_store,
    'total_orders_count': Order.count_all_by_sales_between_dates_in_store,
    'total_deliver_count': Order.count_all_delivered_by_sales_between_dates_in_store,
    'total_customer_count': Customer.count_all_by_sales_between_dates_in_store,
    'formal_customer_count': Customer.count_all_formal_by_sales_between_dates_in_store,
    'instore_appt_count': Appointment.count_instore_appts_by_sales_between_dates_in_store,
    'closed_instore_appt_count': Appointment.count_closed_instore_by_sales_appts_between_dates_in_store,
    'test_drive_customer_count': Customer.count_test_drive_customers_by_sales_between_dates_in_store,
    'avg_rx_duration': Reception.get_avg_rx_duration_by_sales_between_dates_in_store
}


# Sales Stats Below
def get_sales_stats(store_id, stats_names):
    stats = []
    now = datetime.datetime.now()
    current_month_stats_data = get_sales_stats_data_dict(get_first_day_of_month(now).date(),
                                                         get_last_day_of_month(now).date(), store_id, stats_names)

    prev_month_stats_data = get_sales_stats_data_dict(get_first_day_of_month(now, months_delta=-1).date(),
                                                      get_last_day_of_month(now, months_delta=-1).date(), store_id,
                                                      stats_names)

    sales = User.get_all_sales_by_store_from_cache(long(store_id))

    for sale in sales:
        if sale.username != u'管理员':
            stats.append(StoreStatsData(sale.username, {
                'current_month': extract_sales_stats_data(stats_names, current_month_stats_data, sale.id),
                'prev_month': extract_sales_stats_data(stats_names, prev_month_stats_data, sale.id)}))

    return stats


def get_sales_stats_data_dict(start, end, store_id, stats_names):
    result = {}
    for name in stats_names:
        stats_raw_data = sales_stats_meta.get(name)(start, end, store_id)
        result[name] = {r[0]: int(r[1]) if r[1] else 0 for r in stats_raw_data}

    return result


def extract_sales_stats_data(stats_names, stats_data_dict, sales_id):
    result = {}

    for name in stats_names:
        count = stats_data_dict.get(name).get(sales_id)
        result[name] = count if count else 0

    return result


def get_unordered_customers_count_by_intent_level(start, end, store_id):
    uoc_stats = Reception.get_unordered_customers_count_by_intent_level_between_dates_in_store(start, end, store_id)

    uoc_stats = {s[1]: s[0] for s in uoc_stats}

    intent_levels_dict = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), 'intent-level')

    result = []
    for code, value in intent_levels_dict.iteritems():
        stats = uoc_stats.get(code, 0)
        if stats != 0:
            result.append((value.value, stats))

    return result


def get_rx_customers_count_by_car_models(start, end, store_id):
    rx_customers_by_car = Reception.get_rx_customers_count_by_car_models_bwteeen_dates_in_stores(start, end, store_id)

    intent_cars_dict = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), 'intent-car')

    result = dict()
    for code, value in intent_cars_dict.iteritems():
        count = 0
        for stats in rx_customers_by_car:
            # need to calc count again since there would be multiple intent cars seperated by comma.
            if code in stats[1]:
                count += stats[0]

        if count > 0:
            result[code] = count
    return result


def get_orders_count_by_car_models(start, end, store_id):
    orders_by_car = Order.count_all_by_car_models_bwteeen_dates_in_store(start, end, store_id)

    return {o[1]: o[0] for o in orders_by_car}


# car stats meta
car_stats_meta = {
    'rx_customers_count_by_car': get_rx_customers_count_by_car_models,
    'orders_count_by_car': get_orders_count_by_car_models
}


def get_car_stats_between_dates_in_stores(start, end, store_id, stats_names=None):
    intent_cars_dict = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), 'intent-car')

    data_per_category = {}
    for stats_name in stats_names:
        data_per_category[stats_name] = car_stats_meta.get(stats_name)(start, end, store_id)

    result = []

    for code, value in intent_cars_dict.iteritems():
        data = {}

        ignore = False
        for stats_name in stats_names:
            stats = data_per_category.get(stats_name).get(code, 0)
            if stats == 0:
                ignore = True
                continue

            data[stats_name] = stats

        if not ignore:
            stats = StoreStatsData()
            stats.category = value.value
            stats.data = data
            result.append(stats)

    return result


order_cycle = [(u'1周', (0, 7)), (u'2周', (7, 14)), (u'1-2个月', (30, 60)), (u'2-3个月', (60, 90)),
               (u'3-5个月', (90, 150)),
               (u'半年', (150, 180)), (u'超过半年', [180])]

order_cycle_stats_meta = {'order_count': Order.count_all_within_cycle_between_dates_in_store,
                          'rx_count': Order.get_rx_count_within_cycle_between_dates_in_store,
                          'appt_count': Order.get_appt_count_within_cycle_between_dates_in_store}


def get_order_cycle_stats(start, end, store_id, stats_names=None):
    result = []

    for cycle_item in order_cycle:
        stats = StoreStatsData()
        stats.category = cycle_item[0]

        data = dict()
        for stats_name in stats_names:
            data[stats_name] = order_cycle_stats_meta.get(stats_name)(start, end, store_id, cycle_item[1])

        stats.data = data
        result.append(stats)
    return result


store_daily_stats_meta = {'rx_count': Reception.count_all_valid_by_date_in_store,
                          'incomplete_rx_count': Reception.count_all_completed_by_system_by_date_in_store,
                          'new_valid_customer_count': Customer.count_all_new_active_by_date_in_store,
                          'imported_customer_count': Customer.count_all_imported_by_date_in_store,
                          'rx_customer_count_in_draft': Customer.count_all_draft_rx_by_date_in_store,
                          'new_appt_count': Appointment.count_all_new_appt_by_date_in_store,
                          'new_calls_count': Calllog.count_all_by_date_in_store,
                          'new_orders_count': Order.count_orders_by_date_and_store,
                          'no_deliver_date_orders_count': Order.count_no_deliver_date_orders_by_date_and_store,
                          'overdue_orders_count': Order.count_overdue_orders_by_date_and_store}


def get_store_daily_stats(start, end, store_id, stats_names=None):
    result = []
    dates = get_dates_between(start, end)

    for date in dates:
        stats = {'date': date.strftime(DATE_FORMAT)}
        for stats_name in stats_names:
            stats[stats_name] = store_daily_stats_meta.get(stats_name)(date, store_id)
        result.append(stats)

    return result


store_stats_meta = {'rx_count': Reception.count_all_valid_between_date_in_store,
                    'incomplete_rx_count': Reception.count_all_completed_by_system_between_date_in_store,
                    'new_valid_customer_count': Customer.count_all_new_active_between_date_in_store,
                    'imported_customer_count': Customer.count_all_imported_between_date_in_store,
                    'rx_customer_count_in_draft': Customer.count_all_draft_rx_between_date_in_store,
                    'new_appt_count': Appointment.count_all_new_appt_between_date_in_store,
                    'new_calls_count': Calllog.count_all_between_date_in_store,
                    'new_orders_count': Order.count_orders_between_date_and_store,
                    'no_deliver_date_orders_count': Order.count_no_deliver_date_orders_between_date_and_store,
                    'overdue_orders_count': Order.count_overdue_orders_between_date_and_store}


def get_store_stats(start, end, store_id, stats_names=None):
    stats = {}
    for stats_name in stats_names:
        stats[stats_name] = store_stats_meta.get(stats_name)(start, end, store_id)

    return stats
