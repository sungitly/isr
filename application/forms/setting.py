# -*- coding: utf-8 -*-
from flask.ext.babel import gettext
from flask.ext.wtf import Form
from wtforms import StringField, HiddenField
from wtforms.validators import DataRequired


class TAForm(Form):
    date = HiddenField(validators=[DataRequired(gettext(u'TA Date'))])
    ta = StringField(gettext(u'TA'), validators=[DataRequired(gettext(u'ta value'))])
    type = HiddenField()
