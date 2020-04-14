# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, BigInteger, and_, or_, asc, func
from sqlalchemy import String
from sqlalchemy.orm import load_only

from application.cache import cache, LONG_CACHE
from application.models.base import BaseMixin
from .base import db, StoreMixin


class Lookup(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'lookup'

    name = Column(String(100), nullable=False, index=True)
    type = Column(String(100), default='base', nullable=False)
    description = Column(String(100), nullable=True)
    version = Column(Integer, default=1, nullable=False)

    types = ('base', 'brand', 'car', 'account')

    @classmethod
    def find_all_by_store_wo_page(cls, store_id):
        return cls.query.filter(or_(cls.store_id == store_id, cls.store_id == -1)).order_by(asc(cls.store_id)).all()

    @staticmethod
    def find_id_name_version_by_store(sess, store_id):
        return sess.query(Lookup.id, Lookup.name, Lookup.version).filter(Lookup.store_id == store_id).all()

    @classmethod
    def find_all_by_names_of_store(cls, store_id, names):
        return cls.query.filter(and_(cls.name.in_(names), or_(cls.store_id == store_id, cls.store_id == -1))).order_by(
            asc(cls.store_id)).all()

    @classmethod
    def find_by_name_and_store(cls, store_id, name):
        lookups = cls.query.filter(and_(cls.name == name, or_(cls.store_id == store_id, cls.store_id == -1))).order_by(
            asc(cls.store_id)).all()

        if not lookups or len(lookups) == 0:
            return

        lookups_dict = {}
        for lookup in lookups:
            lookups_dict[lookup.name] = lookup

        return lookups_dict.get(name, None)

    @staticmethod
    def exist_by_name_and_store(sess, store_id, name):
        return sess.query(func.count(Lookup.id)).filter(and_(Lookup.name == name, Lookup.store_id == store_id)).scalar()

    @classmethod
    def get_all_store_ids(cls, store_id):
        return cls.query.options(load_only(cls.id)).filter(cls.store_id == store_id).order_by(
            asc(cls.id)).all()

    @classmethod
    def get_descriptions_by_store_id(cls, store_id):
        return cls.query.options(load_only(cls.id, cls.description)).filter(cls.store_id == store_id).order_by(
            asc(cls.id)).all()

    @classmethod
    def get_description_by_store_id(cls, lookup_id):
        return cls.query.options(load_only(cls.description)).filter(cls.id == lookup_id).first()

    @staticmethod
    def find_name_type_description_by_store(sess, store_id):
        return sess.query(Lookup.name, Lookup.type, Lookup.description).filter(Lookup.store_id == store_id).all()

    @classmethod
    def ensure_store_id_not_in_lookup(cls, store_id, name):
        return cls.query.filter(and_(cls.store_id == store_id, cls.name == name)).first()

    @classmethod
    def create(cls, store_id, name, type, description, version):
        instance = cls()
        if instance.ensure_store_id_not_in_lookup(store_id, name) is None:
            instance.store_id = store_id
            instance.name = name
            instance.type = type
            instance.description = description
            instance.version = version
            return instance

    @classmethod
    def update_version(cls, lookup_id, version):
        query = cls.query.filter(and_(cls.id == lookup_id, cls.version == version))
        query.update({cls.version: int(version) + 1})


class LookupValue(db.Model):
    __tablename__ = 'lookupvalue'

    id = Column(BigInteger, primary_key=True)
    code = Column(String(100), nullable=False)
    vendor_code = Column(String(100))
    vendor_value = Column(String(200))
    vendor_section = Column(String(200))
    value = Column(String(200))
    lookup_id = Column(BigInteger, nullable=False, index=True)
    parent_id = Column(BigInteger, default=-1, nullable=False, index=True)
    order = Column(Integer, default=0)

    image_url = Column(String(500))
    section = Column(String(50))

    org_code = Column(String(100))
    user_code = Column(String(100))
    password = Column(String(100))
    v_version = Column(String(100))

    version = Column(Integer, default=1, nullable=False)

    type_base_columns = (
        'id', 'code', 'vendor_code', 'value', 'lookup_id', 'parent_id', 'order', 'version', 'section', 'image_url',
        'vendor_code', 'vendor_value', 'vendor_section')
    type_car_columns = type_base_columns
    type_brand_columns = type_base_columns
    type_account_columns = type_base_columns + ('org_code', 'user_code', 'password', 'v_version')

    types_columns = {'base': type_base_columns, 'brand': type_brand_columns, 'car': type_car_columns,
                     'account': type_account_columns}

    @classmethod
    def find(cls, oid):
        return cls.query.filter(cls.id == oid).first()

    @classmethod
    def find_all_by_lookup_id(cls, lookup_id):
        lookup = Lookup.find(lookup_id)

        return cls.query.options(load_only(*cls.get_load_columns_by_type(lookup.type))).filter(
            cls.lookup_id == lookup_id).all()

    @classmethod
    def find_all_by_lookup_id_by_order(cls, lookup_id):
        lookup = Lookup.find(lookup_id)

        query = cls.query.filter(and_(cls.lookup_id == lookup_id, cls.version == lookup.version))

        return query.order_by(asc(cls.order)).all()

    @classmethod
    def find_all_by_parent_id(cls, parent_id):
        lookup_value = LookupValue.find(parent_id)
        lookup = Lookup.find(lookup_value.lookup_id)
        return cls.query.options(load_only(*cls.get_load_columns_by_type(lookup.type))).filter(
            cls.parent_id == parent_id).all()

    @classmethod
    def get_load_columns_by_type(cls, type):
        return cls.types_columns.get(type, cls.type_base_columns)

    @classmethod
    def find_all_by_lookup_ids(cls, lookup_ids):
        return cls.query.filter(cls.lookup_id.in_(lookup_ids)).all()

    @classmethod
    def find_all_by_lookup_name_of_store(cls, store_id, lookup_name):
        lookup = Lookup.find_by_name_and_store(store_id, lookup_name)

        if lookup:
            return LookupValue.find_all_by_lookup_id(lookup.id)
        else:
            return dict()

    @classmethod
    def get_vendor_code_by_code(cls, code, store_id, lookup_name):
        if code:
            lookups = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), lookup_name)

            lookup = lookups.get(code)

            if lookup:
                return lookup.vendor_code

        return ''

    @classmethod
    @cache.memoize(timeout=LONG_CACHE)
    def find_all_in_dict_by_lookup_name_of_store_from_cache(cls, store_id, lookup_name):
        values = LookupValue.find_all_by_lookup_name_of_store(store_id, lookup_name)
        return {value.code: value for value in values}

    @staticmethod
    def find_code_value_order_by_lookup_id_by_order(sess, lookup_id):

        query = sess.query(Lookup.name, LookupValue.code, LookupValue.value, LookupValue.order).filter(
            and_(LookupValue.lookup_id == lookup_id, Lookup.id == lookup_id,
                 LookupValue.version == Lookup.version)).order_by(
            asc(LookupValue.order))

        return query.all()

    @classmethod
    def find_value_in_lookupvalue_by_lookup_id_by_order_by_value(cls, lookup_id, value):
        lookup = Lookup.find(lookup_id)

        query = cls.query.filter(
            and_(cls.value == value, cls.lookup_id == lookup_id, cls.version == lookup.version)).order_by(
            asc(cls.order))

        return query.first()

    @classmethod
    def ensure_lookup_id_not_in_lookupvalue(cls, lookup_id, code):
        return cls.query.filter(and_(cls.lookup_id == lookup_id, cls.code == code)).first()

    @classmethod
    def create(cls, code, value, lookup_id, parent_id, order, section, version):
        instance = cls()
        if instance.ensure_lookup_id_not_in_lookupvalue(lookup_id, code) is None:
            instance.code = code
            instance.value = value
            instance.lookup_id = lookup_id
            instance.parent_id = parent_id
            instance.order = order
            instance.section = section
            instance.version = version
            return instance

    @classmethod
    def update_version(cls, lookup_id, version, exclude_lookupvalue_id=None):
        query = cls.query.filter(and_(cls.lookup_id == lookup_id, cls.version == version))
        if exclude_lookupvalue_id:
            query = query.filter(cls.id != exclude_lookupvalue_id)
        query.update({cls.version: int(version) + 1})
