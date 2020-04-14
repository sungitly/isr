# -*- coding: utf-8 -*-
from flask.ext.babel import gettext
from flask_wtf import Form
from wtforms import StringField, RadioField, SelectMultipleField, DateField, ValidationError
from wtforms.validators import DataRequired
from wtforms.widgets import TextArea, CheckboxInput, ListWidget

from application.forms.mixins import SortMixin


def validate_end_date(form, field):
    start_date = form.start.data
    if field.data <= start_date:
        raise ValidationError(gettext(u'end time cannot be earlier than start time'))


def validate_notify_date(form, field):
    start_date = form.start.data
    if field.data >= start_date:
        raise ValidationError(u'notify time cannot be later than start time')


class CampaignSearchForm(SortMixin, Form):
    keywords = StringField(gettext(u'keywords'))
    type = RadioField(u'', choices=[('active-campaigns', gettext(u'recently active campaigns')),
                                    ('all-campaigns', gettext(u'all campaigns'))], default='active-campaigns')


class CampaignForm(Form):
    _store_id = None
    title = StringField(gettext(u'campaign title'),
                        validators=[DataRequired(gettext(u'campaign title cannot be empty'))])
    content = StringField(gettext(u'campaign detail'),
                          validators=[DataRequired(gettext(u'campaign detail cannot be empty'))], widget=TextArea())

    related_cars = SelectMultipleField(
        gettext(u'related cars'),
        option_widget=CheckboxInput(),
        widget=ListWidget(prefix_label=False)
    )

    start = DateField(gettext(u'start time'), format='%m/%d/%Y',
                      validators=[DataRequired(gettext(u'start time cannot be empty'))])
    end = DateField(gettext(u'end time'), format='%m/%d/%Y',
                    validators=[DataRequired(gettext(u'end time cannot be empty')), validate_end_date])
    notify_date = DateField(gettext(u'notify time'), format='%m/%d/%Y',
                            validators=[DataRequired(gettext(u'notify time cannot be empty')), validate_notify_date])
