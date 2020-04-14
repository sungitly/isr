# -*- coding: utf-8 -*-
import datetime
import json
from collections import OrderedDict

from application.models.base import db, BaseMixin, StoreMixin, get_user_id
from application.nutils.date import parse_date
from application.nutils.excel import parse_excel
from application.nutils.numbers import is_float
from sqlalchemy import Column, String, Numeric, Date, DateTime, BigInteger, Text, desc, distinct, Boolean, and_, or_


class Inventory(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'inventory'

    vin = Column(String(50), index=True)
    car_brand = Column(String(20))  # 品牌
    car_class = Column(String(200))  # 车系
    car_type = Column(String(200))  # 车型
    car_subtype = Column(String(200))  # 细分车型
    acc_info = Column(String(200))  # 增配信息
    acc_price = Column(Numeric(precision=12, scale=2))  # 增配价格
    color_name = Column(String(50))  # 车身色
    color_attribute = Column(String(50))  # 内饰颜色
    source = Column(String(50))  # 车源
    in_price = Column(Numeric(precision=12, scale=2))  # 采购价格
    inv_status = Column(String(50))  # 库存状态
    out_factory_date = Column(Date)  # 出厂日期
    stockin_date = Column(Date)  # 入库日期
    mrsp = Column(Numeric(precision=12, scale=2))  # 建议售价
    rebate_amt = Column(Numeric(precision=12, scale=2))  # 折扣
    remark = Column(Text)

    extra = Column(Text)

    is_deleted = Column(Boolean, default=0)

    fields_mapper = OrderedDict([(u'车架号', 'vin'),
                                 (u'品牌', 'car_brand'),
                                 (u'车系', 'car_class'),
                                 (u'车型', 'car_type'),
                                 (u'细分车型', 'car_subtype'),
                                 (u'增配信息', 'acc_info'),
                                 (u'增配价格', 'acc_price'),
                                 (u'车身色', 'color_name'),
                                 (u'内饰颜色', 'color_attribute'),
                                 (u'车源', 'source'),
                                 (u'采购价格', 'in_price'),
                                 (u'库存状态', 'inv_status'),
                                 (u'出厂日期', 'out_factory_date'),
                                 (u'入库日期', 'stockin_date'),
                                 (u'建议售价', 'mrsp'),
                                 (u'折扣', 'rebate_amt'), (u'备注', 'remark')])

    def repr_dict(self):
        ret = []

        for k, v in Inventory.fields_mapper.iteritems():
            ret.append({'name': k, 'value': getattr(self, v, None)})
        return ret

    @classmethod
    def find_all_by_store_id_wo_pagination(cls, store_id):
        return cls.query.filter(and_(cls.store_id == store_id, cls.is_deleted == 0)).order_by(
                desc(cls.updated_on)).all()

    @classmethod
    def find_by_vin(cls, vin):
        return cls.query.filter(and_(cls.vin == vin, cls.is_deleted == 0)).first()

    def validate(self):
        # return self.vin and len(unicode(self.vin).strip()) == 17
        return True

    @classmethod
    def get_lookups(cls, store_id, type):
        car_types_result = cls.find_distinct_field_values_by_store(cls.car_type, store_id)
        color_names_result = cls.find_distinct_field_values_by_store(cls.color_name, store_id)
        color_attr_result = cls.find_distinct_field_values_by_store(cls.color_attribute, store_id)

        return {
            'car_type': [item[0] for item in car_types_result if item[0]],
            'color_name': [item[0] for item in color_names_result if item[0]],
            'color_attribute': [item[0] for item in color_attr_result if item[0]]
        }

    @classmethod
    def find_all_by_criteria_in_store(cls, fuzzy, store_id, **kwargs):
        kwargs = cls.clean_filters(kwargs)

        query = cls.query.filter(and_(cls.store_id == store_id, cls.is_deleted == 0))

        if fuzzy:
            for k, v in kwargs.items():
                if hasattr(cls, k):
                    query = query.filter(getattr(cls, k).like('%%%s%%' % v))
            return query.all()
        else:
            for k, v in kwargs.items():
                if hasattr(cls, k):
                    query = query.filter(getattr(cls, k) == v)

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
                            or_(cls.vin.like(keywords), cls.car_class.like(keywords),
                                cls.car_type.like(keywords), cls.car_subtype.like(keywords),
                                cls.source.like(keywords),
                                cls.color_name.like(keywords), cls.color_attribute.like(keywords)))
            return query.all()

    @classmethod
    def clean_filters(cls, filters):
        ret = dict()
        for k, v in filters.iteritems():
            if v and len(unicode(v)) > 0:
                ret[k] = v
        return ret

    @classmethod
    def find_distinct_field_values_by_store(cls, field, store_id):
        return db.session.query(distinct(field)).filter(and_(cls.store_id == store_id, cls.is_deleted == 0)).all()

    @staticmethod
    def create_mock_inv(**kwargs):
        inv = Inventory(**kwargs)
        now = datetime.datetime.now()
        inv.created_on = now
        inv.updated_on = now
        inv.created_by = -1000
        inv.updated_by = -1000
        return inv

    @staticmethod
    def save_from_excel(filepath, store_id):
        # delete all existing inventories
        Inventory.query.filter(and_(Inventory.store_id == store_id, Inventory.is_deleted == 0)).update(
                {'is_deleted': 1})

        data = Inventory.parse_excel(filepath, store_id)
        # TODO validate data
        for row in data:
            if isinstance(row, Inventory) and row.validate():
                # since all existing inv will be soft deleted, update is not necessary.
                # existing_inv = Inventory.find_by_vin(row.vin)
                # if existing_inv:
                #     row.id = existing_inv.id
                row.save()
        return data

    @staticmethod
    def parse_excel(filepath, store_id):
        ret = []

        data_rows = parse_excel(filepath)
        for data in data_rows:
            ret.append(Inventory.map_data(data, store_id))

        return ret

    @staticmethod
    def map_data(data, store_id):
        main_info = dict()
        extra_info = dict()

        for key, value in data.iteritems():
            mapped_key = Inventory.fields_mapper.get(key, None)

            if mapped_key:
                # convert to datetime for out_factory_date and stockin_date
                if mapped_key in ('out_factory_date', 'stockin_date') and value:
                    value = parse_date(value)
                main_info[mapped_key] = value
            else:
                extra_info[key] = value

        inv = Inventory(**main_info)
        if len(extra_info) > 0:
            inv.extra = json.dumps(extra_info)
        inv.store_id = store_id
        return inv


class InvImportHistory(db.Model):
    __tablename__ = 'inv_import_his'

    id = Column(BigInteger, primary_key=True)
    created_on = Column(DateTime, default=datetime.datetime.now)
    created_by = Column(String(50), default=get_user_id)
    origin_file = Column(String(100))
    import_file = Column(String(500))
