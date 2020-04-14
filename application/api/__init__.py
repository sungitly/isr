# -*- coding: utf-8 -*-
from application import get_current_user
from application.auth import hmac_auth, jwt_auth
from application.decorators import render_json_response

from flask import Blueprint, request, current_app, session, g
from werkzeug.exceptions import abort


class ApiBlueprint(Blueprint):
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        super(ApiBlueprint, self).add_url_rule(rule, endpoint, render_json_response(view_func),
                                               **options)


api = ApiBlueprint('api', __name__, url_prefix='/api')

from . import sales_api, reception_api, appointment_api, order_api, lookup_api, auth_api, devices_api, customer_api, \
    campaign_api, jobs_api, external_api, ops_api, inventory_api, insurance_api, tools_api, radar


# noinspection PyBroadException
@api.before_request
def auth_request():
    if 'user_id' in session:
        g.user = get_current_user()
        return

    try:
        if not hmac_auth(request):
            abort(401)
    except:
        if not current_app.config['DEBUG']:
            abort(401)

    try:
        if not jwt_auth(request):
            current_app.logger.warning('no jwt header access: %s' % (request.full_path))
            # disable jwt_auth temporarily. For third party access, jwt auth is not necessary.
            # abort(401)
    except Exception, e:
        current_app.logger.warning('jwt exception found: %s' % (e.message))
        # abort(401)
