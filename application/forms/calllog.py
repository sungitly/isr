# -*- coding: utf-8 -*-
import datetime

from flask.ext.babel import gettext
from flask.ext.wtf import Form
from wtforms import SelectField, DateField, StringField

from application.forms.mixins import SortMixin


class CalllogSearchForm(SortMixin, Form):
    start_date = DateField(description=u'开始日期', default=datetime.date.today())
    end_date = DateField(description=u'结束日期', default=datetime.date.today())
    sales_filter = SelectField()
    keywords = StringField(gettext(u'keywords'))
