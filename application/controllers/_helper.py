# -*- coding: utf-8 -*-
from flask import flash


def flash_error(message):
    flash(message, 'alert-danger')


def flash_success(message):
    flash(message, 'alert-success')


def flash_info(message):
    flash(message, 'alert-info')
