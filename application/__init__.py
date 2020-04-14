# -*- coding: utf-8 -*-
import os
from functools import wraps

from flask import request, g
from flask.ext.wtf import CsrfProtect

from application.controllers import order
from application.errors import ErrorHandler
from application.nutils.assets import assets
from application.nutils.url import url_for_pagination
from application.session import get_current_user, store_id_selected, from_mobile
from application.wsgi_middleware import ProxyMiddleware

csrf = CsrfProtect()


def create_app(mode=None):
    """Create Flask app."""
    from flask import Flask

    app = Flask(__name__)

    @app.before_request
    def cache_raw_http_body_for_form_submit():
        if request.content_type == 'application/x-www-form-urlencoded':
            g.raw_http_body = request.get_data(parse_form_data=False, cache=True)

    # app.wsgi_app = ProxyFix(app.wsgi_app)
    global csrf
    csrf.init_app(app)

    init_config(app, mode)
    init_bp(app, csrf)
    init_jinja(app)
    init_db(app)
    init_i18n(app)
    init_cache(app)
    init_before_request_hooks(app)
    init_errors_hooks(app)

    # init event handlers in the end
    init_event_handlers()
    init_proxy(app)

    if app.config['DEBUG']:
        print app.url_map
    return app


# Application Initialization Method Below:
def init_config(app, mode=None):
    from config import config

    mode = mode or os.environ.get('MODE', 'development')
    app.config.from_object(config[mode])
    config[mode].init_app(app)


def init_bp(app, csrf):
    from application.api import api
    from application.controllers import site, account, user, customer, appt, reception, campaign, setting, stats, ops, \
        calllog, lead, session_setting, update_permissions, inventory, mmgmt, radar

    app.register_blueprint(api)
    csrf.exempt(api)

    app.register_blueprint(site.bp)
    app.register_blueprint(account.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(customer.bp)
    app.register_blueprint(appt.bp)
    app.register_blueprint(reception.bp)
    app.register_blueprint(campaign.bp)
    app.register_blueprint(order.bp)
    app.register_blueprint(setting.bp)
    app.register_blueprint(stats.bp)
    app.register_blueprint(ops.bp)
    app.register_blueprint(calllog.bp)
    app.register_blueprint(lead.bp)
    app.register_blueprint(inventory.bp)
    app.register_blueprint(mmgmt.bp)
    app.register_blueprint(radar.bp)

    csrf.exempt(update_permissions.bp)
    app.register_blueprint(update_permissions.bp)

    csrf.exempt(session_setting.bp)
    app.register_blueprint(session_setting.bp)


def init_db(app):
    from application.models.base import db

    db.init_app(app)

    def auto_commit(target_function):
        @wraps(target_function)
        def wrapper(*args, **kwargs):
            rv = target_function(*args, **kwargs)
            db.session.commit()
            return rv

        return wrapper

    app.dispatch_request = auto_commit(app.dispatch_request)


def init_i18n(app):
    from flask.ext.babel import Babel

    babel = Babel(app)
    babel.init_app(app)


def init_cache(app):
    from application.cache import cache

    cache.init_app(app)


def init_event_handlers():
    import handlers


def init_before_request_hooks(app):
    # TODO: move api blueprint before request hook here

    @app.before_request
    def populate_user():
        from application.api import api
        if api.url_prefix not in request.path:
            g.user = get_current_user()


def init_errors_hooks(app):
    if app.debug:
        return
    else:
        import errors

        error_handler = ErrorHandler(app)
        error_handler.init_app(app)


def init_jinja(app):
    @app.context_processor
    def inject_vars():
        if g and hasattr(g, 'user'):
            return dict(current_user=g.user)
        else:
            return dict()

    import filters
    app.jinja_env.filters.update({
        'date_str': filters.date_str,
        'datetime_str': filters.datetime_str,
        'time_str': filters.time_str,
        'gender_str': filters.gender_str,
        'lookup_str': filters.lookup_str,
        'multi_lookup_str': filters.multi_lookup_str,
        'customer_status_str': filters.customer_status_str,
        'customer_status_css': filters.customer_status_css,
        'timedelta_str': filters.human_readable_timedelta,
        'timedelta_str_in_min': filters.timedelta_in_minutes,
        'timedelta_till_now_str': filters.human_readable_timedelta_until_now,
        'weekly_str': filters.weekly_str,
        'none_str': filters.none_str,
        'appt_status_str': filters.appt_status_str,
        'appt_status_css': filters.appt_status_css,
        'appt_type_str': filters.appt_type_str,
        'rx_type_str': filters.rx_type_str,
        'rx_status_str': filters.rx_status_str,
        'radar_status_css': filters.radar_status_css,
        'radar_status_str': filters.radar_status_str,
        'bool_str': filters.bool_str,
        'cond_return_value': filters.cond_return_value
    })

    app.jinja_env.globals.update({
        'url_for_pagination': url_for_pagination,
        'assets': assets,
        'store_id_selected': store_id_selected,
        'from_mobile': from_mobile
    })


def init_proxy(app):
    ucenter_url = app.config['UCENTER_AUTH_SERVER_URL']
    app.wsgi_app = ProxyMiddleware(app.wsgi_app, app.config['UCENTER_AUTH_TOKEN_KEY'],
                                   {(
                                        'POST',
                                        '/api/restore_get_checksum'): ucenter_url + '/api_1_0/restore_get_checksum',
                                    ('POST', '/api/restore_password'): ucenter_url + '/api_1_0/restore_password'})
