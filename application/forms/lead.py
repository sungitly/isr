# -*- coding: utf-8 -*-
import datetime

from flask.ext.wtf import Form
from wtforms import DateField, BooleanField


class LeadSearchForm(Form):
    start_date = DateField(description=u'开始日期', default=datetime.date.today())
    end_date = DateField(description=u'结束日期', default=datetime.date.today())
    on_file = BooleanField(description=u'留档？')
