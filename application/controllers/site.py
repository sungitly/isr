# -*- coding: utf-8 -*-
from flask import Blueprint, redirect, url_for, g

bp = Blueprint('site', __name__)


@bp.route('/')
def index():
    if g.user:
        return redirect(url_for(g.user.dashboard_endpoint()))
    else:
        return redirect(url_for('account.login'))
