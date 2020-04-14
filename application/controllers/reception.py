# -*- coding: utf-8 -*-

from flask import Blueprint, request, render_template, g

import datetime
from application.forms.mixins import SortMixin
from application.models.reception import Reception
from application.nutils.menu import RX_VIEW
from application.pagination import get_page_info
from application.permissions import UserPermission
from application.utils import get_sales_selection
from application.session import get_or_set_store_id

bp = Blueprint('receptions', __name__, url_prefix="/receptions")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def receptions():
    current_user = g.user
    store_id = get_or_set_store_id()

    from application.forms.reception import RxSearchForm
    search_form = RxSearchForm(request.args)
    search_form.type_filter.choices = get_type_selection()
    search_form.sales_filter.choices = get_sales_selection(store_id)
    search_form.status_filter.choices = get_status_selection()

    query = dict()
    if search_form.start_date.data and search_form.start_date.data != '':
        query['start_date'] = search_form.start_date.data
    if search_form.end_date.data and search_form.end_date.data != '':
        query['end_date'] = search_form.end_date.data
    if search_form.type_filter.data and search_form.type_filter.data not in ('None', 'all'):
        query['type_filter'] = search_form.type_filter.data
    if search_form.sales_filter.data not in ('None', 'all'):
        query['sales_filter'] = search_form.sales_filter.data
    if search_form.incomplete.data:
        query['incomplete'] = search_form.incomplete.data
    if search_form.status_filter.data not in ('None', 'all'):
        query['status'] = search_form.status_filter.data

    sort_params = SortMixin.get_order_query(search_form)
    if sort_params:
        query.update(sort_params)
    query.update(get_page_info(request))

    receptions = Reception.find_all_by_query_params_in_store(store_id, **query)
    return render_template('receptions/receptions.html', selected_menu=RX_VIEW, form=search_form,
                           receptions=receptions, back_endpoint=request.args.get('back_endpoint', None),
                           today=datetime.date.today())


def get_type_selection():
    selections = [('all', u'接待类型'), ('new', u'首次'), ('appt_new', u'首邀'), ('appt', u'再次'), ('other', u'手续')]

    return selections


def get_status_selection():
    selections = [('all', u'接待状态'), ('completed', u'离店客户'), ('in-store', u'在店客户')]
    return selections
