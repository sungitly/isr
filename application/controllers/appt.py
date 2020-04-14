# -*- coding: utf-8 -*-
from application.forms.mixins import SortMixin
from application.models.appointment import Appointment
from application.nutils.menu import APPTS_VIEW
from application.pagination import get_page_info
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from application.utils import get_sales_selection
from flask import Blueprint, request, render_template, g

bp = Blueprint('appointments', __name__, url_prefix="/appointments")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def appts():
    current_user = g.user
    store_id = get_or_set_store_id()

    from application.forms.appt import ApptSearchForm
    search_form = ApptSearchForm(request.args)
    search_form.type_filter.choices = get_type_selection()
    search_form.status_filter.choices = get_status_selection()
    search_form.sales_filter.choices = get_sales_selection(store_id)

    query = dict()
    if search_form.start_date.data and search_form.start_date.data != '':
        query['start_date'] = search_form.start_date.data
    if search_form.end_date.data and search_form.end_date.data != '':
        query['end_date'] = search_form.end_date.data
    if search_form.type_filter.data and search_form.type_filter.data not in ('None', 'all'):
        query['type_filter'] = search_form.type_filter.data
    if search_form.status_filter.data and search_form.status_filter.data not in ('None', 'all'):
        query['status'] = search_form.status_filter.data
    if search_form.sales_filter.data and search_form.sales_filter.data not in ('None', 'all'):
        query['sales_filter'] = search_form.sales_filter.data

    sort_params = SortMixin.get_order_query(search_form)
    if sort_params:
        query.update(sort_params)

    query.update(get_page_info(request))

    appts = Appointment.find_all_by_query_params_in_store(store_id, **query)
    return render_template('appts/appts.html', selected_menu=APPTS_VIEW, form=search_form,
                           back_endpoint=request.args.get('back_endpoint', None),
                           appts=appts)


def get_type_selection():
    selections = [('all', u'预约类型'), ('instore', u'预约到店'), ('deliver', u'预约交车'),
                  ('other', u'预约手续'), ('followup', u'预约回访'), ('deliver_followup', u'交车跟进')]

    return selections


def get_status_selection():
    selections = [('all', u'预约状态'), ('opened', u'未完成'), ('closed', u'已完成'), ('cancelled', u'已取消')]

    return selections
