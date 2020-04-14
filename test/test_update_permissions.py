#coding: utf-8
from base import BaseTestCase
import requests_mock
from application.integration.ucenter import auth_api_get_user_infos, get_ucenter_url


class TestUpdatePermissions(BaseTestCase):
    def test_update_permissions(self):
        ucenter_url = 'http://127.0.0.1'
        self.app.config['AUTH_SERVER_URL'] = ucenter_url

        def mock_ucenter_url(m):
            json_res = [{
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
            }]
            with self.app.app_context():
                url_get_user_infos = get_ucenter_url(auth_api_get_user_infos)
            m.get(url_get_user_infos, json={'error':'ok', 'message':json_res})

        with requests_mock.mock() as m:
            mock_ucenter_url(m)
            url = '/update_permissions/'
            res = self.client.post(url, headers={'Content-Type': 'application/json'}, data='[1]')





