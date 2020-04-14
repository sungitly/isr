# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from application.api import api
from application.api.viewhelper import populate_customer_from_request
from application.exceptions import NewAppointmentDateWarningExcetpion, OldAppointmentDateWarningExcetpion
from application.models.appointment import Appointment
from application.pagination import get_page_info
from application.utils import add_location_header
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from flask import request, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.validators import get_appt_validator


@api.route('/appointments', methods=['POST'])
def create_appointment():
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    # validate appointment time
    if data.get('appt_datetime', None) is None:
        abort(400, description=gettext('appointment datetime can not be empty'))

    appt_time = parse(data.get('appt_datetime'))
    now_time = datetime.now()
    if appt_time < now_time:
        abort(400, description=gettext('appointment datetime must later than now'))

    latest_time = now_time + timedelta(days=30)
    if appt_time > latest_time:
        abort(400, description=gettext('appointment datetime can not be later than 30 days'))

    populate_customer_from_request(data, data.get('store_id'), data.get('sales_id'))
    data.pop('id', None)

    validator = get_appt_validator(data.get('store_id'))
    if validator:
        validator.validate(data)

    if data.get('customer', None) and data['customer'].id:
        Appointment.cancel_all_for_sales_customer(data['sales_id'], data['customer'].id, "new appointment created")

    appt = Appointment(**data)
    appt.customer.enlist()

    appt.save_and_flush()

    return appt, 201, add_location_header(dict(), url_for('api.get_appointment', uid=appt.id))


@api.route('/appointments/<int:uid>', methods=['GET'])
def get_appointment(uid):
    result = Appointment.find(uid)

    if result is None:
        abort(404, description=gettext(u'appointment with id %(id)s is not found', id=uid))
    return result


@api.route('/stores/<int:store_id>/appointments/latest', methods=['GET'])
def get_latest_appointments_by_store(store_id):
    days = request.args.get('days', 4)
    start_date = date.today()
    end_date = start_date + relativedelta(days=(days - 1))

    return Appointment.find_all_between_dates_in_store(start_date, end_date, store_id)


@api.route('/stores/<int:store_id>/appointments', methods=['GET'])
def query_appointments_in_store(store_id):
    query_criteria = request.args.get('q')

    if query_criteria is None:
        return abort(404, description=gettext(u'query criteria can not be empty'))

    return Appointment.find_all_by_q_in_store(query_criteria, store_id)


@api.route('/sales/<int:sales_id>/appointments', methods=['GET'])
def get_appointments_by_sales(sales_id):
    return Appointment.find_all_of_sales(sales_id, **get_page_info(request))


@api.route('/sales/<int:sales_id>/appointments/sync')
def sync_appointments_of_sales(sales_id):
    last_sync_date = request.args.get('last_sync_date', None)
    try:
        last_sync_date = datetime.fromtimestamp(int(last_sync_date))
    except:
        last_sync_date = None

    bulk_size = request.args.get('bulk_size', None)
    return Appointment.find_all_by_sales_before_sync_in_bulk(sales_id, last_sync_date, bulk_size)


@api.route('/customers/<int:customer_id>/appointments', methods=['GET'])
def get_all_customer_appointments(customer_id):
    sales_id = request.args.get("sales_id", None)
    return Appointment.find_all_by_customer_sales(customer_id, sales_id)
