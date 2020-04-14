# -*- coding: utf-8 -*-
from decimal import Decimal

from application.api import api
from application.exceptions import ValidationException
from application.models.appointment import Appointment
from application.models.customer import Customer
from application.models.order import Order
from application.models.reception import Reception
from application.pagination import get_page_info
from application.utils import add_location_header
from flask import request, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort


@api.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    validate_amounts_fields_in_orders(data)
    order = Order(**data)

    order.generate_order_no()

    order.save_and_flush()

    customer = Customer.find(order.customer_id)
    customer.status = 'ordered'

    Appointment.cancel_all_for_sales_customer(order.sales_id, order.customer_id,
                                              'Order: ' + str(order.id) + ' is created')

    Reception.complete_all_for_sales_customer(order.sales_id, order.customer_id,
                                              'Order: ' + str(order.id) + ' is created')

    return Order.find(order.id), 201, add_location_header(dict(), url_for('api.get_order', uid=order.id))


@api.route('/orders/<int:uid>', methods=['GET'])
def get_order(uid):
    result = Order.find(uid)

    if result is None:
        return abort(404, description=gettext(u'Order with id %(id)s is not found', id=uid))
    return result


@api.route('/salespeople/<int:sales_id>/orders', methods=['GET'])
def get_orders_of_sales(sales_id):
    status = request.args.get('status')

    if status:
        return Order.find_all_in_status_by_sales(sales_id, status)
    else:
        return Order.find_all_by_sales(sales_id)


@api.route('/orders/<int:oid>', methods=['PUT', 'POST'])
def update_order(oid):
    result = Order.find(oid)
    if result is None:
        return abort(404, description=gettext(u'Order with id %(id)s is not found', id=id))

    if result.status in ('delivered', 'cancelled'):
        return abort(400, description=gettext(u'Cannot update delivered or cancelled order'))

    data = request.json
    new_status = data.get('status', 'new')

    result.status = new_status

    if result.status.lower() == 'cancelled':
        result.customer.reset_status()
    else:
        # FIXME use flask inputs to do validation
        validate_amounts_fields_in_orders(data)

        # update order data
        for key in Order.attributes_names(Order.excludes_attrs()):
            if data.get(key, None):
                setattr(result, key, data.get(key))

    # FIXME: disable delivered followup temporarily
    # if result.status.lower() == 'delivered':
    #     today = datetime.date.today()
    #     delivered_date = parse_date(result.delivered_date)
    #     if delivered_date >= today:
    #         # make two appointments
    #         Appointment.auto_make_delivered_followup_appointments(result)

    return result


def validate_amounts_fields_in_orders(data):
    for attr in Order.amount_fields:
        if data.get(attr, None):
            try:
                Decimal(data.get(attr))
            except:
                raise ValidationException(message=gettext('%(amount)s is an invalid number', amount=data.get(attr)))


@api.route('/stores/<int:sid>/orders', methods=['GET'])
def get_store_orders(sid):
    status = request.args.get('status')
    confirmed = request.args.get('confirmed')

    return Order.find_all_in_status_by_store(sid, status, confirmed, **get_page_info(request))


@api.route('/orders/<int:oid>/confirm', methods=["GET"])
def confirm_order(oid):
    order = Order.find(oid)

    if order is None:
        return abort(404, description=gettext(u'Order with id %(id)s is not found', id=oid))

    order.is_confirmed = True
    return order


@api.route('/customers/<int:customer_id>/orders', methods=["GET"])
def get_all_customer_orders(customer_id):
    sales_id = request.args.get("sales_id", None)
    return Order.find_all_by_customer_sales(customer_id, sales_id)
