# -*- coding: utf-8 -*-
import datetime

from application.forms.mixins import SortMixin
from flask.ext.babel import gettext
from flask.ext.wtf import Form
from wtforms import SelectField, StringField, HiddenField, DateField, BooleanField


class OrderSearchForm(SortMixin, Form):
    start_date = DateField(description=u'开始日期', default=datetime.date.today())
    end_date = DateField(description=u'结束日期', default=datetime.date.today())
    ordered_car_ids_filter = SelectField()
    sales_filter = SelectField()
    status_filter = SelectField()
    keywords = StringField(gettext(u'keywords'))
    history = BooleanField(description=u'历史订单')


class OrderCancelForm(Form):
    order_id = HiddenField()
