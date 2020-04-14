# -*- coding: utf-8 -*-
import datetime

from flask import Blueprint, render_template, g, request

from application.models.appointment import Appointment
from application.models.campaign import Campaign
from application.models.order import Order
from application.models.reception import Reception
from application.models.setting import TaSetting
from application.models.user import SalesStatus, User
from application.nutils.date import get_first_day_of_month
from application.nutils.menu import USER_RT_DATA, USER_MORNING_CALL, USER_EVENING_CALL
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from application.utils import DATE_FORMAT

bp = Blueprint('user', __name__, url_prefix="/user")


@bp.route('/dashboard', methods=['GET'])
@UserPermission()
def dashboard():
    current_user = g.user
    now = datetime.datetime.now()
    store_id = get_or_set_store_id()
    orders_stats = dict()
    orders_stats['today_orders_count'] = Order.count_orders_by_date_and_store(datetime.date.today(), store_id)
    orders_with_status = Order.find_orders_status_from_date_and_store(datetime.date.today().replace(day=1), store_id)
    orders_stats['current_month_new_count'] = len(
        [x for x in orders_with_status if x.status == 'new'])
    orders_stats['current_month_delivered_count'] = Order.count_delivered_orders_between_date_and_store(store_id,
                                                                                                        get_first_day_of_month(
                                                                                                            now).date(),
                                                                                                        now.date())

    customer_stats = dict()
    today_receptions = Reception.find_all_of_today_in_store(store_id)
    completed_reception = filter(lambda rx: rx.status == 'completed', today_receptions)
    customer_stats['total'] = len(today_receptions) if today_receptions else 0
    customer_stats['complete'] = len(completed_reception) if completed_reception else 0
    customer_stats['instore'] = customer_stats['total'] - customer_stats['complete']
    customer_stats['new'] = len([x for x in today_receptions if x.rx_type == 'new'])
    customer_stats['appt_new'] = len([x for x in today_receptions if x.rx_type == 'appt_new'])
    customer_stats['appt'] = len([x for x in today_receptions if x.rx_type == 'appt'])
    customer_stats['other'] = len([x for x in today_receptions if x.rx_type == 'other'])

    today_appointments = Appointment.find_all_by_date_in_store(datetime.date.today(), store_id)
    appt_stats = dict()
    appt_stats['instore'] = len([x for x in today_appointments if x.status != 'cancelled' and x.type == 'instore'])
    appt_stats['open_instore'] = len([x for x in today_appointments if x.status == 'opened' and x.type == 'instore'])
    appt_stats['followup'] = len([x for x in today_appointments if x.type == 'followup'])
    appt_stats['open_followup'] = len([x for x in today_appointments if x.status == 'opened' and x.type == 'followup'])

    sales = User.get_all_sales_by_store_from_cache(long(store_id))
    # make sure the status is correct
    SalesStatus.reset_all_sales_status(store_id)
    sales_status = SalesStatus.get_all_sales_status(store_id)

    total_counts, reception_counts = calc_reception_counts(today_receptions, sales)

    for sale in sales:
        sale.status = sales_status.get(str(sale.id), 'free')
        set_status_label_and_style(sale)
        sale.rx_count = reception_counts.get(sale.id, {'total': 0, 'new': 0, 'appt_new': 0, 'appt': 0, 'other': 0})
    # receptions_per_sale = filter(lambda rx: rx.sales_id == sale.id, today_receptions)
    #     sale.rx_count = len(receptions_per_sale) if receptions_per_sale else 0
    #     total_rx_count += sale.rx_count

    sales.sort(key=lambda sale: sale.status)

    today_orders = Order.find_all_created_today_by_store(store_id)
    today_orders_count = len(today_orders) if today_orders else 0

    current_endpoint = 'user.dashboard'
    rx_base_url, rx_url_params = get_filter_link('receptions.receptions', now, now, current_endpoint)
    order_base_url, order_url_params = get_filter_link('orders.orders', now, now, current_endpoint)
    monthly_order_url_params = order_url_params.copy()
    monthly_order_url_params.update({'start_date': datetime.date.today().replace(day=1).strftime(DATE_FORMAT)})
    monthly_delivered_order_url_params = monthly_order_url_params.copy()
    monthly_delivered_order_url_params['status_filter'] = 'delivered'
    monthly_delivered_order_url_params['history'] = 'y'
    appt_base_url, appt_url_params = get_filter_link('appointments.appts', now, now, current_endpoint)
    # tbc_orders = Order.find_all_in_status_by_store(store_id, confirmed=0, status='new')

    return render_template('user/salesmanager/dashboard.html', selected_menu=USER_RT_DATA, orders_stats=orders_stats,
                           appt_stats=appt_stats,
                           customer_stats=customer_stats, sales=sales, today_orders=today_orders,
                           total_count=total_counts, today_orders_count=today_orders_count,
                           sales_receptions=reception_counts, rx_base_url=rx_base_url, rx_url_params=rx_url_params,
                           order_base_url=order_base_url, order_url_params=order_url_params,
                           monthly_order_url_params=monthly_order_url_params,
                           monthly_delivered_order_url_params=monthly_delivered_order_url_params,
                           appt_base_url=appt_base_url,
                           appt_url_params=appt_url_params)


@bp.route('/mc', methods=['GET'])
@UserPermission()
def morning_call():
    current_user = g.user
    store_id = get_or_set_store_id()

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    orders_stats = dict()
    orders_stats['yesterday_orders_count'] = Order.count_orders_by_date_and_store(yesterday, store_id)
    orders_stats['current_month_orders_count'] = Order.count_orders_from_date_and_store(
        datetime.date.today().replace(day=1),
        store_id)
    current_month_ta = TaSetting.find_active_monthly_ta(today.year, today.month, store_id)
    orders_stats['current_month_target'] = current_month_ta.value if current_month_ta else 'N/A'

    sales_stats = User.get_all_sales_by_store_from_cache(long(store_id))
    yesterday_receptions = Reception.find_all_by_date_in_store(yesterday, store_id)
    today_appointments = Appointment.find_all_by_date_in_store(datetime.date.today(), store_id)

    rx_stats = dict()
    rx_stats['yesterday_incomplete_count'] = len(
        [x for x in yesterday_receptions if x._last_status_changer == 'system'])

    total_counts, sales_counts = calc_reception_counts(yesterday_receptions, sales_stats)

    for sale in sales_stats:
        sale.rx_count = sales_counts.get(sale.id, {'total': 0, 'new': 0, 'appt_new': 0, 'appt': 0, 'other': 0})

        populate_appt_count_agg_by_sale_and_type(today_appointments, sale)

    sales_stats.sort(key=lambda sale: sale.rx_count, reverse=True)

    appts_count = generate_appt_count_agg_by_type(today_appointments)
    recent_campaigns = Campaign.find_all_by_store_in_recent_days(store_id, 15)

    current_endpoint = 'user.morning_call'
    now = datetime.datetime.now()
    yesterday_datetime = now - datetime.timedelta(days=1)
    rx_base_url, rx_url_params = get_filter_link('receptions.receptions', yesterday_datetime, yesterday_datetime,
                                                 current_endpoint)
    rx_incomplete_params = rx_url_params.copy()
    rx_incomplete_params['incomplete'] = 'y'

    appt_base_url, appt_url_params = get_filter_link('appointments.appts', now, now, current_endpoint)

    order_base_url, order_url_params = get_filter_link('orders.orders', yesterday_datetime, yesterday_datetime,
                                                       current_endpoint)
    monthly_order_url_params = order_url_params.copy()
    monthly_order_url_params['start_date'] = datetime.date.today().replace(day=1).strftime(DATE_FORMAT)
    monthly_order_url_params['end_date'] = now.strftime(DATE_FORMAT)

    return render_template('user/salesmanager/morningcall.html', selected_menu=USER_MORNING_CALL,
                           orders_stats=orders_stats, sales_stats=sales_stats, appts_count=appts_count,
                           total_rx_count=total_counts, recent_campaigns=recent_campaigns,
                           recent_campaigns_count=len(recent_campaigns), current_month_ta=current_month_ta,
                           rx_base_url=rx_base_url, rx_url_params=rx_url_params, appt_base_url=appt_base_url,
                           appt_url_params=appt_url_params, rx_incomplete_params=rx_incomplete_params,
                           order_base_url=order_base_url, order_url_params=order_url_params,
                           monthly_order_url_params=monthly_order_url_params, rx_stats=rx_stats,
                           back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/ec', methods=['GET'])
@UserPermission()
def evening_call():
    current_user = g.user
    store_id = get_or_set_store_id()

    today = datetime.date.today()
    orders_stats = dict()
    orders_stats['today_orders_count'] = Order.count_orders_by_date_and_store(datetime.date.today(), store_id)
    orders_stats['current_month_orders_count'] = Order.count_orders_from_date_and_store(
        datetime.date.today().replace(day=1),
        store_id)
    current_month_ta = TaSetting.find_active_monthly_ta(today.year, today.month, store_id)
    orders_stats['current_month_target'] = current_month_ta.value if current_month_ta else 'N/A'

    sales_stats = User.get_all_sales_by_store_from_cache(long(store_id))
    today_receptions = Reception.find_all_of_today_in_store(store_id)
    today_appointments = Appointment.find_all_by_date_in_store(datetime.date.today(), store_id)
    tomorrow_appointments = Appointment.find_all_by_date_in_store(datetime.date.today() + datetime.timedelta(days=1),
                                                                  store_id)
    total_counts, sales_counts = calc_reception_counts(today_receptions, sales_stats)

    for sale in sales_stats:
        populate_appt_count_agg_by_sale_and_type(today_appointments, sale, include_closed=True)
        populate_appt_count_agg_by_sale_and_type(tomorrow_appointments, sale, attr_prefix='tomorrow_')
        sale.rx_count = sales_counts.get(sale.id, {'total': 0, 'new': 0, 'appt_new': 0, 'appt': 0, 'other': 0})

    appts_count = generate_appt_count_agg_by_type(today_appointments, include_closed=True)
    tomorrow_appts_count = generate_appt_count_agg_by_type(tomorrow_appointments)

    sales_stats.sort(key=lambda sale: sale.rx_count, reverse=True)

    rx_stats = {'today_incomplete_count': len([x for x in today_receptions if x.status != 'completed'])}

    appt_stats = dict()
    appt_stats['instore'] = len([x for x in today_appointments if x.status != 'cancelled' and x.type == 'instore'])
    appt_stats['open_instore'] = len([x for x in today_appointments if x.status == 'opened' and x.type == 'instore'])
    appt_stats['followup'] = len([x for x in today_appointments if x.type == 'followup'])
    appt_stats['open_followup'] = len([x for x in today_appointments if x.status == 'opened' and x.type == 'followup'])

    now = datetime.datetime.now()
    tomorrow_datetime = now + datetime.timedelta(days=1)
    current_endpoint = 'user.evening_call'

    rx_base_url, rx_url_params = get_filter_link('receptions.receptions', now, now, current_endpoint)
    rx_incomplete_params = rx_url_params.copy()
    rx_incomplete_params['status_filter'] = 'in-store'
    appt_base_url, appt_url_params = get_filter_link('appointments.appts', now, now, current_endpoint)

    tomorrow_appt_base_url, tomorrow_appt_url_params = get_filter_link('appointments.appts', tomorrow_datetime,
                                                                       tomorrow_datetime,
                                                                       current_endpoint)

    recent_campaigns = Campaign.find_all_by_store_in_recent_days(store_id, 15)

    order_base_url, order_url_params = get_filter_link('orders.orders', now, now, current_endpoint)
    monthly_order_url_params = order_url_params.copy()
    monthly_order_url_params['start_date'] = datetime.date.today().replace(day=1).strftime(DATE_FORMAT)
    monthly_order_url_params['end_date'] = now.strftime(DATE_FORMAT)

    return render_template('user/salesmanager/eveningcall.html', selected_menu=USER_EVENING_CALL, rx_stats=rx_stats,
                           orders_stats=orders_stats, today_receptions_count=len(today_receptions),
                           rx_incomplete_params=rx_incomplete_params,
                           sales_stats=sales_stats, appts_count=appts_count, total_rx_count=total_counts,
                           tomorrow_appts_count=tomorrow_appts_count, recent_campaigns=recent_campaigns,
                           recent_campaigns_count=len(recent_campaigns), rx_base_url=rx_base_url,
                           rx_url_params=rx_url_params, order_base_url=order_base_url,
                           tomorrow_appt_base_url=tomorrow_appt_base_url,
                           tomorrow_appt_url_params=tomorrow_appt_url_params,
                           order_url_params=order_url_params, appt_stats=appt_stats, appt_base_url=appt_base_url,
                           appt_url_params=appt_url_params,
                           monthly_order_url_params=monthly_order_url_params,
                           back_endpoint=request.args.get('back_endpoint', None))


def populate_appt_count_agg_by_sale_and_type(appt_list, sale, attr_prefix=None, include_closed=None):
    attr_followup_appt_count = 'followup_appt_count'
    attr_instore_appt_count = 'instore_appt_count'
    attr_deliver_appt_count = 'deliver_appt_count'

    if attr_prefix:
        attr_followup_appt_count = attr_prefix + attr_followup_appt_count
        attr_instore_appt_count = attr_prefix + attr_instore_appt_count
        attr_deliver_appt_count = attr_prefix + attr_deliver_appt_count

    followup_per_sale = filter(lambda appt: appt.sales_id == sale.id and appt.type == 'followup',
                               appt_list)
    setattr(sale, attr_followup_appt_count, len(followup_per_sale) if followup_per_sale else 0)

    instore_per_sale = filter(lambda appt: appt.sales_id == sale.id and appt.type == 'instore',
                              appt_list)
    setattr(sale, attr_instore_appt_count, len(instore_per_sale) if instore_per_sale else 0)

    deliver_per_sale = filter(lambda appt: appt.sales_id == sale.id and appt.type == 'deliver',
                              appt_list)
    setattr(sale, attr_deliver_appt_count, len(deliver_per_sale) if deliver_per_sale else 0)

    if include_closed:
        closed_followup_per_sale = filter(
            lambda appt: appt.sales_id == sale.id and appt.type == 'followup' and appt.status == 'cancelled',
            appt_list)

        setattr(sale, 'closed_' + attr_followup_appt_count,
                len(closed_followup_per_sale) if closed_followup_per_sale else 0)

        closed_instore_per_sale = filter(
            lambda appt: appt.sales_id == sale.id and appt.type == 'instore' and appt.status == 'closed',
            appt_list)
        setattr(sale, 'closed_' + attr_instore_appt_count,
                len(closed_instore_per_sale) if closed_instore_per_sale else 0)

        closed_deliver_per_sale = filter(
            lambda appt: appt.sales_id == sale.id and appt.type == 'deliver' and appt.status == 'closed',
            appt_list)
        setattr(sale, 'closed_' + attr_deliver_appt_count,
                len(closed_deliver_per_sale) if closed_deliver_per_sale else 0)


def generate_appt_count_agg_by_type(appt_list, include_closed=None):
    appts_count = dict()
    followup_appts = filter(lambda appt: appt.type == 'followup', appt_list)
    appts_count['followup'] = len(followup_appts) if followup_appts else 0
    instore_appts = filter(lambda appt: appt.type == 'instore', appt_list)
    appts_count['instore'] = len(instore_appts) if instore_appts else 0
    deliver_appts = filter(lambda appt: appt.type == 'deliver', appt_list)
    appts_count['deliver'] = len(deliver_appts) if deliver_appts else 0

    if include_closed:
        actual_followup_appts = filter(lambda appt: appt.type == 'followup' and appt.status == 'cancelled', appt_list)
        appts_count['closed_followup'] = len(actual_followup_appts) if actual_followup_appts else 0
        actual_instore_appts = filter(lambda appt: appt.type == 'instore' and appt.status == 'closed', appt_list)
        appts_count['closed_instore'] = len(actual_instore_appts) if actual_instore_appts else 0
        actual_deliver_appts = filter(lambda appt: appt.type == 'deliver' and appt.status == 'closed', appt_list)
        appts_count['closed_deliver'] = len(actual_deliver_appts) if actual_deliver_appts else 0

    return appts_count


def set_status_label_and_style(sales):
    if sales.status == 'free':
        sales.status_label = u'空闲'
        sales.status_label_css = 'label-success'
    elif sales.status == 'busy':
        sales.status_label = u'忙碌'
        sales.status_label_css = 'label-warning'
    else:
        sales.status_label = u'待岗'
        sales.status_label_css = 'label-defualt'


class ReceptionCounts(object):
    def __init__(self):
        self.total = 0
        self.new = 0
        self.appt_new = 0
        self.appt = 0
        self.other = 0


def calc_reception_counts(receptions, sales):
    total_counts = ReceptionCounts()

    reception_counts = dict()
    sales_ids = [x.id for x in sales]
    for reception in receptions:
        sales_id = reception.sales_id
        rx_type = reception.rx_type
        if sales_id in sales_ids:
            total_counts.total = total_counts.total + 1

            sales_count = reception_counts.get(sales_id, ReceptionCounts())
            sales_count.total = sales_count.total + 1
            if rx_type == 'new':
                sales_count.new = sales_count.new + 1
                total_counts.new = total_counts.new + 1
            elif rx_type == 'appt_new':
                sales_count.appt_new = sales_count.appt_new + 1
                total_counts.appt_new = total_counts.appt_new + 1
            elif rx_type == 'appt':
                sales_count.appt = sales_count.appt + 1
                total_counts.appt = total_counts.appt + 1
            else:
                sales_count.other = sales_count.other + 1
                total_counts.other = total_counts.other + 1

            reception_counts[sales_id] = sales_count

    return total_counts, reception_counts


def get_filter_link(endpoint, start_date, end_date, back_endpoint=None):
    if not isinstance(start_date, datetime.datetime):
        start_date = datetime.datetime.now()

    if not isinstance(end_date, datetime.datetime):
        end_date = datetime.datetime.now()

    url_params = dict()
    url_params['start_date'] = start_date.strftime(DATE_FORMAT)
    url_params['end_date'] = end_date.strftime(DATE_FORMAT)
    if back_endpoint:
        url_params['back_endpoint'] = back_endpoint
    base_url = endpoint
    return base_url, url_params
