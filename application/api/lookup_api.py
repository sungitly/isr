# -*- coding: utf-8 -*-
from application.api import api
from application.cache import cache
from application.models.lookup import LookupValue, Lookup
from flask import request
from flask.ext.babel import gettext

from werkzeug.exceptions import abort


@api.route('/stores/<int:store_id>/lookups', methods=['GET'])
def get_lookups(store_id):
    # workaround the issue client side lose store id after ucenter related upgrade
    if store_id <= 0:
        abort(401)

    names = request.args.getlist('names[]', None)

    if names:
        lookups = Lookup.find_all_by_names_of_store(store_id, names)
    else:
        lookups = Lookup.find_all_by_store_wo_page(store_id)

    lookups_dict = {}
    for lookup in lookups:
        lookups_dict[lookup.name] = lookup

    return lookups_dict.values()


@api.route('/lookups/<int:uid>/values', methods=['GET'])
def get_lookupvalues_by_lookup_id(uid):
    return LookupValue.find_all_by_lookup_id(uid)


@api.route('/stores/<int:store_id>/lookups/<name>/values', methods=['GET'])
def get_lookupvalues_by_lookup_name(store_id, name):
    lookup = Lookup.find_by_name_and_store(store_id, name)

    if not lookup:
        abort(404, description=gettext(u'lookup with name %(name)s is not found', name=name))

    return LookupValue.find_all_by_lookup_id(lookup.id)


@api.route('/lookupvalues', methods=['GET'])
def get_lookup_values():
    parent_id = request.args.get('parent_id', None)

    if parent_id is None:
        abort(400, description=gettext('parent_id is empty'))

    return LookupValue.find_all_by_parent_id(parent_id)


@api.route('/stores/<int:store_id>/lookupvalues', methods=['GET'])
def get_lookup_values_by_store(store_id):
    ids = Lookup.get_all_store_ids(store_id)
    return LookupValue.find_all_by_lookup_ids([id.id for id in ids])


@api.route('/stores/<int:store_id>/lookups/refresh', methods=['POST'])
def refresh_lookup(store_id):
    data = request.json
    if data is None or not data.get('name'):
        abort(400, description=gettext('invalid json request'))

    cache.delete_memoized(LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache, LookupValue, long(store_id),
                          data.get('name'))
    return LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(store_id, data.get('name'))


@api.route('/lookup/descriptions', methods=['GET'])
def get_lookup_descriptions():
    store_id = request.args.get('store_id', None)

    if store_id is None:
        abort(400, description=gettext('store_id is empty'))

    id_and_description = Lookup.get_descriptions_by_store_id(store_id)

    lookups_dict = dict()

    for lookups in id_and_description:
        lookups_dict[lookups.id] = lookups.description

    return lookups_dict
