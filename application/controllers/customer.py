# -*- coding: utf-8 -*-
from application.controllers._helper import flash_success
from application.forms.customer import CustomerReassignForm
from application.forms.mixins import SortMixin
from application.models.appointment import Appointment
from application.models.calllog import Calllog
from application.models.customer import Customer
from application.models.order import Order
from application.models.reception import Reception
from application.models.user import USER_ROLE_STORE_MANAGER
from application.nutils.menu import CUSTOMER_MGMT
from application.nutils.url import back_url
from application.pagination import get_page_info
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from application.utils import get_sales_selection, get_selections_by_lookup_name
from werkzeug.exceptions import abort
from flask import Blueprint, render_template, g, request, redirect, url_for

bp = Blueprint('customers', __name__, url_prefix="/customers")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def customers():
    current_user = g.user
    store_id = get_or_set_store_id()

    from application.forms.customer import CustomerSearchForm
    search_form = CustomerSearchForm(request.args)
    search_form.intent_level_filter.choices = get_intent_level_selection(store_id)
    search_form.intent_car_ids_filter.choices = get_intent_car_ids_selection(store_id)
    search_form.last_instore_filter.choices = get_last_instore_selection(store_id)
    search_form.status_filter.choices = get_status_selection()
    search_form.sales_filter.choices = get_sales_selection(store_id)

    # build query
    query = dict()
    if search_form.intent_level_filter.data not in ('None', 'all'):
        query['intent_level'] = search_form.intent_level_filter.data
    if search_form.intent_car_ids_filter.data not in ('None', 'all'):
        query['intent_car_ids'] = search_form.intent_car_ids_filter.data
    if search_form.last_instore_filter.data not in ('None', 'all'):
        query['last_instore'] = search_form.last_instore_filter.data
    if search_form.status_filter.data not in ('None', 'all'):
        query['status'] = search_form.status_filter.data
    if search_form.keywords.data:
        query['keywords'] = search_form.keywords.data
    if search_form.sales_filter.data not in ('None', 'all'):
        query['sales_id'] = search_form.sales_filter.data

    if not current_user.has_role_in_current_store(USER_ROLE_STORE_MANAGER):
        query.pop('sales_id', None)

    # TODO:
    scope = current_user.getDataScope('customer', store_id)
    if scope:
        scope.pop('store_id', None)
        query.update(scope)

    sort_params = SortMixin.get_order_query(search_form)
    if sort_params:
        query.update(sort_params)

    query.update(get_page_info(request))

    customers_list = Customer.find_all_with_last_appt_by_query_params_in_store(store_id, **query)
    return render_template('customers/customers.html', selected_menu=CUSTOMER_MGMT, form=search_form,
                           customers=customers_list, back_endpoint=request.args.get('back_endpoint', None))


def get_intent_level_selection(store_id):
    selections = [(u'all', u'购买周期')]
    selections.extend(get_selections_by_lookup_name(store_id, 'intent-level'))
    return selections


def get_intent_car_ids_selection(store_id):
    selections = [('all', u'意向车型')]
    selections.extend(get_selections_by_lookup_name(store_id, 'intent-car'))
    return selections


def get_last_instore_selection(store_id):
    selections = [('all', u'到店时间'), ('0', u'今天')]
    selections.extend(get_selections_by_lookup_name(store_id, 'last-instore'))
    return selections


def get_status_selection():
    selections = [('all', u'客户状态'), ('draft', u'待完善资料'), ('formal', u'待跟进'), ('enlist', u'跟进中'), ('defeated', u'休眠'),
                  ('ordered', u'已成交')]

    return selections


@bp.route('/<int:cid>', methods=['GET', 'POST'])
@UserPermission()
def view_details(cid):
    current_user = g.user
    store_id = get_or_set_store_id()

    customer = Customer.find_by_id_and_store(cid, store_id)

    if not customer:
        abort(404)

    orders = Order.find_all_by_customer_sales(customer.id)
    appts = Appointment.find_all_by_customer_sales(customer.id)
    receptions = Reception.find_all_by_customer_sales(customer.id)
    calllogs = Calllog.find_all_by_customer_id(customer.id)

    form = CustomerReassignForm()
    form.saleses_list.choices = get_sales_selection(store_id)

    if current_user.is_receptionist() or (current_user.is_sales() and current_user.is_role_in_store_id(store_id,
                                                                                                       'manager') == False and customer.sales_id != current_user.id):
        abort(401)

    if request.method == 'GET':
        form.saleses_list.data = customer.sales_id

    if request.method == 'POST' and (
            form.saleses_list.data not in ('None', customer.sales_id) and current_user.is_role_in_store_id(store_id,
                                                                                                           'manager')):
        customer.reassign(int(form.saleses_list.data))
        customer.save_and_flush()
        flash_success(u'重新分配成功')
        return redirect(
            url_for('customers.view_details', cid=cid, back_url=back_url(url_for('customers.customers'))),
            code=303)

    return render_template('customers/detail.html', selected_menu=CUSTOMER_MGMT, customer=customer, orders=orders,
                           appts=appts, receptions=receptions, calllogs=calllogs, form=form,
                           back_url=back_url(url_for('customers.customers')))
