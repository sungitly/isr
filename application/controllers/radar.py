# coding: utf-8
from flask import Blueprint, render_template, g, request, redirect, url_for

from application.nutils.menu import L2_RADAR_TENDENCY, L2_RADAR_STRUCTURE, L2_RADAR_MULTI

bp = Blueprint('radar', __name__, url_prefix="/manager/radar/")


@bp.route('tendency')
def tendency():
    return render_template('radar/tendency.html', selected_menu=L2_RADAR_TENDENCY)


@bp.route('structure')
def structure():
    return render_template('radar/structure.html', selected_menu=L2_RADAR_STRUCTURE)


@bp.route('multi')
def multi():
    return render_template('radar/multi.html', selected_menu=L2_RADAR_MULTI)
