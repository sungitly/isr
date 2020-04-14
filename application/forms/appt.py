# -*- coding: utf-8 -*-
import datetime

from flask.ext.wtf import Form
from wtforms import SelectField, DateField

from application.forms.mixins import SortMixin


class ApptSearchForm(SortMixin, Form):
    start_date = DateField(description=u'开始日期', default=datetime.date.today())
    end_date = DateField(description=u'结束日期', default=datetime.date.today())
    sales_filter = SelectField()
    status_filter = SelectField()
    type_filter = SelectField()
