# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from dateutil.parser import parse
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.models.appointment import Appointment
from application.models.order import Order
from application.models.reception import Reception
from application.nutils.date import parse_date


def get_appt_validator(store_id):
    if not store_id:
        return None
    elif unicode(store_id) == u'4':
        return YunTongApptValidator()
    elif unicode(store_id) == u'87':
        return ZhiYuanApptValidator()


class YunTongApptValidator(object):
    def validate(self, appt_data):
        now_time = datetime.now()
        appt_type = appt_data.get('type', None)
        appt_time = parse(appt_data.get('appt_datetime'))
        store_id = appt_data.get('store_id')
        if appt_type and appt_type == 'followup':
            customer = appt_data.get('customer', None)
            if customer and customer.is_active():
                # 1. 未成交客户, 预约回访时间不得晚于当前时间+10天
                general_time_limit = now_time + timedelta(days=10)
                if appt_time > general_time_limit:
                    abort(400, description=gettext('appt_datetime can not be later than %(days)s days', days=10))

                # 2. 如果客户是首次客户, 首次预约回访时间不得晚于到店第二天晚上24时
                receptions = Reception.find_all_by_customer_sales(customer.id)
                if receptions and len(receptions) == 1:
                    last_rx_date = receptions[0].rx_date
                    rx_limit = last_rx_date + timedelta(days=1)
                    if not Appointment.exist_followup_between_dates_by_customer(parse_date(now_time), parse_date(
                            rx_limit), customer.id, store_id) and parse_date(now_time) <= parse_date(rx_limit) \
                            < parse_date(appt_time):
                        abort(400, description=gettext('appt_datetime can not be later than 1 days for new customer'))
            elif customer.status == 'ordered':
                # 3. 如果客户是交车客户, 预约交车时间不得晚于交车第二天晚上24时
                order = Order.find_latest_delivered_order_by_customer(customer.id)
                if order:
                    delivered_date = order.delivered_date
                    order_limit = delivered_date + timedelta(days=1)
                    if not Appointment.exist_followup_between_dates_by_customer(parse_date(now_time), parse_date(
                            order_limit), customer.id, store_id) and parse_date(now_time) <= parse_date(order_limit) < \
                            parse_date(appt_time):
                        abort(400,
                              description=gettext('appt_datetime can not be later than 1 days for delivered customer'))


class ZhiYuanApptValidator(object):
    def validate(self, appt_data):
        now_time = datetime.now()
        appt_type = appt_data.get('type', None)
        appt_time = parse(appt_data.get('appt_datetime'))
        store_id = appt_data.get('store_id')
        if appt_type and appt_type == 'followup':
            customer = appt_data.get('customer', None)
            if customer and customer.is_active():
                # 1. 未成交客户, 预约回访时间不得晚于当前时间+7天
                general_time_limit = now_time + timedelta(days=7)
                if appt_time > general_time_limit:
                    abort(400, description=gettext('appt_datetime can not be later than %(days)s days', days=7))

                # 2. 如果客户是首次客户, 首次预约回访时间不得晚于到店第二天晚上24时
                receptions = Reception.find_all_by_customer_sales(customer.id)
                if receptions and len(receptions) == 1:
                    last_rx_date = receptions[0].rx_date
                    rx_limit = last_rx_date + timedelta(days=1)
                    if not Appointment.exist_followup_between_dates_by_customer(parse_date(now_time), parse_date(
                            rx_limit), customer.id, store_id) and parse_date(now_time) <= parse_date(rx_limit) \
                            < parse_date(appt_time):
                        abort(400, description=gettext('appt_datetime can not be later than 1 days for new customer'))
