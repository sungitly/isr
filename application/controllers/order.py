# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, g, redirect, url_for
from werkzeug.exceptions import abort

from application.controllers._helper import flash_error, flash_success
from application.forms.mixins import SortMixin
from application.forms.order import OrderCancelForm
from application.models.order import Order
from application.nutils.menu import ORDERS_MGMT
from application.pagination import get_page_info
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from application.utils import get_sales_selection, get_selections_by_lookup_name

bp = Blueprint('orders', __name__, url_prefix="/orders")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def orders():
    store_id = request.args.get('store_id', None)
    if not store_id:
        store_id = get_or_set_store_id()

    from application.forms.order import OrderSearchForm
    search_form = OrderSearchForm(request.args)
    search_form.ordered_car_ids_filter.choices = get_intent_car_ids_selection(store_id)
    search_form.sales_filter.choices = get_sales_selection(store_id)
    search_form.status_filter.choices = get_status_selection()

    # build query
    query = dict()
    if search_form.start_date.data and search_form.start_date.data != '':
        query['start_date'] = search_form.start_date.data
    if search_form.end_date.data and search_form.end_date.data != '':
        query['end_date'] = search_form.end_date.data
    if search_form.ordered_car_ids_filter.data not in ('None', 'all'):
        query['ordered_car_ids'] = search_form.ordered_car_ids_filter.data
    if search_form.sales_filter.data not in ('None', 'all'):
        query['sales_id'] = search_form.sales_filter.data
    if search_form.status_filter.data not in ('None', 'all'):
        query['status'] = search_form.status_filter.data
    if search_form.keywords.data:
        query['keywords'] = search_form.keywords.data
    if search_form.history.data:
        query['history'] = search_form.history.data

    sort_params = SortMixin.get_order_query(search_form)
    if sort_params:
        query.update(sort_params)

    query.update(get_page_info(request))

    cancel_form = OrderCancelForm()

    orders_list = Order.find_all_by_query_params_in_store(store_id, **query)
    return render_template('orders/orders.html', selected_menu=ORDERS_MGMT, form=search_form,
                           orders=orders_list, cancel_form=cancel_form,
                           back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/cancel', methods=['POST'])
@UserPermission()
def cancel_order():
    current_user = g.user
    store_id = get_or_set_store_id()
    form = OrderCancelForm()

    if form.order_id.data is None or int(form.order_id.data) < 1:
        flash_error(u'订单信息错误，请选择需要取消的订单')
    else:
        order = Order.find_by_id_and_store(form.order_id.data, store_id)

        if not order:
            abort(404)

        if order and order.status not in ('delivered', 'cancelled'):
            order.status = 'cancelled'
            order.save_and_flush()
            flash_success(u'订单已取消')
        elif order:
            flash_error(u'订单已交车或已取消')
        else:
            flash_error(u'找不到需要取消的订单')

    return redirect(url_for('orders.orders'))


def get_ordered_date_selection():
    selections = [('all', u'订单日期'), ('yesterday', u'昨天'), ('last_week', u'上周'), ('last_month', u'上个月')]

    return selections


def get_intent_car_ids_selection(store_id):
    selections = [('all', u'意向车型')]
    selections.extend(get_selections_by_lookup_name(store_id, 'intent-car'))
    return selections


def get_status_selection():
    selections = [('all', u'订单状态'), ('new', u'未交车'), ('delivered', u'已交车'), ('cancelled', u'已取消')]

    return selections
