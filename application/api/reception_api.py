# -*- coding: utf-8 -*-
from datetime import datetime

from application.api import api
from application.api.viewhelper import populate_customer_from_request
from application.exceptions import IncorrectSalesAssignmentException, NoPermissionOnCustomerException
from application.models.appointment import Appointment
from application.models.base import get_user_id
from application.models.customer import Customer
from application.models.reception import Reception
from application.models.user import User, SalesStatus
from application.events import new_reception_created, reception_cancelled
from application.utils import add_location_header, obj_to_dict, convert_int
from config import Config
from flask import request, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort


@api.route('/receptions', methods=['POST'])
def create_reception():
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    try:
        populate_customer_from_request(data, data.get('store_id'), data.get('sales_id'))
    except NoPermissionOnCustomerException, npe:
        raise IncorrectSalesAssignmentException(
            gettext(u'the customer belongs to %(sales_name)s, force assign to %(new_sales)s',
                    sales_name=npe.customer.sales.username, new_sales=User.find(data.get('sales_id')).username))

    reception = Reception(**data)
    # default receptionist_id if not passed from client
    if convert_int(reception.receptionist_id) <= 0:
        reception.receptionist_id = get_user_id()
    reception.customer.enlist()

    reception.created_on = datetime.now()
    reception.customer.last_reception_date = reception.created_on

    if reception.appointment_id is not None:
        appt = Appointment.find(reception.appointment_id)
        if not appt:
            reception.appointment_id = None
        else:
            if appt.type == 'deliver':
                reception.rx_type = 'other'
            elif not Reception.has_reception_before(appt.customer.id):
                reception.rx_type = 'appt_new'
            else:
                reception.rx_type = 'appt'
            appt.status = 'closed'

    reception.save_and_flush()

    new_reception_created.send(new_reception=reception)

    return reception, 201, add_location_header(dict(), url_for('api.get_reception', uid=reception.id))


@api.route('/receptions/<int:uid>', methods=['GET'])
def get_reception(uid):
    result = Reception.find(uid)

    if result is None:
        abort(404, description=gettext(u'reception with id %(id)s is not found', id=uid))
    return result


@api.route('/receptions/<int:uid>', methods=['PATCH', 'POST'])
def update_reception(uid):
    original_reception = get_reception(uid)

    data = request.json
    # only support update sales assignment for now
    if data is None or data.get('sales_id', None) is None:
        abort(400, description=gettext('invalid json request'))

    new_assigned_sales = User.find(data['sales_id'])
    if new_assigned_sales is None:
        abort(400, description=gettext('salespeople with id %(id)s is not found', id=data['sales_id']))

    # cancel original reception
    original_reception.status = 'cancelled'
    # update customer associate sales if the reception is not created from an appointment and customer is created today.
    new_customer = None
    if (not original_reception.appointment_id) \
            and original_reception.customer.created_on.date() == datetime.today().date():
        # create new customer from old one
        new_customer_dict = obj_to_dict(original_reception.customer)
        new_customer_dict.pop('id')
        new_customer_dict.pop('last_reception_date')
        new_customer_dict.pop('next_appointment_date')
        new_customer_dict['sales_id'] = data['sales_id']
        new_customer = Customer(**new_customer_dict)
        # cancel original customer
        original_reception.customer.status = 'cancelled'

    original_reception.save_and_flush()
    reception_cancelled.send(reception=original_reception)

    # create new reception
    new_reception_dict = obj_to_dict(original_reception)
    new_reception_dict.pop('id')
    new_reception_dict.pop('status')

    if new_customer:
        new_reception_dict.pop('customer_id')
        new_reception_dict['customer'] = new_customer

    new_reception_dict.pop('sales')
    new_reception_dict['sales_id'] = new_assigned_sales.id

    new_reception = Reception(**new_reception_dict)
    new_reception.prev_rx_id = original_reception.id
    new_reception.created_on = datetime.now()
    new_reception.customer.last_reception_date = new_reception.created_on
    new_reception.save_and_flush()

    new_reception_created.send(new_reception=new_reception)
    return new_reception


@api.route('/receptions/<int:uid>/status', methods=['PUT', 'POST'])
def change_reception_status(uid):
    status = request.json.get('name')

    if status is None:
        abort(400, description=gettext('status name is empty'))
    elif status not in Reception.valid_status:
        abort(400, description=gettext('status %(status)s is not valid', status=status))
    else:
        result = get_reception(uid)
        if result.status == status or result.status in ('completed', 'cancelled'):
            return result
        else:
            if status == 'completed' and result.customer.status == 'draft':
                abort(400, description=gettext('the customer can NOT be draft before completing reception'))

            if status == 'completed':
                result.complete()
            elif status == 'cancelled':
                if result.appointment_id is not None:
                    abort(400, description=gettext('the reception comes from appointment, cannot be cancelled'))
                else:
                    result.status = status
                    cancel_cusstomer(result.customer)
            else:
                result.status = status

            if status in ('completed', 'cancelled'):
                close_appointment_before(result)
                if result.rx_type != 'other':
                    update_customer_status(result.customer, result.sales)
                SalesStatus.update_sales_status(result.store_id, result.sales_id)

                # commit db before invoke async process
                result.save_and_commit()
                from application.models.hwaccount import HwjdAccount
                if result.customer and result.customer.status != 'defeated' and result.store_id in \
                        HwjdAccount.find_active_hwjd_store_ids():
                    from application.queue import async_call
                    async_call("sync_hwjd_customer_rx", [result.id])

            return result


def close_appointment_before(reception):
    if not reception.customer_id:
        return

    if reception.rx_type == 'other':
        appt_type = 'deliver'
    else:
        appt_type = 'instore'

    today_appts = Appointment.find_all_opened_by_type_and_date_of_sales_customer(appt_type, datetime.today().date(),
                                                                                 reception.sales_id,
                                                                                 reception.customer_id)

    for appt in today_appts:
        appt.status = 'closed'


def update_customer_status(customer, sales):
    if customer.status == 'enlist' and not Appointment.exist_opened_of_sales_customer(sales.id, customer.id):
        customer.status = 'formal'


def cancel_cusstomer(customer):
    if customer.created_on.date() == datetime.today().date():
        customer.status = 'cancelled'
        customer.save_and_flush()


@api.route('/stores/<int:store_id>/receptions/today', methods=['GET'])
def get_today_receptions(store_id):
    return Reception.find_all_of_today_in_store(store_id)


@api.route('/sales/<int:sale_id>/receptions/today/<status>', methods=['GET'])
def get_today_receptions_by_status_of_sales(sale_id, status):
    return Reception.find_all_of_today_of_sales_by_status(sale_id, status)


@api.route('/customers/<int:customer_id>/receptions', methods=['GET'])
def get_customer_receptions(customer_id):
    sales_id = request.args.get("sales_id", None)
    return Reception.find_all_by_customer_sales(customer_id, sales_id)
