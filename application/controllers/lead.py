# -*- coding: utf-8 -*-
import datetime

from application.models.reception import Reception
from application.nutils.menu import LEADS_VIEW
from application.pagination import get_page_info
from application.permissions import UserPermission
from flask import Blueprint, request, render_template, g

bp = Blueprint('leads', __name__, url_prefix="/leads")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def leads():
    current_user = g.user
    store_id = current_user.store_id

    from application.forms.lead import LeadSearchForm
    search_form = LeadSearchForm(request.args)

    query = dict()
    if search_form.start_date.data and search_form.start_date.data != '':
        query['start_date'] = search_form.start_date.data
    if search_form.end_date.data and search_form.end_date.data != '':
        query['end_date'] = search_form.end_date.data
    if search_form.on_file.data:
        query['on_file'] = search_form.on_file.data

    query.update(get_page_info(request))

    rx = Reception.find_all_leads_by_query_params_in_store(store_id, **query)

    return render_template('leads/leads.html', selected_menu=LEADS_VIEW, form=search_form,
                           leads=rx, back_endpoint=request.args.get('back_endpoint', None),
                           today=datetime.date.today())
