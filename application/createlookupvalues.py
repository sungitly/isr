#!/usr/bin/env python
# -*- coding: utf-8 -*-
from application.models.lookup import Lookup, LookupValue


class NotEmptyChecker:
    def __init__(self, value):
        if not value:
            pass

    def map(self, value):
        return NotEmptyChecker(value)


def _descriptions(store_id=2):
    from application.models.base import db
    search_result = Lookup.find_name_type_description_by_store(db.session, store_id)
    if len(search_result) == 0: return False
    return search_result


def _age_groups(lookup_id):
    from application.models.base import db
    search_result = LookupValue.find_code_value_order_by_lookup_id_by_order(db.session, lookup_id)
    if len(search_result) == 0: return False
    return search_result


def generate_lookup(store_id):
    from application.models.base import db

    ''' insert store info on lookup'''

    lookups_title = _descriptions()
    version = 1

    try:
        for name, type, description in lookups_title:
            lookup = Lookup.create(store_id=store_id, name=name,
                                   type=type, description=description, version=version)
            if lookup is not None:
                lookup.save()
        db.session.commit()
    except Exception as e:
        raise e

    result = Lookup.get_all_store_ids(store_id)

    lookup_ids = dict()
    for lookups in result:
        lookup_ids[str(lookups.name).strip()] = lookups.id

    return lookup_ids


def generate_lookupvalue(lookup_ids, lookupvalues_data):
    '''
    1: copy age-group appt-type last-instore on lookupvalue
    2: insert intent-car test-drive-car intent-color intent-level channel on lookupvalue
    '''
    from application.models.base import db

    lookupvalue_age_groups = _age_groups(lookup_id=11)
    lookupvalue_appt_type = _age_groups(lookup_id=17)
    lookupvalue_last_instore = _age_groups(lookup_id=18)

    try:
        for copy_lookupvalue in [lookupvalue_age_groups, lookupvalue_appt_type, lookupvalue_last_instore]:
            for lookup_name, code, value, order in copy_lookupvalue:
                lookupvalue = LookupValue.create(
                    code=code,
                    value=value,
                    lookup_id=lookup_ids[lookup_name],
                    parent_id='-1',
                    order=order,
                    section=None,
                    version='1'
                )
                if lookupvalue is not None:
                    db.session.add(lookupvalue)
            db.session.commit()
    except Exception as e:
        raise e

    try:
        for lookup_name_key in lookupvalues_data:
            order_count = 10
            for code, value, section in lookupvalues_data[lookup_name_key]:
                lookupvalue = LookupValue.create(
                    code=code,
                    value=value,
                    lookup_id=lookup_ids[lookup_name_key],
                    parent_id='-1',
                    order=order_count,
                    section=section,
                    version='1'
                )
                if lookupvalue is not None:
                    db.session.add(lookupvalue)
                order_count += 10
            db.session.commit()
    except Exception as e:
        raise e

    return True


def check_looupvalue(lookup_id, changevalues):
    from application.nutils.excel import safe_convert_unicode
    lookup_by_store_and_name = Lookup.get_description_by_store_id(lookup_id)
    description = lookup_by_store_and_name.description
    sections = LookupValue.find_all_by_lookup_id_by_order(lookup_id)[0]

    for changevalue in changevalues:
        value = changevalue['value']
        if not value and not changevalue['orders'] and not changevalue['section']:
            continue
        if not value:
            return u"此行%s必须有值" % description
        else:
            value = safe_convert_unicode(value)
            if LookupValue.find_value_in_lookupvalue_by_lookup_id_by_order_by_value(lookup_id, value):
                return u"%s已经存在" % value
        if not isinstance(changevalue['orders'], int):
            return u"次序必须是数值"
        if sections.section:
            if not changevalue['section']:
                return u"类别必须有值"
        else:
            if changevalue['section']:
                return u"类别必须为空"


def add_lookupvalue(lookup_id, version, changevalues):
    from application.models.base import db
    from application.nutils.excel import convert_value_to_code, safe_convert_unicode

    count = 0

    try:
        for changevalue in changevalues:
            if not changevalue['value'] and not changevalue['orders']:
                continue
            lookupvalue = LookupValue.create(
                code=convert_value_to_code(safe_convert_unicode(changevalue['value'])),
                value=safe_convert_unicode(changevalue['value']),
                lookup_id=lookup_id,
                parent_id='-1',
                order=safe_convert_unicode(changevalue['orders']),
                section=safe_convert_unicode(changevalue['section']),
                version=version,
            )
            db.session.add(lookupvalue)
            count += 1
        db.session.commit()
    except Exception as e:
        raise e

    if count == 0: return count

    try:
        Lookup.update_version(lookup_id, version)
        LookupValue.update_version(lookup_id, version)
        db.session.commit()
    except Exception as e:
        raise e

    return count
