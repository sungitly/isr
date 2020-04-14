# -*- coding: utf-8 -*-
from collections import OrderedDict

from application.cache import cache
from application.exceptions import InvalidFrtInventoryLookupTypeException
from application.models.base import db, BaseMixin, StoreMixin
from application.models.user import USER_ROLE_STORE_SALES
from application.nutils.numbers import is_float
from application.pagination import DEFAULT_PAGE_START, DEFAULT_PAGE_SIZE, get_page_info_from_dict
from flask import g
from sqlalchemy import Column, String, Date, Integer, Numeric, distinct, or_, and_, func


class DataCopyMixin(object):
    @classmethod
    def from_data(cls, data):
        instance = cls()
        for key, value in data.iteritems():
            key_fix = key.lower()
            if hasattr(instance, key_fix):
                setattr(instance, key_fix, value)
        return instance


class CarTypeBuilderMixin(object):
    @classmethod
    def build_car_code_info(cls, store_id, latest_sync_timestamp):
        query = db.session.query(cls.cartype_code, cls.cartype, cls.subtype_code, cls.subtype_name).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == latest_sync_timestamp))

        if hasattr(cls, 'inv_status'):
            if hasattr(g, 'user') and g.user and g.user.is_role_in_store_id(store_id, 'manager'):
                status_filters = cls.valid_status
            else:
                status_filters = cls.default_display_status
            query = query.filter(cls.inv_status.in_(status_filters))

        car_codes = query.group_by(cls.subtype_code).order_by(cls.cartype_code.asc(), cls.subtype_code.asc()).all()

        car_types_dict = dict()
        result = []
        for car_code in car_codes:
            car_type = car_types_dict.get(car_code[0])
            if not car_type:
                car_type = OrderedDict((('code', car_code[0]), ('name', car_code[1]), ('subtypes', list())))
                car_types_dict[car_code[0]] = car_type
                result.append(car_type)
            if car_code[2]:
                car_type['subtypes'].append(OrderedDict((('code', car_code[2]), ('name', car_code[3]))))

        return result


class FrtInventory(db.Model, BaseMixin, StoreMixin, DataCopyMixin, CarTypeBuilderMixin):
    __tablename__ = 'frt_inventory'

    brand_code = Column(String(100))
    brand_name = Column(String(200))
    class_code = Column(String(100))
    class_name = Column(String(200))
    cartype_code = Column(String(100))
    cartype = Column(String(200))
    subtype_code = Column(String(100))
    subtype_name = Column(String(200))
    color_name = Column(String(50))
    color_attribute = Column(String(50))
    warehouse_name = Column(String(200))
    location_name = Column(String(200))
    out_factory_date = Column(Date)
    vin = Column(String(50))
    inv_status = Column(String(50))
    _invday = Column('invday', Integer)
    stockage_cat = Column(String(50))
    in_price = Column(Numeric(precision=12, scale=2))
    mrsp = Column(Numeric(precision=12, scale=2))
    rebate_amt = Column(Numeric(precision=12, scale=2))
    sync_timestamp = Column(Integer)

    shared = Column(String(50))

    valid_lookup_type = ('store', 'group')
    valid_status = (u'在库', u'待入库', u'调拨在途', u'采购退货', u'采购退库申请', u'已调拨', u'采购在途', u'调拨申请', u'销售出库')
    default_display_status = (u'在库', u'待入库', u'调拨在途', u'采购在途')
    stockage_cat_lookups = {'1': u'30天内', '2': u'30天到60天', '3': u'60天到90天', '4': u'90天到120天', '5': u'120天到180天',
                            '6': u'180天以上'}

    @property
    def wavehouse_name(self):
        return self.warehouse_name

    @wavehouse_name.setter
    def wavehouse_name(self, name):
        self.warehouse_name = name

    @property
    def invday(self):
        return self._invday

    @invday.setter
    def invday(self, invday):
        self._invday = invday
        self.stockage_cat = FrtInventory.get_cat_by_stockage(invday)

    @classmethod
    def find_latest_sync_timestamp(cls, store_id):
        return db.session.query(db.func.max(cls.sync_timestamp)).filter(cls.store_id == store_id).scalar()

    @classmethod
    def find_all_by_sync_timestamp(cls, store_id, sync_timestamp):
        return cls.query.filter(and_(cls.store_id == store_id, cls.sync_timestamp == sync_timestamp)).all()

    @classmethod
    def find_all_store_inventories(cls, store_id, **kwargs):
        latest_sync_timestamp = cls.find_latest_sync_timestamp(store_id)

        query = cls.query.filter(cls.store_id == store_id).filter(cls.sync_timestamp == latest_sync_timestamp)

        if kwargs.get('cartype_code'):
            query = query.filter(cls.cartype_code == kwargs.get('cartype_code'))

        if kwargs.get('subtype_code'):
            query = query.filter(cls.subtype_code == kwargs.get('subtype_code'))

        if kwargs.get('color_name'):
            query = query.filter(cls.color_name == kwargs.get('color_name'))

        if kwargs.get('color_attribute'):
            query = query.filter(cls.color_attribute == kwargs.get('color_attribute'))

        # status filter
        if hasattr(g, 'user') and g.user and g.user.is_role_in_store_id(store_id, USER_ROLE_STORE_SALES):
            status_filters = cls.default_display_status
        else:
            status_filters = cls.valid_status

        query = query.filter(cls.inv_status.in_(status_filters))

        if kwargs.get('keywords'):
            raw_keywords = kwargs.get('keywords')
            keywords = '%' + raw_keywords + '%'

            if is_float(raw_keywords):
                price = float(raw_keywords)

                if price < 1000:
                    price *= 10000

                min_price = price - 1000
                max_price = price + 1000

                query = query.filter(and_(cls.mrsp >= min_price, cls.mrsp <= max_price))
            else:
                query = query.filter(
                    or_(cls.brand_name.like(keywords), cls.class_name.like(keywords), cls.cartype.like(keywords),
                        cls.subtype_name.like(keywords), cls.color_name.like(keywords),
                        cls.color_attribute.like(keywords), cls.vin.like(keywords)))

        page_info = get_page_info_from_dict(kwargs)

        return query.paginate(page_info['page'], page_info['per_page'])

    @classmethod
    def find_all_brand_code(cls, store_id, sync_timestamp):
        if not sync_timestamp:
            sync_timestamp = cls.find_latest_sync_timestamp(store_id)
        return db.session.query(distinct(cls.brand_code)).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == sync_timestamp)).all()

    @classmethod
    def build_color_code_info(cls, store_id, latest_sync_timestamp):
        colors = db.session.query(distinct(cls.color_name)).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == latest_sync_timestamp)).order_by(cls.color_name).all()

        return [{'code': color[0], 'name': color[0]} for color in colors if color[0]]

    @classmethod
    def build_color_attribute_info(cls, store_id, latest_sync_timestamp):
        colors = db.session.query(distinct(cls.color_attribute)).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == latest_sync_timestamp)).order_by(
            cls.color_attribute).all()

        return [{'code': color[0], 'name': color[0]} for color in colors if color[0]]

    @classmethod
    def get_lookups(cls, store_id, type):
        if type not in cls.valid_lookup_type:
            raise InvalidFrtInventoryLookupTypeException()
        store_id = int(store_id)
        if 'store' == type:
            return cls.get_store_lookups_from_cache(store_id)
        elif 'group' == type:
            return FrtSharedInventory.get_group_lookups_from_cache(store_id)

    @classmethod
    @cache.memoize()
    def get_store_lookups_from_cache(cls, store_id):
        latest_sync_timestamp = cls.find_latest_sync_timestamp(store_id)

        return {
            'cartypes': cls.build_car_code_info(store_id, latest_sync_timestamp),
            'colors': cls.build_color_code_info(store_id, latest_sync_timestamp),
            'color_attributes': cls.build_color_attribute_info(store_id, latest_sync_timestamp)
        }

    @classmethod
    def get_cartypes_count(cls, store_id, stockage=None):
        latest_sync_timestamp = cls.find_latest_sync_timestamp(store_id)

        query = db.session.query(cls.cartype_code, cls.cartype, func.count(cls.id)).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == latest_sync_timestamp))

        if stockage:
            query = query.filter(cls.stockage_cat == stockage)
        result = query.group_by(cls.cartype_code).all()
        if result:
            result = [dict(zip(('cartype_code', 'cartype', 'count'), data)) for data in result]
        return result

    @classmethod
    def get_subtypes_count(cls, store_id, cartype_code=None):
        latest_sync_timestamp = cls.find_latest_sync_timestamp(store_id)
        query = db.session.query(cls.subtype_code, cls.subtype_name, func.count(cls.id)).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == latest_sync_timestamp))

        if cartype_code:
            query = query.filter(cls.cartype_code == cartype_code)
        result = query.group_by(cls.subtype_code).all()
        if result:
            result = [dict(zip(('subtype_code', 'subtype_name', 'count'), data)) for data in result]
        return result

    @classmethod
    def get_stockages_count(cls, store_id):
        latest_sync_timestamp = cls.find_latest_sync_timestamp(store_id)
        result = db.session.query(cls.stockage_cat, func.count(cls.id)).filter(
            and_(cls.store_id == store_id, cls.sync_timestamp == latest_sync_timestamp)).group_by(
            cls.stockage_cat).all()
        if result:
            result = map(lambda d: (d[0], cls.stockage_cat_lookups.get(d[0], ''), d[1]), result)
            result = [dict(zip(('stockage_code', 'stockage_name', 'count'), data)) for data in result]
        return result

    @staticmethod
    def get_cat_by_stockage(invday):
        """
        Hardcode the stockage cat calculation for now. Divide invday by 2 because demo data problem
        """
        if not invday:
            invday = 0
        else:
            try:
                invday = int(invday)
            except Exception:
                invday = 0

        if invday <= 30:
            return '1'
        elif 30 < invday <= 60:
            return '2'
        elif 60 < invday <= 90:
            return '3'
        elif 90 < invday <= 120:
            return '4'
        elif 120 < invday <= 180:
            return '5'
        else:
            return '6'


class FrtSharedInventory(db.Model, BaseMixin, StoreMixin, DataCopyMixin, CarTypeBuilderMixin):
    __tablename__ = 'frt_shared_inventory'

    brand_code = Column(String(100))
    brand_name = Column(String(200))
    class_code = Column(String(100))
    class_name = Column(String(200))
    cartype_code = Column(String(100))
    cartype = Column(String(200))
    subtype_code = Column(String(100))
    subtype_name = Column(String(200))
    qty = Column(Integer)
    sync_timestamp = Column(Integer)

    @classmethod
    @cache.memoize()
    def get_group_lookups_from_cache(cls, store_id):
        latest_sync_timestamp = db.session.query(db.func.max(cls.sync_timestamp)).filter(
            cls.store_id == store_id).scalar()
        return {
            'cartypes': cls.build_car_code_info(store_id, latest_sync_timestamp)
        }

    @classmethod
    def find_all_shared_inventories(cls, store_id, **kwargs):
        latest_sync_timestamp = db.session.query(db.func.max(cls.sync_timestamp)).filter(
            cls.store_id == store_id).scalar()

        query = cls.query.filter(cls.store_id == store_id).filter(cls.sync_timestamp == latest_sync_timestamp)

        if kwargs.get('cartype_code'):
            query = query.filter(cls.cartype_code == kwargs.get('cartype_code'))

        if kwargs.get('subtype_code'):
            query = query.filter(cls.subtype_code == kwargs.get('subtype_code'))

        if kwargs.get('keywords'):
            raw_keywords = kwargs.get('keywords')
            keywords = '%' + raw_keywords + '%'

            if is_float(raw_keywords):
                price = float(raw_keywords)

                if price < 1000:
                    price *= 10000

                query = query.filter(cls.subtype_code.in_(FrtSharedInventory.get_subtype_code_by_price(price)))
            else:
                query = query.filter(
                    or_(cls.brand_name.like(keywords), cls.class_name.like(keywords), cls.cartype.like(keywords),
                        cls.subtype_name.like(keywords)))

        page = int(kwargs.get('page', DEFAULT_PAGE_START))
        per_page = int(kwargs.get('per_page', DEFAULT_PAGE_SIZE))
        return query.paginate(page, per_page)

    @staticmethod
    def get_subtype_code_by_price(price):
        result = []

        from application.integration.frtinv import DEMO_SUBTYPE_MRSP_CONV

        min_price = price - 1000
        max_price = price + 1000

        for k, v in DEMO_SUBTYPE_MRSP_CONV.iteritems():
            try:
                mrsp = float(v)
                if min_price <= mrsp <= max_price:
                    result.append(k)
            except:
                continue

        return result
