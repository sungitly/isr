# coding: utf-8
import json
import time

from base import BaseTestCase


class TestDB(BaseTestCase):
    def test_user(self):
        def test():
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

            user_data = json_login['user']
            user = User(username=user_data['username'])
            db.session.add(user)

            for p in json_login['store_user_role_scopes']:
                user.update_permission(p)

            # self.assertEqual(set(user.role_titles), set(['role_test', 'role_admin']))

            users = User.find_all_sales_by_store(2)
            self.assertEqual(users[0].username, 'gujd')

            sales = User.find_all_by_sales_name('gujd')
            self.assertEqual(sales[0].username, 'gujd')

            self.assertEqual(users[0].stores, '1')

        self.run_in_appcontext(test)
        # self.run_in_appcontext(test)

    def test_insert_frt_inventory(self):
        def insert_frt_inventory():
            inv_json_str = """
                [{
                  "BRAND_CODE": "1201",
                  "BRAND_NAME": "路虎",
                  "CLASS_CODE": "120102",
                  "CLASS_NAME": "Discovery [发现]",
                  "CARTYPE_CODE": "120102003",
                  "CARTYPE": "Discovery4 [发现4]",
                  "SUBTYPE_CODE": "1201020030080",
                  "SUBTYPE_NAME": "2015款 3.0T 手自一体 V6 SC HSE(2015)欧5",
                  "COLOR_NAME": "圣托里尼黑",
                  "COLOR_ATTRIBUTE": "车身色",
                  "WAVEHOUSE_NAME": "本店仓库",
                  "LOCATION_NAME": "1",
                  "OUT_FACTORY_DATE": "0001-01-01T00:00:00",
                  "VIN": "SALAN2V66FA765367",
                  "INV_STATUS": "销售出库",
                  "INVDAY": 190.0,
                  "IN_PRICE": 878687.98,
                  "MRSP": 928000.0,
                  "REBATE_AMT": null
                },
                {
                  "BRAND_CODE": "1201",
                  "BRAND_NAME": "路虎",
                  "CLASS_CODE": "120102",
                  "CLASS_NAME": "Discovery [发现]",
                  "CARTYPE_CODE": "120102003",
                  "CARTYPE": "Discovery4 [发现4]",
                  "SUBTYPE_CODE": "1201020030078",
                  "SUBTYPE_NAME": "2015款 3.0T 手自一体 SDV6 HSE(2015)欧5",
                  "COLOR_NAME": "圣托里尼黑",
                  "COLOR_ATTRIBUTE": "车身色",
                  "WAVEHOUSE_NAME": "本店仓库",
                  "LOCATION_NAME": "1",
                  "OUT_FACTORY_DATE": "0001-01-01T00:00:00",
                  "VIN": "SALAN2F6XFA762485",
                  "INV_STATUS": "销售出库",
                  "INVDAY": 214.0,
                  "IN_PRICE": 841487.99,
                  "MRSP": 888000.0,
                  "REBATE_AMT": null
                }]
            """

            json_data = json.loads(inv_json_str)
            from application.models.frtinv import FrtInventory

            sync_timestamp = int(time.time())

            for item in json_data:
                inv = FrtInventory.from_data(item)
                inv.sync_timestamp = sync_timestamp
                inv.save()

            saved_data = FrtInventory.find_all_by_sync_timestamp(sync_timestamp)
            self.assertEqual(len(json_data), len(saved_data))

        self.run_in_appcontext(insert_frt_inventory)
