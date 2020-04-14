# -*- coding: utf-8 -*-
from sqlalchemy import Column, String, BigInteger, Boolean, and_, Text, asc
from sqlalchemy import Integer

from application.cache import cache, LONG_CACHE
from application.models.base import db, BaseMixin, StoreMixin


class TaSetting(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'tasetting'

    type = Column(String(50))
    year = Column(Integer)
    month = Column(Integer)
    week = Column(Integer)
    sales_id = Column(BigInteger)
    value = Column(Integer)
    is_deleted = Column(Boolean, default=0)

    valid_type = ('monthly', 'weekly', 'monthly_by_sales')

    @classmethod
    def find_all_active_monthly_ta(cls, year, month, store_id):
        return cls.query.filter(
            and_(cls.year == year, cls.month == month, cls.is_deleted == 0, cls.store_id == store_id)).all()

    @classmethod
    def find_active_monthly_ta(cls, year, month, store_id):
        return cls.query.filter(
            and_(cls.year == year, cls.month == month, cls.is_deleted == 0, cls.store_id == store_id)).order_by(
            cls.created_on.desc()).first()

    @classmethod
    def find_all_active_weekly_ta(cls, year, week, store_id):
        return cls.query.filter(
            and_(cls.year == year, cls.week == week, cls.is_deleted == 0, cls.store_id == store_id)).all()

    @classmethod
    def find_active_weekly_ta(cls, year, week, store_id):
        return cls.query.filter(
            and_(cls.year == year, cls.week == week, cls.is_deleted == 0, cls.store_id == store_id)).order_by(
            cls.created_on.desc()).first()

    @classmethod
    def find_all_active_by_type_and_store(cls, type, store_id):
        return cls.query.filter(and_(cls.type == type, cls.is_deleted == 0, cls.store_id == store_id)).order_by(
            cls.year.desc(), cls.month.desc(),
            cls.week.desc()).all()


class StoreSetting(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'store_setting'

    type = Column(String(50))
    value = Column(Text)

    TYPE_INV_PROVIDER = 'inventory_provider'
    TYPE_INSURANCE = 'insurance'
    TYPE_RADAR = 'radar'
    INV_PROVIDERS = ('uinv', 'frt')

    @classmethod
    def find_all_by_store_wo_page(cls, store_id):
        return cls.query.filter(cls.store_id == store_id).order_by(asc(cls.type)).all()

    @classmethod
    def find_all_by_store_and_type(cls, store_id, type):
        return cls.query.filter(and_(cls.store_id == store_id, cls.type == type)).all()

    @classmethod
    @cache.memoize(timeout=LONG_CACHE)
    def is_radar_avail(cls, store_id):
        setting = cls.query.filter(and_(cls.store_id == store_id, cls.type == 'radar')).first()

        if setting and 'Y' == setting.value:
            return True
        else:
            return False
