# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import StringField, PasswordField, HiddenField
from wtforms.validators import DataRequired, length, EqualTo

from .validaters import PhonenumberRequired


class LoginForm(Form):
    username = StringField(u'账户', validators=[DataRequired(u'账户不能为空')])
    password = PasswordField(u'密码', validators=[DataRequired(u'密码不能为空')])


class ResetPasswordForm(Form):
    original_password = PasswordField(u'当前密码', description=u'当前密码',
                                      validators=[DataRequired(u'当前密码不能为空'), length(min=6, message=u'密码必须大于六位')])
    new_password = PasswordField(u'新密码', description=u'新密码',
                                 validators=[DataRequired(u'新密码不能为空'), length(min=6, message=u'密码必须大于六位')])
    confirm_password = PasswordField(u'确认密码', description=u'确认密码',
                                     validators=[DataRequired(u'确认密码不能为空'), length(min=6, message=u'密码必须大于六位'),
                                                 EqualTo('new_password', message=u'两次输入密码不一致')])


class RestorePasswordForm(Form):
    '''
    找回密码
    '''
    token = HiddenField(u'Token', description=u'验证token')
    mobile = StringField(u'手机号', description=u'注册手机号',
                         validators=[DataRequired(u'当前手机号码不能为空'), PhonenumberRequired()])
    verify_code = StringField(u'验证码', description=u'手机验证码', validators=[DataRequired(u'验证码不能为空')])
    new_password = PasswordField(u'新密码', description=u'新密码',
                                 validators=[DataRequired(u'新密码不能为空'), length(min=6, message=u'密码必须大于六位')])
    confirm_password = PasswordField(u'确认密码', description=u'确认密码',
                                     validators=[DataRequired(u'确认密码不能为空'), length(min=6, message=u'密码必须大于六位'),
                                                 EqualTo('new_password', message=u'两次输入密码不一致')])