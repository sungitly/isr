# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileRequired, FileAllowed, FileField
from wtforms import SelectField, DateField, StringField, TextAreaField, IntegerField, FieldList, FormField, \
    SubmitField
from wtforms.validators import DataRequired


class TimePeriodForm(Form):
    start = DateField(description=u'开始日期')
    end = DateField(description=u'结束日期')


class GenericSearchForm(Form):
    start = DateField(description=u'开始日期')
    end = DateField(description=u'结束日期')
    store_filter = SelectField()


class AppUpgradeForm(Form):
    version = StringField(validators=[DataRequired(u'版本不能为空')])
    version_num = StringField(validators=[DataRequired(u'版本号不能为空')])
    note = TextAreaField()


class LookupvalueForm(Form):
    store_filter = SelectField()
    lookup_filter = SelectField()


class AddLookupvalueForm(Form):
    value = StringField()
    orders = IntegerField()
    section = StringField()


class TotalLookupvalueForm(Form):
    lookupvalues = FieldList(FormField(AddLookupvalueForm), min_entries=5, max_entries=10)
    submits = SubmitField(u"提交")


class CreateLookupvalueForm(Form):
    lookupvalue_file = FileField(u"上传经销商信息:", validators=[FileRequired()])
    update = SubmitField(u"更新")
