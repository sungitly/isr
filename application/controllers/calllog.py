# -*- coding: utf-8 -*-
from flask import Blueprint, request, render_template, g

from application.forms.mixins import SortMixin
from application.models.calllog import Calllog
from application.nutils.menu import CALL_LOG
from application.pagination import get_page_info
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from application.utils import get_sales_selection

bp = Blueprint('calllogs', __name__, url_prefix="/calllogs")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def calllogs():
    current_user = g.user
    store_id = get_or_set_store_id()

    from application.forms.calllog import CalllogSearchForm
    search_form = CalllogSearchForm(request.args)
    search_form.sales_filter.choices = get_sales_selection(store_id)

    query = dict()
    if search_form.start_date.data and search_form.start_date.data != '':
        query['start_date'] = search_form.start_date.data
    if search_form.end_date.data and search_form.end_date.data != '':
        query['end_date'] = search_form.end_date.data
    if search_form.sales_filter.data not in ('None', 'all'):
        query['sales_filter'] = search_form.sales_filter.data
    if search_form.keywords.data:
        query['keywords'] = search_form.keywords.data

    sort_params = SortMixin.get_order_query(search_form)
    if sort_params:
        query.update(sort_params)

    query.update(get_page_info(request))

    calllogs = Calllog.find_all_by_query_params_in_store(store_id, **query)
    return render_template('calllogs/calllogs.html', selected_menu=CALL_LOG, form=search_form,
                           calllogs=calllogs, back_endpoint=request.args.get('back_endpoint', None))
