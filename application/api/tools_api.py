# -*- coding: utf-8 -*-
from flask import request

from application.api import api
from application.cache import cache
from application.integration.vinlookup import VinLookupService
from application.utils import parse_comma_seperated_args


@api.route('/vin/<vin>', methods=['GET'])
def get_vin(vin):
    return VinLookupService.get_by_vin(vin)


@api.route('/hwjd/lookups/<type>', methods=['GET'])
def refresh_hwjd_lookup(type):
    from application.models.hwlookup import HwjdLookup
    return HwjdLookup.refresh(type)


@api.route('/hwjd/lookups/intent-car/match')
def match_hwjd_intent_car():
    store_ids = parse_comma_seperated_args(request.args.get('store_id', None))

    from application.models.hwlookup import HwjdLookup
    HwjdLookup.match_intent_car_lookups(store_ids)


@api.route('/hwjd/lookups/age-group/match')
def match_hwjd_age_group():
    store_ids = parse_comma_seperated_args(request.args.get('store_id', None))

    from application.models.hwlookup import HwjdLookup
    HwjdLookup.match_age_group_lookups(store_ids)


@api.route('/hwjd/lookups/intent-level/match')
def match_hwjd_intent_level():
    store_ids = parse_comma_seperated_args(request.args.get('store_id', None))

    from application.models.hwlookup import HwjdLookup
    HwjdLookup.match_intent_level_lookups(store_ids)


@api.route('/hwjd/accounts/refresh')
def refresh_hwjd_accounts():
    from application.models.hwaccount import HwjdAccount
    cache.delete_memoized(HwjdAccount.find_active_hwjd_store_ids)
    return HwjdAccount.find_active_hwjd_store_ids()
