# -*- coding: utf-8 -*-
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.exceptions import NoPermissionOnCustomerException


def populate_customer_from_request(data, store_id, user_id):
    from application.models.customer import Customer

    customer_id = extract_customer_id(data)
    customer_data = data.get('customer')
    customer = None

    if not customer_id and not customer_data:
        abort(400, description=gettext('either customer_id or customer has to be provided'))
    elif customer_id:
        customer = Customer.find(customer_id)
        if not customer:
            abort(400, description=gettext('customer with id %(id)s is not found', id=data['customer_id']))
        elif unicode(customer.sales_id) != unicode(user_id) and data.get('force', None) != 'force':
            raise NoPermissionOnCustomerException(customer, gettext(
                u'the customer %(name)s you are operating does not belong to you. Please contact your sales manager',
                name=customer.name))
    else:
        if customer_data.get('mobile', None):
            customer = Customer.find_by_mobile(store_id, customer_data['mobile'])

        customer = handle_no_rx_customer(customer)

        if customer and unicode(customer.sales_id) != unicode(user_id) and data.get('force', None) != 'force':
            raise NoPermissionOnCustomerException(customer, gettext(
                u'the customer %(name)s you are operating does not belong to you. Please contact your sales manager',
                name=customer.name))

        if not customer:
            customer = Customer(**customer_data)
            customer.store_id = store_id
            customer.sales_id = user_id

    data['customer'] = customer
    return data


def handle_no_rx_customer(existing_customer):
    from application.models.user import INSTORE_NO_RX_LEAD
    if existing_customer and existing_customer.sales and existing_customer.sales.username == INSTORE_NO_RX_LEAD:
        # if existing customer belongs to NO_RX_LEAD, cancel it and ignore this customer
        existing_customer.status = 'cancelled'
        return None
    else:
        return existing_customer


def extract_customer_id(data):
    customer_id = data.get('customer_id')

    if not customer_id:
        customer = data.get('customer', None)
        if customer:
            customer_id = customer.get('id')

    return customer_id
