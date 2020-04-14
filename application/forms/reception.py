# -*- coding: utf-8 -*-
import datetime

from flask.ext.wtf import Form
from wtforms import SelectField, DateField, BooleanField

from application.forms.mixins import SortMixin


class RxSearchForm(SortMixin, Form):
    start_date = DateField(description=u'开始日期', default=datetime.date.today())
    end_date = DateField(description=u'结束日期', default=datetime.date.today())
    sales_filter = SelectField()
    type_filter = SelectField()
    incomplete = BooleanField(description=u'未离店留档')
    status_filter = SelectField()
