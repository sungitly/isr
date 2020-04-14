# -*- coding: utf-8 -*-
import datetime

from application.api import api
from application.models.stats import get_store_stats, get_store_daily_stats
from application.models.store import Store
from application.nutils.date import get_last_monday, get_last_sunday
from application.utils import parse_comma_seperated_args
from dateutil.parser import parse
from flask import request

ALL_STATS = ['rx_count', 'incomplete_rx_count', 'new_valid_customer_count', 'imported_customer_count',
             'rx_customer_count_in_draft', 'no_deliver_date_orders_count', 'overdue_orders_count', 'new_appt_count',
             'new_calls_count',
             'new_orders_count']


@api.route('/ops/stats', methods=['GET'])
def ops_stats():
    now = datetime.datetime.now()
    start_date = request.args.get('start', get_last_monday(now))
    end_date = request.args.get('end', get_last_sunday(now))
    store_ids = parse_comma_seperated_args(request.args.get('store_id', None))

    if len(store_ids) == 0:
        stores = Store.find_all()
    else:
        stores = Store.find_all_by_stores_ids(store_ids)

    result = []
    for store in stores:
        if store.id > 0:
            stats_data = get_store_stats(start_date, end_date, store.id, ALL_STATS)
            result.append((store.id, store.name, stats_data))

    return result


@api.route('/ops/stores/<store_id>/stats/daily', methods=['GET'])
def ops_stats_daily(store_id):
    now = datetime.datetime.now()
    start_date = request.args.get('start', None)
    if start_date:
        start_date = parse(start_date)
    else:
        start_date = get_last_monday(now)

    end_date = request.args.get('end', None)
    if end_date:
        end_date = parse(end_date)
    else:
        end_date = get_last_sunday(now)

    stores = Store.find_all_by_stores_ids([store_id])

    result = dict()
    if stores and len(stores) > 0:
        store = stores[0]
        stats_data = get_store_daily_stats(start_date, end_date, store.id, ALL_STATS)
        result['store_id'] = store.id
        result['storename'] = store.name
        result['data'] = stats_data
        return result