# -*- coding: utf-8 -*-
import requests
from flask import request, current_app, g
from flask.ext.babel import gettext
from werkzeug.exceptions import abort

from application.api import api
from application.events import new_receptionist_joined, sales_logout, receptionist_logout
from application.events import new_sales_joined
from application.exceptions import UserWasNotFound
from application.integration.bmw import (bmw_login,
                                         bmw_is_success,
                                         bmw_save_user)
from application.integration.ucenter import (uc_login,
                                             uc_save_user,
                                             uc_change_password)
from application.models.appmeta import AppMeta, ReleaseHistory
from application.models.setting import StoreSetting
from application.models.user import User

auth_api = '/j/rlogin/'
security_api = '/j/changepass'


@api.route('/login', methods=['POST'])
def login():
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    username = data.get('username', None)
    password = data.get('password', None)

    if username is None or password is None:
        abort(400, description=gettext('Authentication Failed'))

    user = None
    login_response = uc_login(username, password)  # 测试使用 ucenter
    try:
        if login_response:
            user = uc_save_user(login_response)
    except UserWasNotFound:
        json_r = bmw_login(username, password)  # 使用原始bmw
        if not json_r:
            abort(500)
        if bmw_is_success(json_r):
            user = bmw_save_user(json_r)
        if json_r['status'] != 0:
            abort(400, description=json_r['message'])

    if not user:
        raise UserWasNotFound()

    if user.is_sales():
        new_sales_joined.send(sales=user)
    elif user.is_receptionist():
        new_receptionist_joined.send(receptionist=user)

    # hack to easy client development
    user.status = ''

    return user


@api.route('/logout', methods=['POST'])
def logout():
    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    user_id = data['user_id']

    if user_id is None:
        abort(400, description=gettext('user_id can not be emtpy'))

    user = User.find(user_id)

    if user:
        # user.deactivate()
        if user.is_sales():
            sales_logout.send(sales=user)
        elif user.is_receptionist():
            receptionist_logout.send(receptionist=user)

    return user


@api.route('/security', methods=['POST', 'PUT'])
def change_password():
    """
    data json sample:
    {
        "user_id": 1,
        "old_password": "old_password",
        "new_password": "new_password"
    }

    :return: user
    """

    data = request.json
    if data is None:
        abort(400, description=gettext('invalid json request'))

    user_id = data.get('user_id', None)
    try:
        if user_id:
            user_id = long(user_id)
            data['user_id'] = user_id
    except:
        user_id = None

    if not user_id or not g.user:
        abort(400, description='Not found user in request')

    if g.user.id != user_id:
        abort(400, description='Cant change other user password')

    if g.user.system == 'bmw':
        r = requests.post(current_app.config['AUTH_SERVER_URL'] + security_api, json=data)
        json_data = r.json()
        if json_data['status'] != 0:
            abort(401, description=json_data['message'])
    else:
        user_id = data['user_id']
        old_password = data['old_password']
        new_password = data['new_password']
        r = uc_change_password(user_id, old_password, new_password)
        if not r:
            abort(401, description='changepassword failed')
    return g.user  # 兼容以前的


@api.route('/apps/<name>', methods=['GET'])
def get_app_info_by_name(name):
    app_info = AppMeta.find_by_name(name)
    app_info.version_number = app_info.version_num

    return app_info


@api.route('/apps', methods=['GET'])
def get_all_app():
    return AppMeta.find_all()


@api.route('/apps/<app_name>/upgrade', methods=['POST'])
def update_app(app_name):
    app = AppMeta.find_by_name(app_name)

    if not app:
        abort(404, description=u'App not found')

    upgrade_info = request.json

    if not upgrade_info or not upgrade_info.get('version', None) or not upgrade_info.get('version_num', None):
        abort(400, description=gettext('Upgrade info not provided'))

    version = upgrade_info.get('version', None)
    version_num = upgrade_info.get('version_num', None)
    release_note = upgrade_info.get('release_note', None)

    if long(version_num) <= long(app.version_num):
        abort(400, description=gettext('version_num must be greater than current'))

    app.upgrade(version, version_num, release_note)
    return app


@api.route('/apps/<app_name>/release', methods=['GET'])
def get_release(app_name):
    return ReleaseHistory.find_all_by_app_name(app_name)


@api.route('/stores/<int:store_id>/settings')
def get_store_settings(store_id):
    return StoreSetting.find_all_by_store_wo_page(store_id)
