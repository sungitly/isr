# -*- coding: utf-8 -*-
from flask.ext.babel import gettext
from flask_wtf import Form
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired

from application.forms.mixins import SortMixin


class CustomerSearchForm(SortMixin, Form):
    intent_level_filter = SelectField()
    intent_car_ids_filter = SelectField()
    last_instore_filter = SelectField(default=0)
    status_filter = SelectField()
    sales_filter = SelectField()
    keywords = StringField(gettext(u'keywords'))


class CustomerReassignForm(Form):
    saleses_list = SelectField('', validators=[DataRequired(u'new sales cannot be empty')])
