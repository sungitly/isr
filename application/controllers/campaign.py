# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, g, request, redirect, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.controllers._helper import flash_success
from application.forms.mixins import SortMixin
from application.models.campaign import Campaign
from application.models.lookup import LookupValue, Lookup
from application.nutils.menu import CAMPAIGN_MGMT
from application.nutils.url import back_url
from application.pagination import get_page_info
from application.permissions import UserPermission
from application.session import get_or_set_store_id

bp = Blueprint('campaigns', __name__, url_prefix="/campaigns")


@bp.route('/', methods=['GET', 'POST'])
@UserPermission()
def campaigns():
    current_user = g.user
    store_id = get_or_set_store_id()
    from application.forms.campaign import CampaignSearchForm
    form = CampaignSearchForm(request.args)

    type = form.type.data
    keywords = form.keywords.data
    days = None
    active = False
    if type == 'active-campaigns':
        days = 15
        active = True

    query = {
        'days': days,
        'active': active,
        'keywords': keywords,
    }

    sort_params = SortMixin.get_order_query(form)
    if sort_params:
        query.update(sort_params)
    query.update(get_page_info(request))

    campaigns = Campaign.find_all_by_store_in_recent_days_and_keywords(store_id, **query)

    return render_template('campaigns/campaigns.html', selected_menu=CAMPAIGN_MGMT, form=form, campaigns=campaigns,
                           back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/<int:campaign_id>', methods=['GET', 'POST', 'PUT'])
@UserPermission()
def edit_campaign(campaign_id):
    current_user = g.user
    store_id = get_or_set_store_id()

    campaign = Campaign.find_by_id_and_store(campaign_id, store_id)

    if not campaign:
        abort(404)

    return edit(CAMPAIGN_MGMT, campaign=campaign)  # render_template('campaigns/edit.html', selected_menu=CAMPAIGN_MGMT)


@bp.route('/new', methods=['GET', 'POST', 'PUT'])
@UserPermission()
def create_campaign():
    return edit(CAMPAIGN_MGMT)


def edit(selected_menu, campaign=None):
    current_user = g.user
    store_id = get_or_set_store_id()

    from application.forms.campaign import CampaignForm

    form = None
    campaign_cars = []
    if campaign:
        campaign_cars = campaign.related_cars.split(',')
        form = CampaignForm(obj=campaign)
    else:
        form = CampaignForm()

    lookup = Lookup.find_by_name_and_store(store_id, 'intent-car')

    if lookup:
        cars = LookupValue.find_all_by_lookup_id(lookup.id)
        form.related_cars.choices = [(car.code, car.value) for car in cars]

    if form.related_cars.choices is None:
        form.related_cars.choices = []

    if request.method == 'GET':
        form.related_cars.data = campaign_cars

    if request.method == 'POST' and form.validate_on_submit():
        if campaign is None:
            campaign = Campaign()
            campaign.store_id = store_id
        form.populate_obj(campaign)
        campaign.related_cars = u','.join(form.related_cars.data)
        campaign.save_and_flush()
        flash_success(gettext(u'campaign saved'))

        return redirect(url_for('campaigns.campaigns'))
        # form.
        # campaign = form.po
        # if form.validate_on_submit():
        # json_r = uc_login(form.username.data, form.password.data)
        #
        # if json_r and json_r['status'] == 0 and get_user_type(json_r) == 6:
        #     user = save_user_from_uc(json_r)
        #     add_user(user)
        #     return redirect(referer or url_for('user.dashboard'))
        #
        # flash_error(gettext(u'login failed'))

    return render_template('campaigns/edit.html', selected_menu=selected_menu, campaign=campaign, form=form,
                           back_url=back_url(url_for('campaigns.campaigns')))
