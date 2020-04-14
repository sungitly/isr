# -*- coding: utf-8 -*-
import os

from pymercury.alembicutils import reflect_model, bulk_insert_data, absolute_path, session_scope
from pymercury.csvparser import parse_csv_with_header
from sqlalchemy import func, and_


def reload_table_from_csv(tablename, csv_file, filters=None, absolute_path=False):
    # delete existing records
    delete_sql = 'DELETE FROM %s' % tablename

    if filters:
        delete_sql = delete_sql + ' WHERE ' + convert_dict_to_where_clause(filters)

    from alembic import op
    op.execute(delete_sql)

    # load the csv
    load_table_from_csv(tablename, csv_file, filters, absolute_path)


def convert_dict_to_where_clause(where_dict):
    return ' and '.join(["%s='%s'" % (k, v) for k, v in where_dict.iteritems()])


def load_table_from_csv(tablename, csv_file, filters=None, absolute_path=False):
    bulk_insert_data(tablename,
                     parse_csv_with_header(get_path(csv_file, absolute_path), filters=filters))


def exist_lookup_by_name_and_store(store_id, name):
    with session_scope() as session:
        Lookup = reflect_model('lookup')
        return session.query(func.count(Lookup.id)).filter(
            and_(Lookup.name == name, Lookup.store_id == store_id)).scalar() > 0


def find_lookup_basic_info_by_store(store_id):
    with session_scope() as session:
        Lookup = reflect_model('lookup')
        return session.query(Lookup.id, Lookup.name, Lookup.version).filter(Lookup.store_id == store_id).all()


def find_lookup_basic_info_by_id(id):
    with session_scope() as session:
        Lookup = reflect_model('lookup')
        return session.query(Lookup.id, Lookup.name, Lookup.version).filter(Lookup.id == id).first()


def update_lookup_version(id, new_version):
    with session_scope() as session:
        Lookup = reflect_model('lookup')
        return session.query(Lookup.id, Lookup.version).filter(Lookup.id == id).update({'version': new_version})


def load_lookup_from_csv(csv_file, store_id_override=None, filters=None, absolute_path=False):
    data = parse_csv_with_header(get_path(csv_file, absolute_path), filters=filters)

    # 1. check if lookup already exist
    # 2. update store_id if store_id_override is provided
    for item in data:
        store_id = store_id_override if store_id_override else item.get('store_id', -1)
        exist = exist_lookup_by_name_and_store(store_id, item['name'])
        if exist:
            raise Exception(
                'Lookup with name %s already exist. Please specify the lookup name which has\'t been populated.')
        item['store_id'] = store_id

    if len(data) > 0:
        bulk_insert_data('lookup', data)


def load_lookupvalue_from_csv(csv_file, lookup_id, version, absolute_path=False):
    data = parse_csv_with_header(get_path(csv_file, absolute_path))

    for item in data:
        item['lookup_id'] = lookup_id
        item['version'] = version

    if len(data) > 0:
        bulk_insert_data('lookupvalue', data)


def load_all_lookupvalue_from_csv(csv_file_folder, store_id, absolute_path=False):
    csv_file_folder = get_path(csv_file_folder, absolute_path)
    lookups = find_lookup_basic_info_by_store(store_id)
    for lookup in lookups:
        csv_file = os.path.join(csv_file_folder, '%s.csv' % lookup.name)
        if os.path.isfile(csv_file):
            load_lookupvalue_from_csv(csv_file, lookup.id, lookup.version, absolute_path=absolute_path)


def get_path(path, absolute):
    if absolute:
        return path
    else:
        return absolute_path(path)
