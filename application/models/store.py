# coding: utf-8
from application.cache import LONG_CACHE, cache
from sqlalchemy import Column
from sqlalchemy.types import String

from .base import Model, BaseMixin, SequenceFieldMixIn, get_or_create

INVALID_STORE_ID = -1


class Store(BaseMixin, SequenceFieldMixIn, Model):
    '''
    店面信息`
    '''
    __tablename__ = 'store'
    name = Column(String(250), unique=True, index=True)

    @classmethod
    def from_json(cls, data):
        id = data['id']
        sequence_id = data.get('sequence_id')
        name = data['name']
        instance, _ = get_or_create(cls, id=id)
        if sequence_id:
            instance.sequence_id = sequence_id
        instance.name = name
        return instance

    @classmethod
    def find_all_by_stores_ids(cls, ids):
        return cls.query.filter(cls.id.in_(ids)).all()

    @classmethod
    def from_id_name(cls, id, name):
        instance, _ = get_or_create(cls, id=id)
        instance.name = name
        return instance

    @classmethod
    @cache.memoize(timeout=LONG_CACHE)
    def find_from_cache(cls, oid):
        return cls.find(oid)

    @classmethod
    def find_storename_by_store_id(cls, store_id):
        query = cls.query.filter(cls.id == store_id)
        return query.first()
