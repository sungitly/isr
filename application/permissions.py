# -*- coding: utf-8 -*-
import re
from flask import session, redirect, url_for, g, request
from permission import Rule, Permission
from .models.user import (USER_ROLE_STORE_MANAGER,
                          USER_ROLE_STORE_SALES,
                          USER_ROLE_STORE_OPS, USER_ROLE_STORE_STOCKMAN)

"""
The permission stuff has to be rewrite because the current implementation is not quite appropriate.
"""

RE_CUSTOMER_DETAILS_URL = '^\/customers\/[0-9]+$'


class VisitorRule(Rule):
    def check(self):
        return 'user_id' not in session

    def deny(self):
        return redirect(url_for('site.index'))


class UserRule(Rule):
    def check(self):
        user = g.user

        path = request.path

        if user and path:
            role_titles = user.role_titles
            if USER_ROLE_STORE_OPS in role_titles or USER_ROLE_STORE_MANAGER in role_titles:
                return True
            if USER_ROLE_STORE_SALES in role_titles:
                return (
                    path in ('/customers/', '/settings/security', '/account/login', '/account/logout', '/') or re.match(
                        RE_CUSTOMER_DETAILS_URL, path))
            if USER_ROLE_STORE_STOCKMAN in role_titles:
                return path in ('/settings/security', '/account/login', '/account/logout', '/')
            return False
        else:
            return False

    def deny(self):
        return redirect(url_for('account.login'))


class ManagerRule(Rule):
    def check(self):
        user = g.user
        if user:
            role_titles = user.role_titles
            return USER_ROLE_STORE_OPS in role_titles or USER_ROLE_STORE_MANAGER in role_titles
        else:
            return False

    def deny(self):
        return redirect(url_for('account.login'))


class OpsRule(Rule):
    def check(self):
        user = g.user
        if not user:
            return False
        role_titles = user.role_titles
        return USER_ROLE_STORE_OPS in role_titles

    def deny(self):
        return redirect(url_for('account.login'))


class StockRule(Rule):
    def check(self):
        user = g.user
        if not user:
            return False
        return USER_ROLE_STORE_STOCKMAN in user.role_titles

    def deny(self):
        return redirect(url_for('account.login'))


class VisitorPermission(Permission):
    def rule(self):
        return VisitorRule()


class UserPermission(Permission):
    def rule(self):
        return UserRule()


class OpsPermission(Permission):
    def rule(self):
        return OpsRule()


class StockPermission(Permission):
    def rule(self):
        return StockRule()


class ManagerPermission(Permission):
    def rule(self):
        return ManagerRule()
