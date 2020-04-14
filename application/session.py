# -*- coding: utf-8 -*-
from flask import session, g, request

from application.auth import hmac_auth
from application.auth import jwt_auth
from application.models.store import INVALID_STORE_ID
from application.models.user import User


def add_user(user, permenent=True):
    """Sign in user."""
    session.permanent = permenent
    session['user_id'] = user.id
    g.user = user


def remove_user():
    """Sign out user."""
    session.pop('user_id', None)


def get_current_user():
    """Get current user."""
    if 'user_id' in session:
        user = User.get_user_by_id_from_cache(session['user_id'])
    else:
        # FIXME: wft. will be replaced by access token auth.
        try:
            if not hmac_auth(request):
                return None
        except:
            return None

        try:
            if not jwt_auth(request):
                return None
        except Exception, e:
            return None

        user = g.user
        current_store = request.headers.get('X-Current-Store', None)
        if current_store:
            set_store_id(current_store)

        g.from_mobile = True

    if not user or not user.is_active():
        remove_user()
        return None
    return user


def remove_store_id():
    session.pop('store_id', None)


def set_store_id(store_id):
    session['store_id'] = store_id


def get_or_set_store_id():
    session_store_id = session.get('store_id')
    if session_store_id:
        return session_store_id
    if g.user:
        default_store_id = g.user.get_default_store_id()
        if default_store_id:
            set_store_id(default_store_id)
            return default_store_id
    return INVALID_STORE_ID


def store_id_selected(value):
    return unicode(get_or_set_store_id()) == unicode(value)


def from_mobile():
    return hasattr(g, 'from_mobile') and g.from_mobile
