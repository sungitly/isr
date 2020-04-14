# -*- coding: utf-8 -*-
from application.controllers._helper import flash_error
from application.exceptions import JsonRequestRequired, NeedMobileException, InvalidateMobileException, UserWasNotFound, \
    UserWasNotAuthorized, RestorePasswordOverflow, RestorePasswordChecksumMissmatch, RestorePasswordInvalidToken
from application.forms.account import LoginForm, RestorePasswordForm
from application.integration.ucenter import (uc_login,
                                             uc_save_user,
                                             uc_restore_get_checksum,
                                             uc_restore_password
                                             )

from application.integration.bmw import (bmw_login,
                                         bmw_is_success,
                                         bmw_validate_user,
                                         bmw_is_redirect_ucenter,
                                         bmw_save_user)
from application.models.user import User
from application.permissions import VisitorPermission
from application.session import add_user, remove_user, remove_store_id
from application.cache import cache
from application.utils import validate_mobile

from flask import Blueprint, render_template, request, url_for, redirect, g, jsonify
from flask.ext.babel import gettext

bp = Blueprint('account', __name__, url_prefix="/account")


@bp.route('/login', methods=['GET', 'POST'])
@VisitorPermission()
def login():
    form = LoginForm()
    referer = request.form.get('referer')

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = None
        flashed = False
        try:
            login_response = uc_login(username, password) #测试使用 ucenter
            if login_response:
                user = uc_save_user(login_response)
        except UserWasNotFound:
            json_r = bmw_login(username, password) #使用原始bmw
            if bmw_is_success(json_r):
                if bmw_validate_user(json_r):
                    user = bmw_save_user(json_r)
        except UserWasNotAuthorized:
            flash_error(u'用户密码错误')
            flashed = True

        if user:
            add_user(user)
            return redirect(referer or url_for(user.dashboard_endpoint()))
        if not flashed:
            flash_error(gettext(u'login failed'))

    return render_template('account/login.html', form=form)


@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if g.user:
        user = User.find(g.user.id)
        # user.deactivate()
        remove_user()
        remove_store_id()
        cache.delete_memoized(User.get_all_sales_by_store_from_cache, user.id)

    return redirect(url_for('site.index'))


def ok_message(data=None, message=None):
    if not message:
        message = 'ok'
    return jsonify({'code': 0, 'message': message, 'data': data})


def fail_message(data=None, message=None):
    return jsonify({'code': 1, 'message': message, 'data': data})


@bp.route('/get_checksum', methods=['POST'])
def get_checksum():
    req_data = request.form

    if not req_data:
        raise JsonRequestRequired()

    if 'mobile' not in req_data:
        raise NeedMobileException()
    mobile = req_data['mobile']
    if not isinstance(mobile, (basestring, unicode)):
        raise InvalidateMobileException()

    if not validate_mobile(mobile):
        raise InvalidateMobileException()
    res = uc_restore_get_checksum(mobile)
    if not res:
        return fail_message(u"获取验证码错误")
    return ok_message(data=res.to_data())


@bp.route('/restore_password', methods=['GET', 'POST'])
def restore_password():
    form = RestorePasswordForm()
    if form.validate_on_submit():
        token = form.token.data
        if not token:
            flash_error(u'无效验证码')
        else:
            verify_code = form.verify_code.data
            new_password = form.new_password.data
            ip = request.remote_addr
            flashed = False
            try:
                if uc_restore_password(token, verify_code, new_password, 'isr', ip):
                    return redirect('/account/login')
            except (RestorePasswordInvalidToken, RestorePasswordChecksumMissmatch) as e:
                flash_error(e.message)
                flashed = True
            if not flashed:
                flash_error(gettext(u'重置密码失败'))
    return render_template('account/restore_password.html', form=form)