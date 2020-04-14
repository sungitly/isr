# -*- coding: utf-8 -*-
import json
import time

from application.cache import cache
from application.exceptions import FrtEncryptParamException, FrtFetchStoreInventoriesException, \
    FrtFetchSharedInventoriesException
from application.models.base import db
from application.models.frtinv import FrtInventory, FrtSharedInventory
from application.utils import convert_dict_key_lower_case
from config import Config
from flask import current_app
from pysimplesoap.client import SoapClient
from pysimplesoap.simplexml import SimpleXMLElement

WSA_NS = 'http://www.w3.org/2005/08/addressing'
NS_BINDING = 'http://tempuri.org/IContract/'

DEMO_BRANDS = ('1201', '1202')
DEMO_STATUS_CONV = {u'销售出库': u'在库'}
DEMO_SUBTYPE_MRSP_CONV = {
    u'1202010010002': u'498000.00',
    u'1201020030081': u'1018000.00',
    u'1201050010004': u'618000.00',
    u'1201050010003': u'558000.00',
    u'1202010010004': u'582800.00',
    u'1202010010003': u'552800.00',
    u'1201020030079': u'828000.00',
    u'1201040020025': u'666000.00',
    u'1201040040097': u'1098000.00',
    u'1201040010135': u'2648000.00',
    u'1201040010133': u'1558000.00',
    u'1201040040103': u'1048000.00',
    u'1201020030080': u'928000.00',
    u'1201040010130': u'1768000.00',
    u'1201040010126': u'2648000.00',
    u'1201040010128': u'1558000.00',
    u'1201040010113': u'1558000.00',
    u'1201040020023': u'628000.00',
    u'1201040040086': u'1098000.00',
    u'1201040040085': u'1048000.00',
    u'1201040040087': u'1138000.00',
    u'1201040010120': u'1768000.00',
    u'1201040020020': u'578000.00',
    u'1201030020076': u'608000.00',
    u'1201040020022': u'578000.00',
    u'1201040020021': u'628000.00'

}

soap_client = SoapClient(
    location=Config.FRT_WS_URL,
    cache=None,
    timeout=60,
    ns="brt",
    namespace="http://tempuri.org/",
    soap_ns="soap12env",
    trace=False,
    action='',
    http_headers={'Content-type': 'application/soap+xml; charset=utf-8'})
FrtEncryptParamException()


def generate_wsa_header_for_soap12(ns_binding, action):
    action_header = ns_binding + action

    soap_header = SimpleXMLElement('<Header></Header>')
    soap_header.add_child('To', Config.FRT_WS_URL, WSA_NS)
    soap_header.add_child('Action', action_header, WSA_NS)
    return soap_header


def encrypt_params(params):
    encrypt_result = soap_client.DataEncrypt(Text=json.dumps(params),
                                             sKey=Config.FRT_API_KEY,
                                             headers=generate_wsa_header_for_soap12(NS_BINDING, 'DataEncrypt'))

    if encrypt_result:
        try:
            encrypted_params = encrypt_result(tag='DataEncryptResult')
            return unicode(encrypted_params)
        except Exception:
            current_app.logger.exception('FRT ERRORS >>>>>>')

    raise FrtEncryptParamException()


def get_store_inventories(encrypted_params):
    inventories_result = soap_client.SelectCarInv(param=encrypted_params,
                                                  headers=generate_wsa_header_for_soap12(NS_BINDING, 'SelectCarInv'))

    if inventories_result:
        try:
            inventories = json.loads(unicode(inventories_result(tag='SelectCarInvResult')))
            return inventories['tb']
        except Exception:
            current_app.logger.exception('FRT ERRORS >>>>>>')

    raise FrtFetchStoreInventoriesException()


def get_shared_inventories(encrypted_params):
    inventories_result = soap_client.SelectCarShareInv(param=encrypted_params,
                                                       headers=generate_wsa_header_for_soap12(NS_BINDING,
                                                                                              'SelectCarShareInv'))

    if inventories_result:
        try:
            inventories = json.loads(unicode(inventories_result(tag='SelectCarShareInvResult')))
            return inventories['tb']
        except Exception:
            current_app.logger.exception('FRT ERRORS >>>>>>')

    raise FrtFetchSharedInventoriesException()


def get_shared_inventories_details_by_subtype_code(store_id, sub_type_code):
    # TODO the result could be cached for like one hour ...
    params = [{"carSubTypeNo": sub_type_code}]
    encrypted_params = encrypt_params(params)

    inventories_result = soap_client.SelectCarShareInvDet(param=encrypted_params,
                                                          headers=generate_wsa_header_for_soap12(NS_BINDING,
                                                                                                 'SelectCarShareInvDet'))

    if inventories_result:
        try:
            inventories = json.loads(unicode(inventories_result(tag='SelectCarShareInvDetResult')))
            data = inventories['tb']
            # convert to lower case
            result = []
            for item in data:
                result.append(convert_dict_key_lower_case(item))
            return result
        except Exception:
            current_app.logger.exception('FRT ERRORS >>>>>>')

    raise FrtFetchSharedInventoriesException()


def sync_latest_store_inventory(store_id):
    # TODO transfer store_id to frt store_no

    # load store inventories
    params = [{"store_no": map_store(store_id), "carTypeNo": ""}]
    encrypted_params = encrypt_params(params)
    inventories = get_store_inventories(encrypted_params)

    timestamp = int(time.time())

    inventories = filter(lambda inv: is_valid_inventory(inv), inventories)

    for inventory in inventories:
        frt_inv = FrtInventory.from_data(inventory)

        if current_app.config['FRT_DEMO']:
            if frt_inv.invday > 180:
                frt_inv.invday /= 5
            if DEMO_STATUS_CONV.get(frt_inv.inv_status, None):
                frt_inv.inv_status = DEMO_STATUS_CONV[frt_inv.inv_status]
            if DEMO_SUBTYPE_MRSP_CONV.get(frt_inv.subtype_code, None):
                frt_inv.mrsp = DEMO_SUBTYPE_MRSP_CONV[frt_inv.subtype_code]

        frt_inv.store_id = store_id
        frt_inv.sync_timestamp = timestamp

        frt_inv.save()

    db.session.commit()

    cache.delete_memoized(FrtInventory.get_store_lookups_from_cache, FrtInventory, int(store_id))

    # load group shared inventory
    brand_codes = FrtInventory.find_all_brand_code(store_id, None)
    if brand_codes:
        brand_codes = [c for c, in brand_codes]

    timestamp = time.time()

    shared_inventories_total = []

    if current_app.config['FRT_DEMO']:
        brand_codes = DEMO_BRANDS

    for brand in brand_codes:
        shared_inv_params = [{"brand_code": brand}]
        shared_inv_encrypted_params = encrypt_params(shared_inv_params)
        shared_inventories = get_shared_inventories(shared_inv_encrypted_params)

        for shared_inventory in shared_inventories:
            frt_shared_inv = FrtSharedInventory.from_data(shared_inventory)
            frt_shared_inv.store_id = store_id
            frt_shared_inv.sync_timestamp = timestamp

            frt_shared_inv.save()
            shared_inventories_total.append(frt_shared_inv)

    db.session.commit()

    cache.delete_memoized(FrtSharedInventory.get_group_lookups_from_cache, FrtInventory, int(store_id))

    return timestamp, inventories, shared_inventories_total


def map_store(isr_store_id):
    return '2004001'


def is_valid_inventory(inv):
    if not inv.get('SUBTYPE_CODE', None):
        return False
    elif inv.get('OUT_FACTORY_DATE', None) and '0001-01-01' in inv['OUT_FACTORY_DATE']:
        return False
    elif current_app.config['FRT_DEMO'] and inv.get('BRAND_CODE', None) not in DEMO_BRANDS:
        return False
    else:
        return True
