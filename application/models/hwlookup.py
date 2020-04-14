# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, and_
from sqlalchemy import String

from application.models.base import db


class HwjdLookup(db.Model):
    __tablename__ = 'hwjd_lookup'

    id = Column(Integer, primary_key=True)
    # LX
    type = Column(String(50))
    # CODE
    code = Column(String(50), unique=True)
    # NAME
    name = Column(String(200))
    make = Column(String(100))
    model = Column(String(100))
    # GGXH
    extra = Column(String(200))

    @classmethod
    def refresh(cls, lookup_type, account_info=None):
        if not account_info:
            from application.models.hwaccount import HwjdAccount
            # 如果没有传hwjd账号,则默认使用高德店的账号来获取基本配置信息
            account_info = HwjdAccount.find_by_store_id(11)

        from application.integration.hwjd import get_hwjd_scrb_info
        results = get_hwjd_scrb_info(account_info, lookup_type)

        if len(results) > 0:
            cls.query.filter(cls.type == lookup_type).delete()
            for item in results:
                lookup = HwjdLookup()
                lookup.type = lookup_type
                lookup.code = item['CODE']
                lookup.name = item['NAME']
                lookup.extra = item['GGXH']
                if lookup.type == u'品牌类型':
                    names = lookup.name.split('-')
                    if len(names) >= 2:
                        lookup.make = names[0]
                        lookup.model = names[1]
                db.session.add(lookup)

        return results

    @classmethod
    def find_by_make_models(cls, make, models):
        return cls.query.filter(and_(cls.type == u'品牌类型', cls.make == make, cls.model.in_(models))).order_by(
            cls.make.asc(), cls.model.asc()).all()

    @classmethod
    def find_by_type(cls, type):
        return cls.query.filter(and_(cls.type == type)).order_by(cls.code.asc()).all()

    @staticmethod
    def match_intent_car_lookups(store_ids):
        from application.models.hwaccount import HwjdAccount
        stores = HwjdAccount.find_all_stores()
        if store_ids:
            stores = filter(lambda s: unicode(s.store_id) in store_ids, stores)
        for store_config in stores:
            hwjd_lookupvalues = HwjdLookup.find_by_make_models(store_config.make, store_config.models_array())

            if hwjd_lookupvalues and len(hwjd_lookupvalues) > 0:
                from application.models.lookup import Lookup
                isr_lookup = Lookup.find_by_name_and_store(store_config.store_id, 'intent-car')

                for index, item in enumerate(hwjd_lookupvalues):
                    # 六位的code证明这个值不是具体车型的值,不做mapping
                    if len(item.code) > 6 and item.name != item.extra:
                        from application.models.lookup import LookupValue
                        isr_lookupvalue = LookupValue()
                        # 没用用hwjd的code是因为在报表里, 有可能直接用code来做显示了
                        from application.utils import underscore_join_str
                        isr_lookupvalue.code = u'%s_%s' % (item.model, underscore_join_str(item.extra))
                        isr_lookupvalue.value = item.extra
                        isr_lookupvalue.lookup_id = isr_lookup.id
                        isr_lookupvalue.parent_id = -1
                        # order从10开始,按照10步进
                        isr_lookupvalue.order = 10 + index * 10
                        isr_lookupvalue.section = item.model
                        isr_lookupvalue.version = isr_lookup.version + 1
                        isr_lookupvalue.vendor_code = item.code
                        isr_lookupvalue.vendor_value = item.extra
                        isr_lookupvalue.vendor_section = item.name
                        db.session.add(isr_lookupvalue)

                isr_lookup.version += 1

    @staticmethod
    def match_age_group_lookups(store_ids):
        from application.models.hwaccount import HwjdAccount
        stores = HwjdAccount.find_all_stores()
        if store_ids:
            stores = filter(lambda s: unicode(s.store_id) in store_ids, stores)

        for store_config in stores:
            from application.models.lookup import Lookup
            isr_lookup = Lookup.find_by_name_and_store(store_config.store_id, 'age-group')

            hwjd_lookupvalues = HwjdLookup.find_by_type(u'市场-年龄')
            for index, item in enumerate(hwjd_lookupvalues):
                from application.models.lookup import LookupValue
                isr_lookupvalue = LookupValue()
                isr_lookupvalue.code = item.name
                isr_lookupvalue.value = item.name
                isr_lookupvalue.lookup_id = isr_lookup.id
                isr_lookupvalue.parent_id = -1
                # order从10开始,按照10步进
                isr_lookupvalue.order = 10 + index * 10
                isr_lookupvalue.version = isr_lookup.version + 1
                isr_lookupvalue.vendor_code = item.code
                isr_lookupvalue.vendor_value = item.name
                db.session.add(isr_lookupvalue)

            isr_lookup.version += 1

    @staticmethod
    def match_intent_level_lookups(store_ids):
        from application.models.hwaccount import HwjdAccount
        stores = HwjdAccount.find_all_stores()
        if store_ids:
            stores = filter(lambda s: unicode(s.store_id) in store_ids, stores)
        for store_config in stores:
            from application.models.lookup import Lookup
            isr_lookup = Lookup.find_by_name_and_store(store_config.store_id, 'intent-level')

            hwjd_lookupvalues = HwjdLookup.find_by_type(u'市场-级别')
            for index, item in enumerate(hwjd_lookupvalues):
                from application.models.lookup import LookupValue
                isr_lookupvalue = LookupValue()
                isr_lookupvalue.code = item.name
                isr_lookupvalue.value = item.name
                isr_lookupvalue.lookup_id = isr_lookup.id
                isr_lookupvalue.parent_id = -1
                # order从10开始,按照10步进
                isr_lookupvalue.order = 10 + index * 10
                isr_lookupvalue.version = isr_lookup.version + 1
                isr_lookupvalue.vendor_code = item.code
                isr_lookupvalue.vendor_value = item.name
                db.session.add(isr_lookupvalue)

            isr_lookup.version += 1
