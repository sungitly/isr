# -*- coding: utf-8 -*-
import uuid
from datetime import timedelta

from sqlalchemy import Column, BigInteger, DateTime, Integer, Date
from sqlalchemy import String

from application.models.base import db, BaseMixin
from application.models.lookup import LookupValue
from application.models.order import Order
from application.utils import TIME_FORMAT_WO_SEC, parse_comma_seperated_args

VENDOR_CODE = 'HWJD'


def convert_boolean(bool):
    if bool:
        return u'是'
    else:
        return u'否'


def convert_car_code(store_id, isr_car_codes):
    car_codes = parse_comma_seperated_args(isr_car_codes)

    if car_codes and len(car_codes) > 0:
        car_code = car_codes[0]  # use the first one
        lookups = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), 'intent-car')
        lookup = lookups.get(car_code)

        if lookup:
            return lookup.vendor_code, lookup.vendor_section, lookup.vendor_value

    return '', '', ''


def convert_visit_type(rx_type):
    return u'到店'


def convert_rx_type(rx_type):
    if 'new' == rx_type:
        return u'首次'
    elif 'appt_new' == rx_type:
        return u'电话预约'
    elif 'appt' == rx_type:
        return u'再次'
    else:
        return u'非购车'


def convert_purchase_type(customer):
    # 可用类型 '置换', '添置', '新购'
    if customer.is_car_replace:
        return u'置换'
    else:
        return u'新购'


class HwjdCustomer(db.Model, BaseMixin):
    __tablename__ = 'hwjd_customer'

    # type: hash
    redis_key_vendor_store_info = 'isr:int:vendor:%s:store:%s'

    reception_id = Column(BigInteger, nullable=False, unique=True)
    customer_id = Column(BigInteger, nullable=False)
    store_id = Column(BigInteger, nullable=False, index=True)

    uuid = Column(String(50), unique=True)
    company_code = Column(String(50), nullable=False)
    created_date = Column(Date)
    intent_car_code = Column(String(100))
    intent_car_model = Column(String(100))
    visit_type = Column(String(50))
    rx_start = Column(String(100))
    rx_end = Column(String(100))
    rx_duration = Column(String(100))
    rx_type = Column(String(50))
    channel = Column(String(50))
    sales = Column(String(50))
    intent_car_name = Column(String(100))
    intent_car_color = Column(String(50))
    intent_order_date = Column(Date)
    budget = Column(String(50))
    payment = Column(String(50))
    purpose = Column(String(50))
    purchase_type = Column(String(50))
    intent_level = Column(String(50))
    on_file = Column(String(50))
    has_trail = Column(String(50))
    name = Column(String(200))
    age_group = Column(String(50))
    gender = Column(String(50))
    industry = Column(String(50))
    district = Column(String(100))
    mobile = Column(String(200))
    has_order = Column(String(50))
    dealership = Column(String(50))
    discount = Column(String(50))
    price = Column(String(50))
    gadgets_gift = Column(String(50))
    gadgets_purchase = Column(String(50))
    competing_car_brand = Column(String(100))
    competing_car_name = Column(String(100))
    used_car_model = Column(String(100))
    used_car_value = Column(String(50))
    has_used_car_assessed = Column(String(50))
    remark = Column(String(500))

    last_sync_date = Column(DateTime)
    last_sync_status = Column(Integer)

    vendor_fields = ['uuid', 'company_code', 'created_date', 'intent_car_code', 'intent_car_model', 'visit_type',
                     'rx_start', 'rx_end', 'rx_duration', 'rx_type', 'channel', 'sales', 'intent_car_name',
                     'intent_car_color', 'intent_order_date', 'budget', 'payment', 'purpose', 'purchase_type',
                     'intent_level', 'on_file', 'has_trail', 'name', 'age_group', 'gender', 'industry', 'district',
                     'mobile', 'has_order', 'dealership', 'discount', 'price', 'gadgets_gift', 'gadgets_purchase',
                     'competing_car_brand', 'competing_car_name', 'used_car_model', 'used_car_value',
                     'has_used_car_assessed', 'remark']
    vendor_joiner = '^'

    @classmethod
    def find_by_reception_id(cls, reception_id):
        return cls.query.filter(cls.reception_id == reception_id).first()

    @classmethod
    def convert_from_reception(cls, reception):
        hc = cls.find_by_reception_id(reception.id)

        if not hc:
            hc = cls()
            hc.reception_id = reception.id
            hc.customer_id = reception.customer_id
            hc.store_id = reception.store_id
            hc.uuid = str(uuid.uuid4())

        customer = reception.customer

        from application.models.hwaccount import HwjdAccount
        hwjd_account = HwjdAccount.find_by_store_id(hc.store_id)
        hc.company_code = hwjd_account.org_code if hwjd_account else ''
        hc.created_date = reception.rx_date
        hc.intent_car_code, hc.intent_car_model, hc.intent_car_name = convert_car_code(hc.store_id,
                                                                                       customer.intent_car_ids)
        hc.visit_type = convert_visit_type(reception.rx_type)
        hc.rx_start = reception.created_on.strftime(TIME_FORMAT_WO_SEC)
        hc.rx_end = (reception.created_on + timedelta(seconds=reception.rx_duration)).strftime(TIME_FORMAT_WO_SEC)
        hc.rx_duration = reception.rx_duration
        hc.rx_type = convert_rx_type(reception.rx_type)
        hc.channel = u'其他'
        hc.sales = reception.sales.username
        hc.intent_car_color = customer.intent_car_colors.split(',')[
            0] if customer.intent_car_colors and len(customer.intent_car_colors) > 0 else ''
        hc.intent_order_date = None
        hc.budget = customer.budget
        hc.payment = customer.payment
        hc.purchase_type = convert_purchase_type(customer)
        hc.intent_level = LookupValue.get_vendor_code_by_code(customer.intent_level, hc.store_id, 'intent-level')
        hc.on_file = convert_boolean(customer.mobile and len(customer.mobile) >= 11)
        hc.has_trail = convert_boolean(
            customer.test_drive_car_ids and customer.test_drive_car_ids != 'none' and len(
                customer.test_drive_car_ids) > 0)
        hc.name = customer.respect_name
        hc.age_group = LookupValue.get_vendor_code_by_code(customer.channel, hc.store_id, 'age-group')
        hc.gender = customer.gender_str
        hc.mobile = customer.mobile if customer.mobile and customer.mobile != '000' else ''
        hc.has_order = convert_boolean(Order.has_valid_orders_by_customer(hc.customer_id))
        hc.discount = ''
        hc.price = ''
        hc.gadgets_gift = u'否'
        hc.gadgets_purchase = u'否'
        hc.competing_car_brand = u'未定'
        hc.competing_car_name = u'未定'
        hc.used_car_model = u'无'
        hc.remark = customer.remark

        from application.models.customer import CustomerAddlInfo
        addl_info = CustomerAddlInfo.find_by_customer_id(reception.customer_id)
        if addl_info:
            hc.purpose = addl_info.purpose
            hc.industry = addl_info.industry
            hc.district = addl_info.district
            hc.dealership = addl_info.dealership
            hc.used_car_value = addl_info.used_car_value
            hc.has_used_car_assess = addl_info.has_used_car_assessed

        return hc

    def to_xml(self):
        vendor_fields_values = []

        for field in self.vendor_fields:
            value = getattr(self, field)
            vendor_fields_values.append(unicode(value) if value is not None else u'')

        return u'<Root><BillHeader>' + self.vendor_joiner.join(vendor_fields_values) + u'</BillHeader></Root>'
