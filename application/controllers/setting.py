# -*- coding: utf-8 -*-
import datetime

from application.controllers._helper import flash_error, flash_success
from application.forms.account import ResetPasswordForm
from application.forms.setting import TAForm
from application.integration.ucenter import uc_change_password
from application.integration.bmw import bmw_change_password
from application.models.setting import TaSetting
from application.nutils.menu import MODIFY_PASSWORD, TARGET_SETTINGS
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from dateutil.parser import parse
from flask import Blueprint, render_template, g, request, redirect, url_for

bp = Blueprint('settings', __name__, url_prefix="/settings")


@bp.route('/security', methods=['GET', 'POST'])
@UserPermission()
def modify_password():
    form = ResetPasswordForm()

    if form.validate_on_submit():
        if form.new_password.data != form.confirm_password.data:
            flash_error(u'两次输入密码不一致')
        else:
            success = False
            error_msg = u'非常抱歉服务器出错了, 请稍后重试或者联系系统管理员.'
            if g.user.system == 'ucenter':
                try:
                    success = uc_change_password(g.user.id, form.original_password.data, form.new_password.data)
                except Exception as e:
                    if hasattr(e, 'message'):
                        error_msg = e.message
            else:
                result = bmw_change_password(g.user.id, form.original_password.data, form.new_password.data)
                if isinstance(result, dict):
                    if 'status' in result and result['status'] == 0:
                        success = True
                    if 'message' in result:
                        error_msg = result['message']
            if success:
                flash_success(u'密码修改成功')
            else:
                flash_error(error_msg)
    return render_template('settings/security.html', selected_menu=MODIFY_PASSWORD, form=form)


@bp.route('/ta', methods=['GET', 'POST'])
@UserPermission()
def set_target():
    store_id = get_or_set_store_id()
    current_year = datetime.datetime.now().isocalendar()[0]
    monthly_form = TAForm(prefix='monthly')
    monthly_form.type.data = 'monthly'

    weekly_form = TAForm(prefix='weekly')
    weekly_form.type.data = 'weekly'

    if monthly_form.validate_on_submit():
        setting_date = parse(monthly_form.date.data)
        year = setting_date.year
        month = setting_date.month

        existing_ta_settings = TaSetting.find_all_active_monthly_ta(year, month, store_id)
        for setting in existing_ta_settings:
            setting.is_deleted = 1

        ta_setting = TaSetting(type='monthly', year=year, month=month, value=monthly_form.ta.data, store_id=store_id)
        ta_setting.save()

        monthly_form.date.data = ''
        monthly_form.ta.data = ''
        return redirect(url_for('settings.set_target'))

    if weekly_form.validate_on_submit():
        setting_date = parse(weekly_form.date.data)
        year = setting_date.year
        week = setting_date.isocalendar()[1]

        existing_ta_settings = TaSetting.find_all_active_weekly_ta(year, week, store_id)
        for setting in existing_ta_settings:
            setting.is_deleted = 1

        ta_setting = TaSetting(type='weekly', year=year, week=week, value=weekly_form.ta.data, store_id=store_id)
        ta_setting.save()

        weekly_form.date.data = ''
        weekly_form.ta.data = ''
        return redirect(url_for('settings.set_target'))

    monthly_ta_settings = TaSetting.find_all_active_by_type_and_store('monthly', store_id)
    weekly_ta_settings = TaSetting.find_all_active_by_type_and_store('weekly', store_id)

    return render_template('settings/ta.html', selected_menu=TARGET_SETTINGS, monthly_form=monthly_form,
                           weekly_form=weekly_form, current_year=current_year, monthly_ta_settings=monthly_ta_settings,
                           weekly_ta_settings=weekly_ta_settings, back_endpoint=request.args.get('back_endpoint', None))
