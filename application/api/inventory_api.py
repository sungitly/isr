# -*- coding: utf-8 -*-

from application.api import api
from application.integration.frtinv import get_shared_inventories_details_by_subtype_code
from application.models.frtinv import FrtInventory, FrtSharedInventory
from application.models.inventory import Inventory
from application.models.setting import StoreSetting
from application.nutils.numbers import parse_float
from flask import request, current_app, g
from flask.ext.babel import gettext
from werkzeug.exceptions import abort


@api.route('/stores/<int:store_id>/inventories/provider', methods=['GET'])
def get_store_inventory_provider(store_id):
    return StoreSetting.find_all_by_store_and_type(store_id, StoreSetting.TYPE_INV_PROVIDER)


@api.route('/inventories/<int:inventory_id>/pub', methods=['GET'])
def publish_share_inventory(inventory_id):
    scope = request.args.get('scope', 'group')
    inv = FrtInventory.find(inventory_id)

    if inv is None:
        return abort(404)

    inv.shared = scope
    return inv


@api.route('/inventories')
def get_inventories():
    user = g.user

    settings = get_store_inventory_provider(user.store_id)
    if settings and settings[0].value == 'frt':
        return get_frt_stores_inventories(user.store_id)
    else:
        return get_uinv_stores_inventories(user.store_id, fuzzy=True)


@api.route('/inventories/<int:uid>/repr')
def get_inventory_for_display(uid):
    result = Inventory.find(uid)
    if result is None:
        abort(404, description=gettext(u'inventory with id %(id)s is not found', id=uid))

    result = result.repr_dict()
    return result


@api.route('/inventories/<int:uid>', methods=['PUT', 'POST'])
def update_inventory(uid):
    data = request.json
    if not data:
        abort(400, description=gettext('invalid json request'))

    inv = Inventory.find_by_id_and_store(uid, g.user.store_id)
    inv.inv_status = data.get('inv_status', None)
    inv.rebate_amt = parse_float(data.get('rebate_amt', None))
    inv.remark = data.get('remark', None)
    return inv


# uinv inventory api
@api.route('/stores/<int:store_id>/inventories/uinv/lookups', methods=['GET'])
def get_uinv_stores_inventories_lookups(store_id):
    type = request.args.get('type', 'store')

    return Inventory.get_lookups(store_id, type)


@api.route('/stores/<int:store_id>/inventories/uinv', methods=['GET'])
def get_uinv_stores_inventories(store_id, fuzzy=False):
    invs = Inventory.find_all_by_criteria_in_store(fuzzy, store_id, **request.args.to_dict())
    return invs


# frt inventory api

MOCK_ORDERS_COUNT = {
    '120102003': 1,
    '120103002': 0,
    '120104001': 5,
    '120104002': 18,
    '120104004': 4,
    '120105001': 2,
}

MOCK_STORE_LEEDS_COUNT = {
    '120102003': 72,
    '120103002': 0,
    '120104001': 35,
    '120104002': 87,
    '120104004': 3,
    '120105001': 49,
}

MOCK_GROUP_LEEDS_COUNT = {
    '120102003': 521,
    '120103002': 6,
    '120104001': 483,
    '120104002': 647,
    '120104004': 39,
    '120105001': 355,
}

MOCK_NET_LEEDS_COUNT = {
    '120102003': 25,
    '120103002': 0,
    '120104001': 29,
    '120104002': 63,
    '120104004': 7,
    '120105001': 23,
}


@api.route('/stores/<int:store_id>/inventories/lookups', methods=['GET'])
def _get_frt_stores_inventories_lookups(store_id):
    return get_frt_stores_inventories_lookups(store_id)


@api.route('/stores/<int:store_id>/inventories/frt/lookups', methods=['GET'])
def get_frt_stores_inventories_lookups(store_id):
    type = request.args.get('type', 'store')

    return FrtInventory.get_lookups(store_id, type)


@api.route('/stores/<int:store_id>/inventories', methods=['GET'])
def _get_frt_stores_inventories(store_id):
    return get_frt_stores_inventories(store_id)


@api.route('/stores/<int:store_id>/inventories/frt', methods=['GET'])
def get_frt_stores_inventories(store_id):
    return FrtInventory.find_all_store_inventories(store_id, **request.args.to_dict())


@api.route('/stores/<int:store_id>/inventories/cartypes/stats')
def _get_frt_inventory_cartypes_stats(store_id):
    return get_frt_inventory_cartypes_stats(store_id)


@api.route('/stores/<int:store_id>/inventories/frt/cartypes/stats')
def get_frt_inventory_cartypes_stats(store_id):
    stockage = request.args.get('stockage', None)

    result = FrtInventory.get_cartypes_count(store_id, stockage)
    if current_app.config['FRT_DEMO']:
        for data in result:
            data['order_count'] = MOCK_ORDERS_COUNT.get(data['cartype_code'], 0)
            data['store_leads_count'] = MOCK_STORE_LEEDS_COUNT.get(data['cartype_code'], 0)
            data['group_leads_count'] = MOCK_GROUP_LEEDS_COUNT.get(data['cartype_code'], 0)
            data['net_leads_count'] = MOCK_NET_LEEDS_COUNT.get(data['cartype_code'], 0)
    return result


@api.route('/stores/<int:store_id>/inventories/subtypes/stats')
def _get_frt_inventory_subtypes_stats(store_id):
    return get_frt_inventory_subtypes_stats(store_id)


@api.route('/stores/<int:store_id>/inventories/frt/subtypes/stats')
def get_frt_inventory_subtypes_stats(store_id):
    cartype_code = request.args.get('cartype_code', None)

    return FrtInventory.get_subtypes_count(store_id, cartype_code)


@api.route('/stores/<int:store_id>/inventories/frt/stockages/stats')
def _get_frt_inventory_stockages_stats(store_id):
    return get_frt_inventory_stockages_stats(store_id)


@api.route('/stores/<int:store_id>/inventories/stockages/stats')
def get_frt_inventory_stockages_stats(store_id):
    return FrtInventory.get_stockages_count(store_id)


@api.route('/stores/<int:store_id>/inventories/frt/shared', methods=['GET'])
def _get_frt_shared_inventories(store_id):
    return get_frt_stores_inventories(store_id)


@api.route('/stores/<int:store_id>/inventories/shared', methods=['GET'])
def get_frt_shared_inventories(store_id):
    return FrtSharedInventory.find_all_shared_inventories(store_id, **request.args.to_dict())


@api.route('/stores/<int:store_id>/inventories/frt/shared/<subtype_code>', methods=['GET'])
def _get_frt_shared_inventories_details(store_id, subtype_code):
    return get_frt_shared_inventories_details(store_id, subtype_code)


@api.route('/stores/<int:store_id>/inventories/shared/<subtype_code>', methods=['GET'])
def get_frt_shared_inventories_details(store_id, subtype_code):
    return get_shared_inventories_details_by_subtype_code(store_id, subtype_code)
