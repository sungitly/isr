# -*- coding: utf-8 -*-

import json
import time

import os
from application import csrf
from application.controllers._helper import flash_success, flash_error
from application.models.base import db
from application.models.inventory import InvImportHistory, Inventory
from application.nutils.menu import INV_MGMT
from application.permissions import StockPermission
from application.session import get_or_set_store_id
from application.utils import str_random
from flask import Blueprint, render_template, request, current_app, url_for, send_from_directory
from flask import Response
from werkzeug.utils import redirect

bp = Blueprint('inventories', __name__, url_prefix="/inventories")

default_inv_status = [u'在途', u'在库', u'锁定', u'销售出库']


def build_inv_status_items(store_id):
    existing_result = Inventory.find_distinct_field_values_by_store(Inventory.inv_status, store_id)
    existing_inv_status = [item[0] for item in existing_result]

    existing_inv_status.extend(default_inv_status)
    all_inv_status = list(set(existing_inv_status))
    all_inv_status.sort()

    ret = [{'id': '', 'name': ''}]
    for item in all_inv_status:
        ret.append({'id': item, 'name': item})

    return ret


@bp.route('/', methods=['GET', 'POST'])
@StockPermission()
def inventories():
    inv_status_items = build_inv_status_items(get_or_set_store_id())
    return render_template('inventories/inventories.html', selected_menu=INV_MGMT, inv_status_items=inv_status_items)


@bp.route('/template', methods=['GET', 'POST'])
@StockPermission()
def download_template():
    from application.docgen.docgen import TEMPLATE_FOLDER
    return send_from_directory(directory=TEMPLATE_FOLDER, filename='inv_template.xlsx', as_attachment=True)


@bp.route('/download', methods=['GET', 'POST'])
@StockPermission()
def download_inv():
    store_id = get_or_set_store_id()
    from application.docgen.docgen import generate_store_inventories_excel
    filename = generate_store_inventories_excel(store_id, Inventory.find_all_by_store_id_wo_pagination(store_id))
    from application.docgen.docgen import OUTPUT_FOLDER
    return send_from_directory(OUTPUT_FOLDER, filename=filename, as_attachment=True)


@bp.route('/get_inventories', methods=['GET'])
def get_inventories():
    from application.models.inventory import Inventory
    from application.utils import CustomizedEncoder

    result = Inventory.find_all_by_store_id_wo_pagination(get_or_set_store_id())

    data = json.dumps(result, cls=CustomizedEncoder)

    resp = Response(response=data, status=200, mimetype="application/json")
    return (resp)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ('xls', 'xlsx')


@bp.route('/import', methods=['POST'])
@StockPermission()
def import_inv():
    if request.method == 'POST':
        upload_file = request.files['upload_file']
        if not upload_file or not allowed_file(upload_file.filename):
            flash_error(u'导入文件不存在或者不是合法的文件类型')
        else:
            origin_file_name = upload_file.filename
            store_id = get_or_set_store_id()
            gen_file_name = gen_inv_upload_file_path(store_id, origin_file_name)
            upload_file.save(gen_file_name)

            import_his = InvImportHistory()
            import_his.origin_file = origin_file_name
            import_his.import_file = os.path.relpath(gen_file_name, current_app.config['INV_UPLOAD_FOLDER'])
            db.session.add(import_his)

            Inventory.save_from_excel(gen_file_name, store_id)
            flash_success(u'导入成功')
    return redirect(url_for('inventories.inventories'))


def gen_inv_upload_file_path(store_id, filename):
    upload_dir = os.path.join(current_app.config['INV_UPLOAD_FOLDER'], str(store_id))

    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    return os.path.join(upload_dir, u's%s_%s_%s%s' % (
        unicode(store_id), unicode(int(time.time())), str_random(6), os.path.splitext(filename)[1]))


csrf.exempt(import_inv)
