# -*- coding: utf-8 -*-
from flask import request
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.api import api
from application.exceptions import InvalidSalesStatusTransitionException
from application.models.appointment import Appointment
from application.models.customer import Customer
from application.models.reception import Reception
from application.models.user import User, SalesStatus, SalesLastRxTime


@api.route('/stores/<int:store_id>/sales', methods=['GET'])
def get_sales(store_id):
    reset_sales_status = request.args.get('reset')

    if reset_sales_status:
        SalesStatus.reset_all_sales_status(store_id)

    sales = User.get_all_sales_by_store_from_cache(long(store_id))
    sales_status = SalesStatus.get_all_sales_status(store_id)
    sales_rxtime = SalesLastRxTime.get_all_sales_rxtime(store_id)

    for sale in sales:
        sale.status = sales_status.get(str(sale.id), 'free')
        sale.last_rxtime = sales_rxtime.get(str(sale.id), 0)

    sales.sort(key=lambda salesperson: salesperson.last_rxtime)
    return sales


@api.route('/stores/<int:store_id>/sales/status', methods=['PUT', 'POST'])
def change_sales_status(store_id):
    sales_status = request.json

    sales_status_mapping = dict()

    for status in sales_status:
        sales_status_mapping[status['id']] = status['status']
    SalesStatus.set_sales_status_from_mapping(store_id, sales_status_mapping)

    return get_sales(store_id)


@api.route('/sales/<int:uid>', methods=['GET'])
def get_salesperson(uid):
    result = User.find(uid)

    if result is None:
        return abort(404, description=gettext(u'salespeople with id %(id)s is not found', id=uid))
    return result


@api.route('/sales/<int:sales_id>/status', methods=['PUT', 'POST'])
def update_sales_status(sales_id):
    status = request.json.get('name')
    sales = User.find(sales_id)

    if not sales:
        abort(400, description=gettext(u'sales with id (%id)s is not found', id=sales_id))

    if status == 'free' and Reception.exist_sales_incomplete_receptions_of_today(sales_id):
        raise InvalidSalesStatusTransitionException(
            gettext(u'sales %(name)s can not be free because there is incomplete receptions', name=sales.username))
    else:
        SalesStatus.set_sales_status(sales.store_id, sales.id, status)
        return {sales_id: status}


@api.route('/sales/<int:from_sales_id>/transfer/<int:to_sales_id>')
def transfer_sales_customers(from_sales_id, to_sales_id):
    passcode = request.args.get('passcode', None)
    status = request.args.getlist('status')

    if not passcode or not valid_passcode(passcode):
        abort(401)

    from_sales = User.find(from_sales_id)
    if not from_sales or from_sales.is_active():
        abort(400, description=gettext(u'sales with id (%id)s is not found', id=from_sales_id))

    to_sales = User.find(to_sales_id)
    if not to_sales:
        abort(400, description=gettext(u'sales with id (%id)s is not found', id=to_sales_id))

    Appointment.cancel_all_for_sales(from_sales_id, u'重新分配客户')

    processed_count = Customer.reassign_all_of_sales_to_sales(from_sales_id, to_sales_id, status)

    return {'from_sales_id': from_sales_id, 'to_sales_id': to_sales_id, 'processed_count': processed_count}


@api.route('/stores/<int:from_store_id>/transfer/<int:to_store_id>')
def merge_stores(from_store_id, to_store_id):
    passcode = request.args.get('passcode', None)
    if not passcode or not valid_passcode(passcode):
        abort(401)

    result = dict()

    result['receptions'] = Reception.migrate_store(from_store_id, to_store_id)
    result['customers'] = Customer.migrate_store(from_store_id, to_store_id)
    result['appointments'] = Appointment.migrate_store(from_store_id, to_store_id)
    from application.models.order import Order
    result['orders'] = Order.migrate_store(from_store_id, to_store_id)
    from application.models.calllog import Calllog
    result['calllogs'] = Calllog.migrate_store(from_store_id, to_store_id)
    from application.models.campaign import Campaign
    result['campaigns'] = Campaign.migrate_store(from_store_id, to_store_id)
    from application.models.driverecord import DriveRecord
    result['driverecords'] = DriveRecord.migrate_store(from_store_id, to_store_id)

    return result


def valid_passcode(passcode):
    import hashlib
    import datetime
    return passcode == hashlib.sha256(datetime.datetime.now().strftime('%Y-%m-%d') + 'unicorn').hexdigest()
