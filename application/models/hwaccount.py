# -*- coding: utf-8 -*-
from sqlalchemy import Column, BigInteger, String, Boolean, and_

from application.cache import cache, LONG_CACHE
from application.models.base import db


class HwjdAccount(db.Model):
    __tablename__ = 'hwjd_account'

    id = Column(BigInteger, primary_key=True)
    store_id = Column(BigInteger, unique=True)
    name = Column(String(200))
    org_code = Column(String(50))
    user_code = Column(String(50))
    password = Column(String(50))
    make = Column(String(100))
    models = Column(String(1000))
    active = Column(Boolean, default=True)

    @classmethod
    def find_by_store_id(cls, store_id):
        return cls.query.filter(and_(cls.store_id == store_id, cls.active == 1)).first()

    @classmethod
    @cache.memoize(timeout=LONG_CACHE)
    def find_active_hwjd_store_ids(cls):
        store_ids = db.session.query(cls.id).filter(cls.active == 1).all()
        if store_ids:
            return [item[0] for item in store_ids]
        else:
            return []

    @classmethod
    def find_all_stores(cls):
        return cls.query.all()

    def models_array(self):
        if self.models:
            return self.models.split('|')
        else:
            return []

