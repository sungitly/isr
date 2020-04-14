# -*- coding: utf-8 -*-
import json

from application.models.stats import get_weekly_store_stats_between_dates, get_sales_stats, \
    get_unordered_customers_count_by_intent_level, get_car_stats_between_dates_in_stores, get_order_cycle_stats
from application.nutils.menu import SR_TCR, SR_CR, SP_FR, SP_ACR, SP_TDR, SM_SC, SM_UOC, SM_OC, SM_HC, SP_ICD, SR_RR
from application.permissions import UserPermission
from application.session import get_or_set_store_id
from application.utils import CustomizedEncoder
from flask import Blueprint, render_template, request, g
from dateutil.parser import parse

bp = Blueprint('stats', __name__, url_prefix="/stats")


def require_json():
    mimes = request.accept_mimetypes
    return mimes.accept_json and not mimes.accept_html


def extract_stats_params():
    return parse(request.args.get('start')), parse(request.args.get('end')), get_or_set_store_id()


def dump_json(stats):
    return json.dumps(stats, cls=CustomizedEncoder)


@bp.route('/tcr', methods=['GET', 'POST'])
@UserPermission()
def target_completion_rate():
    if require_json():
        stats_fields = ['total_orders_count', 'ta_settings']
        stats = get_weekly_store_stats_between_dates(*extract_stats_params(), stats_names=stats_fields)
        return dump_json(stats)
    return render_template('stats/tcr.html', selected_menu=SR_TCR, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/cr', methods=['GET', 'POST'])
@UserPermission()
def conversion_rate():
    if require_json():
        result = dict()
        stats_fields = ['total_rx_customer_count', 'total_orders_count', 'total_customer_count',
                        'test_drive_customer_count',
                        'test_drive_ordered_customer_count']
        result['weekly_stats'] = get_weekly_store_stats_between_dates(*extract_stats_params(), stats_names=stats_fields)
        result['car_stats'] = get_car_stats_between_dates_in_stores(*extract_stats_params(),
                                                                    stats_names=['rx_customers_count_by_car',
                                                                                 'orders_count_by_car'])
        return dump_json(result)
    return render_template('stats/cr.html', selected_menu=SR_CR, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/rr', methods=['GET', 'POST'])
@UserPermission()
def returning_rate():
    if require_json():
        stats = get_weekly_store_stats_between_dates(*extract_stats_params(),
                                                     stats_names=['total_rr_rx_count', 'total_rr_order'])
        return dump_json(stats)
    return render_template('stats/rr.html', selected_menu=SR_RR, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/fr', methods=['GET', 'POST'])
@UserPermission()
def filing_rate():
    if require_json():
        stats_fields = ['total_customer_count', 'formal_customer_count']
        stats = get_weekly_store_stats_between_dates(*extract_stats_params(), stats_names=stats_fields)
        return dump_json(stats)
    return render_template('stats/fr.html', selected_menu=SP_FR, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/acr', methods=['GET', 'POST'])
@UserPermission()
def appointment_completion_rate():
    if require_json():
        stats_fields = ['total_customer_count', 'instore_appt_count_by_customer', 'instore_appt_count',
                        'closed_instore_appt_count']
        stats = get_weekly_store_stats_between_dates(*extract_stats_params(), stats_names=stats_fields)
        return dump_json(stats)
    return render_template('stats/acr.html', selected_menu=SP_ACR, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/tdr', methods=['GET', 'POST'])
@UserPermission()
def test_drive_rate():
    if require_json():
        stats_fields = ['total_rx_customer_count', 'test_drive_customer_count']
        stats = get_weekly_store_stats_between_dates(*extract_stats_params(), stats_names=stats_fields)
        return dump_json(stats)
    return render_template('stats/tdr.html', selected_menu=SP_TDR, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/icd', methods=['GET', 'POST'])
@UserPermission()
def intent_car_distribution():
    if require_json():
        stats = get_car_stats_between_dates_in_stores(*extract_stats_params(),
                                                      stats_names=['rx_customers_count_by_car'])
        return dump_json(stats)
    return render_template('stats/icd.html', selected_menu=SP_ICD, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/sc', methods=['GET', 'POST'])
@UserPermission()
def sales_consultant():
    if require_json():
        # stats_fields = ['total_customer_count', 'test_drive_customers_count']
        # stats = get_weekly_store_stats_between_dates(*extract_stats_params(), stats_names=stats_fields)
        stats = get_sales_stats(get_or_set_store_id(),
                                ['total_rx_customer_count', 'total_orders_count', 'total_customer_count',
                                 'formal_customer_count', 'instore_appt_count', 'closed_instore_appt_count',
                                 'test_drive_customer_count', 'avg_rx_duration', 'total_deliver_count'])
        return dump_json(stats)
    return render_template('stats/sc.html', selected_menu=SM_SC, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/uoc', methods=['GET', 'POST'])
@UserPermission()
def unordered_customers():
    if require_json():
        stats = get_unordered_customers_count_by_intent_level(*extract_stats_params())
        return dump_json(stats)
    return render_template('stats/uoc.html', selected_menu=SM_UOC, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/oc', methods=['GET', 'POST'])
@UserPermission()
def ordered_customers():
    if require_json():
        stats = get_order_cycle_stats(*extract_stats_params(), stats_names=['order_count', 'rx_count', 'appt_count'])
        return dump_json(stats)
    return render_template('stats/oc.html', selected_menu=SM_OC, back_endpoint=request.args.get('back_endpoint', None))


@bp.route('/hc', methods=['GET', 'POST'])
@UserPermission()
def hibernate_customers():
    return render_template('stats/hc.html', selected_menu=SM_HC, back_endpoint=request.args.get('back_endpoint', None))
