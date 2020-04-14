# -*- coding: utf-8 -*-
import urlparse
import requests

from flask import current_app
from application.exceptions import  (UCenterConnectExcetion,
                                     UserPasswordInvalid, InvalidateMobileException, RestorePasswordOverflow,
                                     RestorePasswordInvalidToken, RestorePasswordChecksumMissmatch,
                                     UCenderConnectYunpianException, UCIntegrationNotFound)
from application.models.user import User
from application.exceptions import UserWasNotAuthorized, UserWasNotFound
from application.constants import *
from application.redisstore import redis_store
from params import *

api_base_url = '/api_1_0/'

# 登录相关
auth_api_login = api_base_url + 'user_login'
auth_api_changepassword = api_base_url + 'user_changepassword'
auth_api_get_user_infos = api_base_url + 'user_infos'

# 重置密码相关
restore_api_get_checksum = api_base_url + 'restore_get_checksum'
restore_api_restore_password = api_base_url + 'restore_password'


#集成相关
integration_api_gen_token = api_base_url + 'integration/gen_token'
integration_api_get_info = api_base_url + 'integration/get_info'


def get_ucenter_url(sub_url, params=None):
    base_url = current_app.config['UCENTER_AUTH_SERVER_URL']
    full_url = urlparse.urljoin(base_url, sub_url)
    if params:
        full_url += '?' + params
    return full_url


def uc_validate_json_res(data):
    for item in ('data', 'error', 'message'):
        if item not in data:
            return False
    return True


def uc_validate_success_res(data):
    return data['error'] == 0


def _ucenter_request(method, url=None, data=None, json=None, **kwargs):
    if method not in ['get', 'post']:
        return
    token = current_app.config['UCENTER_AUTH_TOKEN_KEY']
    try:
        if method == 'get':
            res = requests.get(url, auth=(token, ''), **kwargs)
        else:
            res = requests.post(url, data=data, json=json, auth=(token, ''), **kwargs)
    except Exception as e:
        raise UCenterConnectExcetion()
    data = res.json()
    if not data:
        raise UCenterConnectExcetion()
    if not uc_validate_json_res(data):
        raise UCenterConnectExcetion()

    error = data['error']

    if error == 0:
        return data

    error_2_exception_map = {
        UC_APIUNAUTHORIZED: UCenterConnectExcetion,
        UC_USERPASSWORDINVALID: UserPasswordInvalid,
        UC_USERNOTFOUND: UserWasNotFound,
        UC_USERUNAUTHORIZED: UserWasNotAuthorized,
        UC_WRONGPHONENUMBER: InvalidateMobileException,
        UC_RESTOREPASSWORDDAYOVERFLOW: RestorePasswordOverflow,
        UC_RESTOREPASSWORDWEEKOVERFLOW: RestorePasswordOverflow,
        UC_RESTOREPASSWORDINVALIDATETOKEN: RestorePasswordInvalidToken,
        UC_RESTOREPASSWORDCHECKSUMMISMATCH: RestorePasswordChecksumMissmatch,
        UC_SENDRESETPASSWORDCHECKSUMEXCEPTION: RestorePasswordChecksumMissmatch,
        UC_AUTHPARAMEXCEPTION: UCenderConnectYunpianException,
        UC_INTEGRATIONNOTFOUND: UCIntegrationNotFound,

    }

    message = data.get('message', None)
    if error in error_2_exception_map:
        raise error_2_exception_map[error](message)

    return data


################## 重置密码 ################


def uc_restore_get_checksum(mobile):
    req_get_checksum = RestoreGetChecksumRequest(mobile)
    data = _ucenter_request('post', get_ucenter_url(restore_api_get_checksum), json=req_get_checksum.to_data())
    res_get_checksum = RestoreGetChecksumResponse.from_data(data['data'])
    return res_get_checksum


def uc_restore_password(token, checksum, password, device, ip, extra_datas=None):
    req_restore_password = RestorePasswordRequest(token, checksum, password, device , ip, extra_datas)
    data = _ucenter_request('post', get_ucenter_url(restore_api_restore_password), json=req_restore_password.to_data())
    return True


############### 用户登录 ################
# noinspection PyBroadException
def uc_login(account, password):
    req_login = AuthLoginRequest(account, password)
    data = _ucenter_request('post', get_ucenter_url(auth_api_login), json=req_login.to_data())
    login_res = AuthLoginResponse.from_data(data['data'])
    return login_res


def uc_change_password(user_id, old_password, new_password):
    req_change_password = AuthChangePasswordRequest(user_id, old_password, new_password)
    data = _ucenter_request('post', get_ucenter_url(auth_api_changepassword), json=req_change_password.to_data())
    return uc_validate_success_res(data)


def uc_get_user_infos(user_ids):
    req_user_infos = AuthUserInfosRequest(user_ids)
    data = _ucenter_request('get', get_ucenter_url(auth_api_get_user_infos, req_user_infos.to_param()))
    user_info_res = AuthUserInfoResponse.from_data(data['data'])
    return user_info_res


def uc_save_user(login_res):
    return User.from_ucenter(login_res)


def uc_integration_get_token(client_name, **kwargs):
    req_data = {
        'client_name': client_name
    }
    req_data.update(kwargs)
    data = _ucenter_request('post', get_ucenter_url(integration_api_gen_token), json=req_data)
    return data['data']

if __name__ == '__main__':
    from flask import Flask
    import requests_mock
    app = Flask(__name__)

    base_url = 'http://127.0.0.1:5002/'

    def mock_login(m):
        url = get_ucenter_url(auth_api_login)
        res = {
            'json': {'error': '0',
                     'message': None,
                     'data': {'user': {'id': 1, 'username': 'gujd', 'last_login_on': '2012-2-3'},
                                 'store_user_role_scopes': []}}
        }
        m.post(url, **res)

    def mock_change_password(m):
        url = get_ucenter_url(auth_api_changepassword)
        res = {
            'json': {'error': '0',
                     'data': None,
                     'message': 'change_password_ok'}
        }
        m.post(url, **res)

    def mock_get_user_infos(m):
        url = get_ucenter_url(auth_api_get_user_infos)
        res = {
            'json': {'error': '0',
                     'message': None,
                     'data': [{'user': {'id': 1, 'username': 'gujd', 'last_login_on': '2012-2-3'},
                                        'store_user_role_scopes': []},
                                 {'user': {'id': 2, 'username': 'abc', 'last_login_on': '2013-2-3'},
                                        'store_user_role_scopes': []}]}
        }
        m.get(url, **res)

    class Config:
        AUTH_UCENTER_TOKEN_KEY = 'xxx'
        UCENTER_AUTH_SERVER_URL = base_url

    app.config.from_object(Config())
    with app.app_context():
        with requests_mock.mock() as m:
            mock_login(m)
            res = uc_login('gujd', '1')
            print res

            mock_change_password(m)
            res = uc_change_password(1, '1', '2')
            print res

            mock_get_user_infos(m)
            res = uc_get_user_infos([1,2,1])
            print res

    print 'ok'