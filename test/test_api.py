# coding: utf-8
import json

from flask import url_for

from base import BaseTestCase

from application.models.base import db
from application.models.user import User
from application.models.role import Role
from application.models.store import Store
from application.api import api


def create_user(data):
    user_data = data['user']
    user = User(username=user_data['username'])
    db.session.add(user)

    for p in data['store_user_role_scopes']:
        user.update_permission(p)
    db.session.commit()


class TestAPI(BaseTestCase):
    rebuild_db = False

    def test_insurance(self):
        from application.integration.ucenter import get_ucenter_url, integration_api_gen_token

        del self.app.before_request_funcs['api']
        url = '/api/insurance/gen_token/1'
        with self.app.app_context():
            ucenter_url = get_ucenter_url(integration_api_gen_token)

        import requests_mock
        with requests_mock.mock() as m:
            mock_res = {
                'error': 0,
                'message': '',
                'data': {
                    'token': '123123',
                    'expires_in': 120
                }
            }
            m.post(ucenter_url, json=mock_res)
            res1 = self.client.get(url)
            print res1

    def test_user_login(self):

        del self.app.before_request_funcs['api']

        json_login = {
                'user': {
                    'username': 'gujd',
                    'id': 1
                },
                'store_user_role_scopes': [
                    {
                        'store': {'id': 1, 'sequence_id': 'seq_1', 'name': 'store_1'},
                        'role': {'title': 'manager'},
                        'scope_type': 'individual',
                        'user_ids': '1,2,3'
                    },
                    {
                        'store': {'id': 2, 'sequence_id': 'seq_2', 'name': 'store_2'},
                        'role': {'title': 'sales'},
                        'scope_type': 'peoples',
                        'user_ids': '1,2,3'
                    },
                    {
                        'store': {'id': 2, 'sequence_id': 'seq_2', 'name': 'store_2'},
                        'role': {'title': 'ops'},
                        'scope_type': 'peoples',
                        'user_ids': '1,2,3'
                    },
                    {
                        'store': {'id': 2, 'sequence_id': 'seq_2', 'name': 'store_2'},
                        'role': {'title': 'reception'},
                        'scope_type': 'peoples',
                        'user_ids': '1,2,3'
                    }]
            }
        self.run_in_appcontext(lambda : create_user(json_login))

        url = '/api/login'

        headers = {
            'Content-Type': 'application/json'
        }
        data = {
            'username': '18613818077',
            'password': '818077'
        }


        rv = self.client.post(url, headers=headers, data=json.dumps(data))
        print rv
