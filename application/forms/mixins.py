# -*- coding: utf-8 -*-
from wtforms import HiddenField, StringField, IntegerField, SelectField
from sqlalchemy import desc, asc
from sqlalchemy.orm.attributes import InstrumentedAttribute

from application.forms.fields import HiddenIntField


class SortMixin(object):
    '''Form上面加入排序功能'''
    ORDER_NORMAL = 0 #不排序
    ORDER_ASC = 1    #正向排序
    ORDER_DESC = 2  #逆向排序

    sort_by_field = HiddenField()
    sort_by_order = HiddenIntField(default=ORDER_NORMAL)

    @staticmethod
    def get_order_query(form):
        filed = form.sort_by_field.data
        if not filed:
            return None
        order = form.sort_by_order.data
        if order not in [SortMixin.ORDER_ASC, SortMixin.ORDER_DESC]:
            return None
        return {'_sort_query': {
            'field': filed,
            'order': order
        }}

    @staticmethod
    def add_order_query(query, cls, sortable_fields, query_params):
        if '_sort_query' not in query_params:
            return query
        sort_query = query_params['_sort_query']
        field = sort_query['field']
        order = sort_query['order']
        if field not in sortable_fields:
            return query
        order_func = None
        if order == SortMixin.ORDER_ASC:
            order_func = asc
        if order == SortMixin.ORDER_DESC:
            order_func = desc
        field_db = getattr(cls, field, None)
        if not field_db or not isinstance(field_db, InstrumentedAttribute):
            return query
        query_by_order = query.order_by(order_func(field_db))
        return query_by_order
