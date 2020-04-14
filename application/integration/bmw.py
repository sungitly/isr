# -*- coding: utf-8 -*-
import json

from application.models.user import User
from flask import current_app
import requests

auth_api = '/j/rlogin/'
security_api = '/j/changepass'


# noinspection PyBroadException
def bmw_login(account, password):
    params = dict()
    params['email'] = account.strip() if account else ''
    params['password'] = password

    try:
        r = requests.post(current_app.config['AUTH_SERVER_URL'] + auth_api, data=params)
        if r and r.json():
            return r.json()
    except:
        pass


def bmw_change_password(user_id, old_password, new_password):
    data = {'user_id': user_id, 'old_password': old_password, 'new_password': new_password}
    r = requests.post(current_app.config['AUTH_SERVER_URL'] + security_api, json=data)
    return r.json()


def bmw_save_user(bmw_user_json):
    result = bmw_user_json['content']
    user = User.find(result['id'])
    if user is None:
        user = User()
    user.from_auth(result)
    user.save()
    return user


def get_user_type(bmw_user_json):
    if bmw_user_json and bmw_user_json['content']:
        return bmw_user_json['content'].get('user_type')
    else:
        return -1


def bmw_validate_user(bmw_user_json):
    if bmw_user_json and bmw_user_json['content']:
        user_type = bmw_user_json['content'].get('user_type')
        roles = bmw_user_json['content'].get('roles')

        return user_type in (6, 101, 7) or (roles and 'manager' in roles)
    else:
        return False


def bmw_is_success(json_data):
    if not json_data:
        return False
    if not isinstance(json_data, dict):
        return False
    return json_data.get('status', 1) == 0


def bmw_is_redirect_ucenter(json_data):
    if not json_data:
        return False
    if not isinstance(json_data, dict):
        return False
    if 'status' not in json_data or json_data['status'] != 1:
        return False
    if 'message' not in json_data:
        return False
    return json_data['message'] == 'need change to ucenter'