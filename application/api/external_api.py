# -*- coding: utf-8 -*-
from datetime import date, timedelta

from flask import request, url_for
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.api import api
from application.cache import cache
from application.integration.params import AuthLoginResponse
from application.integration.ucenter import uc_get_user_infos, uc_save_user
from application.models.campaign import Campaign
from application.models.user import User
from application.utils import add_location_header


@api.route('/external/campaigns', methods=['POST'])
def sync_campaigns():
    # if not hasattr(request, 'source'):
    #     abort(401)

    try:
        data = request.json
        if not data:
            abort(400, description=gettext('invalid json request'))
    except:
        abort(400, description=gettext('invalid json request'))

    campaign = Campaign(**data)
    # campaign.source = request.source
    # default notify_date to tomorrow
    campaign.notify_date = date.today() + timedelta(days=1)

    campaign.save_and_flush()

    return campaign, 201, add_location_header(dict(), url_for('api.get_campaign', uid=campaign.id))


@api.route('/external/events', methods=['POST'])
def on_events():
    event = None

    try:
        event = request.json
        if not event or not event.get('type', None):
            abort(400, description=gettext('invalid json request'))
    except:
        abort(400, description=gettext('invalid json request'))

    event_type = event.get('type')
    if 'user_update' == event_type:
        event_data = event.get('data', None)
        if event_data and event_data.get('id'):
            user_id = event_data.get('id')
            users = uc_get_user_infos([user_id]).to_data()
            if users and len(users) > 0:
                user = uc_save_user(AuthLoginResponse.from_data(users[0]))
                # invalid cache
                if user.is_sales():
                    cache.delete_memoized(User.get_all_sales_by_store_from_cache, long(user.store_id))
                elif user.is_receptionist():
                    cache.delete_memoized(User.get_all_receptionist_by_store_from_cache, long(user.store_id))
                return user

    return dict()
