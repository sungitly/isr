# -*- coding: utf-8 -*-
import datetime

from flask import request, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.api import api
from application.api.viewhelper import handle_no_rx_customer
from application.exceptions import DuplicatedCustomerException, NoPermissionOnCustomerException, EmptyRequiredFields
from application.models.appointment import Appointment
from application.models.base import get_or_create
from application.models.calllog import Calllog
from application.models.customer import Customer, validate_required_fields, CustomerAddlInfo
from application.models.order import Order
from application.models.reception import Reception
from application.models.salestracker import SalesTracker
from application.models.user import User
from application.nutils.numbers import parse_int
from application.pagination import get_page_info
from application.utils import add_location_header, validate_mobile


@api.route('/customers/<int:uid>', methods=['PUT', 'POST'])
def update_customer(uid):
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    # do not allow to update customer id and status directly
    Customer.filter_not_updatable_fields(data)
    customer = get_customer(uid)

    # validate mobile. The logic is duplicated with validate method of Customer. Merge the logic later.
    if data.get('mobile', None) and '000' != data['mobile'] and validate_mobile(data['mobile']):
        existing_cust_with_same_mobile = Customer.find_by_mobile_exclude(customer.store_id, data['mobile'],
                                                                         customer.id)
        existing_cust_with_same_mobile = handle_no_rx_customer(existing_cust_with_same_mobile)
        if existing_cust_with_same_mobile:
            if customer.sales_id == existing_cust_with_same_mobile.sales_id:
                raise DuplicatedCustomerException(gettext(u'The mobile is the same as customer %(name)s',
                                                          name=existing_cust_with_same_mobile.respect_name),
                                                  existing_customer_id=existing_cust_with_same_mobile.id)
            else:
                raise NoPermissionOnCustomerException(existing_cust_with_same_mobile,
                                                      gettext(u'The mobile belongs to other sales\' customer'))

    is_defeated = Customer.is_defeated(data)
    if not is_defeated:
        # validate required fields if client ask for it.
        if customer.status != 'draft':
            data['required_validation'] = True
        if not validate_required_fields(data):
            raise EmptyRequiredFields(gettext(u'Please fill all required fields'))

    create_or_update_addl_info(customer, data)

    for key, value in data.iteritems():
        if hasattr(customer, key):
            try:
                setattr(customer, key, value)
            except:
                # ignore the errors here
                pass

    if not is_defeated:
        customer.formal()
        from application.models.hwaccount import HwjdAccount
        if customer.store_id in HwjdAccount.find_active_hwjd_store_ids():
            last_rx = Reception.find_last_rx_by_customer_id(customer.id)
            if last_rx:
                from application.queue import async_call
                async_call("sync_hwjd_customer_rx", [last_rx.id])
    else:
        customer.defeated('NA')

    return customer


@api.route('/customers/<int:uid>', methods=['GET'])
def get_customer(uid):
    result = Customer.find_with_addl(uid)

    if result is None:
        abort(404, description=gettext(u'customer with id %(id)s is not found', id=uid))
    return result


@api.route('/sales/<int:sales_id>/customers', methods=['GET'])
def get_customers_of_sales(sales_id):
    return Customer.find_all_by_sales(sales_id, **get_page_info(request))


@api.route('/sales/<int:sales_id>/customers/sync')
def sync_customers_of_sales(sales_id):
    last_sync_date = request.args.get('last_sync_date', None)
    try:
        last_sync_date = datetime.datetime.fromtimestamp(int(last_sync_date))
    except:
        last_sync_date = None

    bulk_size = parse_int(request.args.get('bulk_size', None), 100)
    return Customer.find_all_by_sales_before_sync_in_bulk(sales_id, last_sync_date, bulk_size)


@api.route('/sales/<int:sales_id>/customers/tbu')
def get_tbu_customers_of_sales(sales_id):
    return Customer.find_all_in_tbu_by_sales(sales_id)


@api.route('/customers/<int:customer_id>/defeated', methods=['PUT', 'POST'])
def mark_customer_defeated(customer_id):
    reason = request.json.get('reason')

    if reason is None:
        abort(400, description=gettext('defeated reason is empty'))
    else:
        result = get_customer(customer_id)
        result.defeated(reason)
        return result


@api.route('/customers/<int:customer_id>/intent', methods=['PUT', 'POST'])
def update_customer_intent(customer_id):
    intent_level = request.json.get('intent_level')

    customer = get_customer(customer_id)

    customer.intent_level = intent_level

    return customer


@api.route("/customers/<int:cid>/replaced", methods=['PUT', 'POST'])
def cancel_customer(cid):
    replaced_by_customer_id = request.json.get('by_customer_id')

    customer = get_customer(cid)
    customer.status = 'cancelled'
    customer.save_and_flush()

    replaced_by_customer = get_customer(replaced_by_customer_id)

    Appointment.reset_customer_id(customer, replaced_by_customer)
    Reception.reset_customer_id(customer, replaced_by_customer)
    Order.reset_customer_id(customer, replaced_by_customer)

    return replaced_by_customer


@api.route('/stores/<int:sid>/customers', methods=['GET'])
def get_all_store_customers(sid):
    status = request.args.get('status', None)
    return Customer.find_all_by_store_in_status(sid, status, **get_page_info(request))


@api.route('/customers/<int:cid>/reassign', methods=['POST'])
def assign_customer(cid):
    customer = Customer.find(cid)
    if customer is None:
        abort(400, description=gettext(u'customer with id %(id)s is not found', id=cid))

    new_sales_id = request.json.get('sales_id')
    if new_sales_id is None:
        abort(400, description=gettext(u'new sales id is empty'))

    customer.reassign(new_sales_id)
    return customer


@api.route('/stores/<int:store_id>/customers/reassign', methods=['POST'])
def bulk_assign_store_customers(store_id):
    # currently only support bulk reassign defeated customers by last reception date
    new_sales_id = request.json.get('sales_id')
    if new_sales_id is None:
        abort(400, description=gettext(u'new sales id is empty'))

    rx_date_from = request.json.get('rx_date_from')
    rx_date_to = request.json.get('rx_date_to')
    if not rx_date_from or not rx_date_to:
        abort(400, description=u"rx_date_from or rx_date_to can't be empty")

    customers = Customer.find_all_defeated_in_store_by_last_reception_date(store_id, rx_date_from, rx_date_to)

    for customer in customers:
        customer.reassign(new_sales_id)

    return customers


@api.route('/sales/<int:sid>/customers/<int:cid>/accept', methods=['PATCH', 'POST', 'GET'])
def accept_reassign_customer(sid, cid):
    customer = Customer.find(cid)
    if customer is None or customer.sales_id != sid:
        abort(400, description=gettext(u'customer with id %(id)s is not found or not belongs to sales %(sid)s', id=cid,
                                       sid=sid))
    customer.reassigned = 0
    return customer


@api.route('/stores/<int:cid>/customers/search', methods=['POST'])
def search_customer(cid):
    mobile = request.json.get('mobile', None)
    if mobile:
        customer = Customer.find_by_mobile_with_sales_in_store(mobile, cid)
        return customer
    else:
        abort(400, description=gettext(u'Customer with mobile %(mobile)s not found', mobile=mobile))

    abort(400, description=gettext(u'Mobile is empty'))


@api.route("/sales/<int:sales_id>/customers/reassigned", methods=['POST'])
def get_all_reassigned_customers(sales_id):
    start_time = request.json.get('start_time', None)
    if start_time:
        return SalesTracker.find_all_by_sales_with_start_date(sales_id, start_time)
    else:
        return SalesTracker.find_all_by_from_sales(sales_id)


@api.route('/sales/<int:sales_id>/customers', methods=['POST', 'PUT'])
def create_customer(sales_id):
    sales = User.get_user_by_id_from_cache(sales_id)

    if sales is None:
        abort(400, description=gettext(u'Incorrect sales, cannot find sales with id %(id)'), id=sales_id)

    data = request.json
    customer = None
    if data.get('mobile', None):
        customer = Customer.find_by_mobile(sales.store_id, data['mobile'])
        from application.api.viewhelper import handle_no_rx_customer
        customer = handle_no_rx_customer(customer)

    if customer:
        if customer.sales_id != sales.id:
            raise NoPermissionOnCustomerException(customer,
                                                  gettext(u'The mobile belongs to other sales\' customer'))
        else:
            raise DuplicatedCustomerException(gettext(u'The mobile is the same as customer %(name)s',
                                                      name=customer.respect_name),
                                              existing_customer_id=customer.id)
    else:
        customer = Customer(**data)
        customer.store_id = sales.store_id
        customer.sales_id = sales.id
        customer.reset_status()
        customer.save_and_flush()

    return customer, 201, add_location_header(dict(), url_for('api.get_customer', uid=customer.id))


@api.route('/customers/<int:customer_id>/calllog', methods=['POST'])
def create_calllog(customer_id):
    customer = Customer.find(customer_id)

    if customer is None:
        abort(400, description=gettext(u'Customer with id %(id) not found', id=customer))

    data = request.json
    data.pop('id', None)
    data.pop('created_on', None)
    data.pop('updated_on', None)
    sequence_id = data.get('sequence_id', None)

    call_log = None
    if sequence_id:
        call_log = Calllog.find_by_sequence_id(sequence_id)

    if not call_log:
        call_log = Calllog(**data)

    call_log.customer_id = customer_id
    call_log.store_id = customer.store_id

    call_log.save_and_flush()
    return call_log


@api.route("/sales/<int:sales_id>/customers/search", methods=['POST'])
def search_sales_customer(sales_id):
    sales = User.get_user_by_id_from_cache(sales_id)
    data = request.json
    mobile = data.get('mobile', None)
    if mobile:
        customer = Customer.find_by_mobile(sales.store_id, mobile)
        if customer:
            if customer.sales_id == sales.id:
                return customer
            else:
                raise NoPermissionOnCustomerException(customer,
                                                      gettext(u'The mobile belongs to other sales\' customer'))
        else:
            abort(400, description=gettext(u'Customer with mobile %(mobile)s not found', mobile=mobile))
    else:
        abort(400, description=gettext(u'Mobile is empty'))


def create_or_update_addl_info(customer, customer_data_with_addl_info):
    # TODO: abstract relationship object population to BaseMixin
    addl_info, created = get_or_create(CustomerAddlInfo, customer_id=customer.id)
    addl_info.customer_id = customer.id

    for key in CustomerAddlInfo.attributes_names(CustomerAddlInfo.excludes_attrs()):
        if customer_data_with_addl_info.get(key, None):
            setattr(addl_info, key, customer_data_with_addl_info.get(key))
