# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, render_template

from application.controllers.user import get_filter_link
from application.models.order import Order
from application.nutils.date import format_date_zh
from application.permissions import ManagerPermission
from application.session import get_or_set_store_id
from application.utils import DATE_FORMAT

bp = Blueprint('mmgmt', __name__, url_prefix="/mmgmt")


@bp.route('/', methods=['GET'])
@ManagerPermission()
def stats_summary():
    now = datetime.datetime.now()
    today = datetime.date.today()
    first_day_of_currrent_month = datetime.date.today().replace(day=1)
    store_id = get_or_set_store_id()
    current_endpoint = 'mmgmt.stats_summary'

    orders_stats = dict()
    orders_stats['today_orders_count'] = Order.count_orders_by_date_and_store(today, store_id)
    orders_stats['today_delivered_count'] = Order.count_delivered_orders_between_date_and_store(store_id, today, today)
    orders_stats['current_month_delivered_count'] = Order.count_delivered_orders_between_date_and_store(store_id,
                                                                                                        first_day_of_currrent_month, today)
    orders_stats['undelivered_count'] = Order.count_all_new_orders_by_store(store_id)

    # inv_status = dict()
    # inv_status['total_inv'] = ?

    rx_stats = dict()
    from application.models.reception import Reception
    today_receptions = Reception.find_all_of_today_in_store(store_id)
    rx_stats['rx_new'] = len([rx for rx in today_receptions if rx.rx_type == 'new'])
    rx_stats['rx_appt_new'] = len([rx for rx in today_receptions if rx.rx_type == 'appt_new'])
    rx_stats['rx_appt'] = len([rx for rx in today_receptions if rx.rx_type == 'appt'])
    rx_stats['rx_other'] = len([rx for rx in today_receptions if rx.rx_type == 'other'])

    rx_stats['rx_total'] = len(today_receptions)
    rx_stats['rx_instore'] = len([rx for rx in today_receptions if rx.status != 'completed'])

    rx_base_url, rx_url_params = get_filter_link('receptions.receptions', now, now, current_endpoint)
    order_base_url, order_url_params = get_filter_link('orders.orders', now, now, current_endpoint)

    monthly_delivered_order_url_params = order_url_params.copy()
    monthly_delivered_order_url_params.update(
        {'start_date': datetime.date.today().replace(day=1).strftime(DATE_FORMAT)})
    monthly_delivered_order_url_params['status_filter'] = 'delivered'
    monthly_delivered_order_url_params['history'] = 'y'

    all_new_order_url_params = order_url_params.copy()
    all_new_order_url_params['start_date'] = ''
    all_new_order_url_params['end_date'] = ''
    all_new_order_url_params['status_filter'] = 'new'

    return render_template('mmgmt/summary.html', today_str=format_date_zh(datetime.date.today()),
                           orders_stats=orders_stats, rx_stats=rx_stats, rx_base_url=rx_base_url,
                           rx_url_params=rx_url_params, order_base_url=order_base_url,
                           order_url_params=order_url_params,
                           monthly_delivered_order_url_params=monthly_delivered_order_url_params,
                           all_new_order_url_params=all_new_order_url_params)


@bp.route('/detail', methods=['GET'])
@ManagerPermission()
def stats_detail():
    return render_template('mmgmt/detail.html')


@bp.route('/chart', methods=['GET'])
@ManagerPermission()
def stats_chart():
    return render_template('mmgmt/chart.html')
