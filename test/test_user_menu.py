# -*- coding: utf-8 -*-
from unittest import TestCase


class TestUserMenu(TestCase):
    def test_user_menu_with_manager_role(self):
        from application.models.user import User, _role_to_endpoint_menu

        menu = User._get_menu_items(['manager'])

        manager_menu = [m for m in _role_to_endpoint_menu if m.role == 'manager']
        assert menu == manager_menu[0].menu

    def test_user_menu_with_manager_stockman_roles(self):
        from application.models.user import User, _role_to_endpoint_menu

        menu = User._get_menu_items(['manager', 'stockman'])
        manager_menu = [m for m in _role_to_endpoint_menu if m.role == 'manager']
        stockman_menu = [m for m in _role_to_endpoint_menu if m.role == 'stockman']

        # assert all manger menu is included
        assert all([m in menu for m in manager_menu[0].menu])

        # assert all stockman menu is included
        from application.nutils.menu import L2_SETTINGS
        assert all([m in menu for m in stockman_menu[0].menu if m != L2_SETTINGS])

        # assert setting menu is the last item
        from application.nutils.menu import L1_SETTINGS
        assert L1_SETTINGS == menu[-1]
