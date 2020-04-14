# -*- coding: utf-8 -*-
import os

from flask import Blueprint, request, render_template, url_for, redirect, send_from_directory, current_app
from werkzeug.utils import secure_filename

from application.api.ops_api import ALL_STATS
from application.controllers._helper import flash_success, flash_error, flash_info
from application.forms.ops import AppUpgradeForm
from application.integration.radar import get_details_trend, get_all_devices_status, get_radar_count
from application.integration.radar import get_radar_online_days
from application.models.appmeta import AppMeta, ReleaseHistory
from application.models.stats import get_store_daily_stats
from application.models.stats import get_store_stats
from application.models.store import Store
from application.nutils.menu import OPS_OVERVIEW
from application.nutils.menu import STORE_STATS_SUMMARY, STORE_RADAR_SUMMARY, APPS_MGMT_SUMMARY, RADAR_STATUS_SUMMARY, \
    LOOKUPVALUE_MGMT_SUMMARY
from application.nutils.url import back_url
from application.permissions import OpsPermission
from application.utils import get_stores_selection, remove_empty_storename, get_stores_descriptions_and_lookupvalues, \
    convert_changevalues

bp = Blueprint('ops', __name__, url_prefix="/ops")


def validate(query):
    if not query.get('end_date', None) or not query.get('end_date', None):
        return False
    elif query['start_date'] > query['end_date']:
        return False
    elif not query.get('store_filter'):
        return False

    return True


def check_filename(filename, store_id):
    correct_filename = 'lookupvalues' + '_' + str(store_id) + '.xlsx'
    if filename == correct_filename:
        return True
    return False


@bp.route('/overview', methods=['GET', 'POST'])
@OpsPermission()
def overview():
    from application.forms.ops import TimePeriodForm
    search_form = TimePeriodForm(request.args)
    query = dict()
    if search_form.start.data and search_form.start.data != '':
        query['start_date'] = search_form.start.data
    if search_form.end.data and search_form.end.data != '':
        query['end_date'] = search_form.end.data

    query['store_filter'] = 'all'

    result = []
    if validate(query):
        start = query['start_date']
        end = query['end_date']

        stores = Store.find_all()
        stores = sorted(stores, key=lambda s: s.name)
        for store in stores:
            if store.id > 0:
                stats_data = get_store_stats(start, end, store.id, ALL_STATS)
                stats_data['online_days'] = get_radar_online_days(start, end, store.id)
                if stats_data['rx_count'] > 0:
                    stats_data['incomplete_rx_percent'] = str(
                        stats_data['incomplete_rx_count'] * 100 / stats_data['rx_count']) + '%'
                else:
                    stats_data['incomplete_rx_percent'] = 'N/A'
                result.append((store.id, store.name, stats_data))

    return render_template('ops/overview.html', selected_menu=OPS_OVERVIEW, form=search_form, stats=result)


@bp.route('/download/overview', methods=['GET', 'POST'])
@OpsPermission()
def download_overview():
    # TODO: refactor to remove duplications with overview method.
    from application.docgen.docgen import generate_ops_overview_excel, OUTPUT_FOLDER
    from application.forms.ops import TimePeriodForm
    search_form = TimePeriodForm(request.args)
    query = dict()
    if search_form.start.data and search_form.start.data != '':
        query['start_date'] = search_form.start.data
    if search_form.end.data and search_form.end.data != '':
        query['end_date'] = search_form.end.data

    query['store_filter'] = 'all'

    result = []
    if validate(query):
        start = query['start_date']
        end = query['end_date']

        stores = Store.find_all()
        stores = sorted(stores, key=lambda s: s.name)
        for store in stores:
            if store.id > 0:
                stats_data = get_store_stats(start, end, store.id, ALL_STATS)
                stats_data['online_days'] = get_radar_online_days(start, end, store.id)
                if stats_data['rx_count'] > 0:
                    stats_data['incomplete_rx_percent'] = str(
                        stats_data['incomplete_rx_count'] * 100 / stats_data['rx_count']) + '%'
                else:
                    stats_data['incomplete_rx_percent'] = 'N/A'
                result.append((store.id, store.name, stats_data))
        generated_filename = generate_ops_overview_excel(start, end, result)
        # TODO: change a more efficient way to serve static file.
        return send_from_directory(OUTPUT_FOLDER, generated_filename)

    return render_template('ops/overview.html', selected_menu=OPS_OVERVIEW, form=search_form, stats=result)


@bp.route('/isr', methods=['GET', 'POST'])
@OpsPermission()
def isr():
    from application.forms.ops import GenericSearchForm
    search_form = GenericSearchForm(request.args)
    search_form.store_filter.choices = get_stores_selection()

    # build query
    query = dict()
    if search_form.start.data and search_form.start.data != '':
        query['start_date'] = search_form.start.data
    if search_form.end.data and search_form.end.data != '':
        query['end_date'] = search_form.end.data
    if search_form.store_filter.data and search_form.store_filter.data not in ('None', 'all'):
        query['store_filter'] = search_form.store_filter.data

    if validate(query):
        stats_data = get_store_daily_stats(query['start_date'], query['end_date'], query['store_filter'],
                                           ['rx_count', 'incomplete_rx_count', 'new_valid_customer_count',
                                            'new_appt_count', 'new_calls_count', 'new_orders_count'])
    else:
        stats_data = []
    return render_template('ops/isr.html', selected_menu=STORE_STATS_SUMMARY, form=search_form,
                           stats=stats_data)


@bp.route('/radar', methods=['GET', 'POST'])
@OpsPermission()
def radar():
    from application.forms.ops import GenericSearchForm
    search_form = GenericSearchForm(request.args)
    search_form.store_filter.choices = get_stores_selection()

    # build query
    query = dict()
    if search_form.start.data and search_form.start.data != '':
        query['start_date'] = search_form.start.data
    if search_form.end.data and search_form.end.data != '':
        query['end_date'] = search_form.end.data
    if search_form.store_filter.data and search_form.store_filter.data not in ('None', 'all'):
        query['store_filter'] = search_form.store_filter.data

    if validate(query):
        stats_data = get_details_trend(query['store_filter'], query['start_date'], query['end_date'])
    else:
        stats_data = []
    return render_template('ops/radar.html', selected_menu=STORE_RADAR_SUMMARY, form=search_form,
                           stats=stats_data)


@bp.route('/radar/status', methods=['GET'])
@OpsPermission()
def radar_status():
    data = []
    result = get_all_devices_status()
    if result:
        data = sorted(result, key=lambda s: s['storename'])

    return render_template('ops/radar_status.html', selected_menu=RADAR_STATUS_SUMMARY, devices=data)


@bp.route('/apps', methods=['GET', 'POST'])
@OpsPermission()
def apps():
    apps = AppMeta.find_all()
    return render_template('ops/apps.html', selected_menu=APPS_MGMT_SUMMARY, apps=apps)


@bp.route('/app/<app_name>', methods=['GET', 'POST'])
def app_detail(app_name):
    app = AppMeta.find_by_name(app_name)
    notes = ReleaseHistory.find_all_by_app_name(app_name)

    form = AppUpgradeForm()

    if form.validate():
        app.upgrade(form.version.data, form.version_num.data, form.note.data)
        flash_success(u'成功提交升级信息')
        return redirect(
            url_for('ops.app_detail', app_name=app_name, back_url=back_url(url_for('ops.apps'))),
            code=303)

    return render_template('ops/app_detail.html', selected_menu=APPS_MGMT_SUMMARY, app=app, notes=notes, form=form,
                           back_url=back_url(url_for('ops.apps')))


@bp.route('/lookupvalue', methods=['GET', 'POST'])
@OpsPermission()
def lookupvalues():
    from application.forms.ops import LookupvalueForm
    from application.models.lookup import LookupValue

    selections = remove_empty_storename(get_stores_selection())

    search_lookupvalue = LookupvalueForm(request.args)
    search_lookupvalue.store_filter.choices = selections

    lookup_id = request.args.get('lookup_filter', None)
    descriptions = get_stores_descriptions_and_lookupvalues(lookup_id)

    if search_lookupvalue.store_filter.data and search_lookupvalue.store_filter.data not in ('None', 'all'):
        store_id = search_lookupvalue.store_filter.data
        store_name = Store.find_storename_by_store_id(store_id).name

        from application.models.lookup import Lookup
        id_and_description = Lookup.get_descriptions_by_store_id(store_id)
        search_lookupvalue.lookup_filter.choices = [(lookup.id, lookup.description) for lookup in id_and_description]
    else:
        store_id = ''
        store_name = ''
        search_lookupvalue.lookup_filter.choices = {}

    if lookup_id and lookup_id is not None:
        lookupvalueslist = LookupValue.find_all_by_lookup_id_by_order(lookup_id)
    else:
        lookupvalueslist = []

    return render_template('ops/lookupvalue.html', selected_menu=LOOKUPVALUE_MGMT_SUMMARY, form=search_lookupvalue,
                           lookupvalues=lookupvalueslist, descriptions=descriptions, storename=store_name,
                           lookup_id=lookup_id, store_id=store_id)


@bp.route('/lookupvalue/<int:lookup_id>', methods=['GET', 'POST'])
@OpsPermission()
def lookupvalues_add(lookup_id):
    from application.models.lookup import Lookup
    from application.createlookupvalues import add_lookupvalue, check_looupvalue

    lookup_by_store_and_name = Lookup.get_description_by_store_id(lookup_id)
    descriptions = get_stores_descriptions_and_lookupvalues(lookup_id)
    version = lookup_by_store_and_name.version

    store_name = Store.find_storename_by_store_id(lookup_by_store_and_name.store_id).name

    if request.method == 'POST':
        changevalues = convert_changevalues(request.form)
        message = check_looupvalue(lookup_id, changevalues)
        if message:
            flash_error(message)
            return redirect(url_for('ops.lookupvalues_add', lookup_id=lookup_id), code=303)

        count = add_lookupvalue(lookup_id, version, changevalues)
        if count is None:
            flash_error(u"更新失败!")
        elif count == 0:
            flash_info(u"未发生更新!")
        else:
            flash_success(u"成功更新%s条信息!" % count)

        return redirect(url_for('ops.lookupvalues_add', lookup_id=lookup_id), code=303)

    return render_template('ops/lookupvalues_add.html', store_name=store_name, lookup_by_id=lookup_by_store_and_name,
                           descriptions=descriptions, lookup_id=lookup_id)


@bp.route('/lookupvalue/<int:lookupvalue_id>/delete', methods=['GET'])
@OpsPermission()
def lookupvalues_delete(lookupvalue_id):
    from application.models.lookup import Lookup
    from application.models.lookup import LookupValue
    lookupvalue = LookupValue.find(lookupvalue_id)

    version = lookupvalue.version
    LookupValue.update_version(lookupvalue.lookup_id, version, lookupvalue.id)
    Lookup.update_version(lookupvalue.lookup_id, version)

    lookup = Lookup.find(lookupvalue.lookup_id)

    from werkzeug.datastructures import ImmutableMultiDict
    request.args = ImmutableMultiDict(dict(store_filter=lookup.store_id, lookup_filter=lookup.id))
    return lookupvalues()


@bp.route('/lookupvalues_upload/<int:store_id>', methods=['GET', 'POST'])
@OpsPermission()
def lookupvalues_upload(store_id):
    from application.forms.ops import CreateLookupvalueForm
    from application.createlookupvalues import generate_lookup, generate_lookupvalue
    from application.nutils.excel import load_excel

    store_name = Store.find_storename_by_store_id(store_id).name

    form = CreateLookupvalueForm()

    redirect_url = redirect(
        url_for('ops.lookupvalues_upload', store_id=store_id), code=303)

    if form.validate_on_submit():
        filename = secure_filename(form.lookupvalue_file.data.filename)
        if check_filename(filename, store_id):
            lookupvalues_file = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.lookupvalue_file.data.save(lookupvalues_file)

            lookupvalues_data = load_excel(lookupvalues_file)

            lookup_ids = generate_lookup(store_id)

            if generate_lookupvalue(lookup_ids, lookupvalues_data):
                flash_success(u"店面信息导入完成")
                return redirect_url

        else:
            flash_error(u'上传的文件名错误')
            return redirect_url

    return render_template('ops/lookupvalues_upload.html', storename=store_name, form=form)
