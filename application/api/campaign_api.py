# -*- coding: utf-8 -*-
from datetime import date

from application.api import api
from application.handlers import notify_all_sales_of_store
from application.models.campaign import Campaign, push_msg_for_campaign_creation, push_msg_for_campaign_update
from application.pagination import get_page_info
from application.utils import add_location_header
from flask import request, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort


@api.route('/campaigns', methods=['POST'])
def create_campaign():
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    campaign = Campaign(**data)

    campaign.save_and_flush()

    if campaign.notify_date == date.today():
        notify_all_sales_of_store(campaign.store_id, push_msg_for_campaign_creation(campaign), type="campaign",
                                  campaign_id=campaign.id)
        campaign.notify_sent = True

    return campaign, 201, add_location_header(dict(), url_for('api.get_campaign', uid=campaign.id))


@api.route('/campaigns/<int:uid>', methods=['PUT', 'POST'])
def update_campaign(uid):
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    # do not allow to update campaign id and notify_sent directly
    data.pop('id', None)
    data.pop('notify_sent', None)

    campaign = get_campaign(uid)

    for key, value in data.iteritems():
        setattr(campaign, key, value)

    if campaign.notify_sent:
        notify_all_sales_of_store(campaign.store_id, push_msg_for_campaign_update(campaign), type="campaign",
                                  campaign_id=campaign.id)
    elif campaign.notify_date == date.today():
        # if notify_date is changed to today, send the notification right now.
        notify_all_sales_of_store(campaign.store_id, push_msg_for_campaign_creation(campaign), type="campaign",
                                  campaign_id=campaign.id)
        campaign.notify_sent = True

    return campaign


@api.route('/campaigns/<int:uid>', methods=['GET'])
def get_campaign(uid):
    result = Campaign.find(uid)

    if result is None:
        abort(404, description=gettext(u'campaign with id %(id)s is not found', id=uid))
    return result


@api.route('/stores/<int:store_id>/campaigns', methods=['GET'])
def get_all_campaigns(store_id):
    return Campaign.find_all_by_store(store_id, **get_page_info(request))


@api.route('/stores/<int:store_id>/campaigns/active', methods=['GET'])
def get_active_campaigns(store_id):
    return Campaign.find_all_active_by_store(store_id, **get_page_info(request))
