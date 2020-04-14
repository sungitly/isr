#coding: utf-8
from application.permissions import UserPermission
from application.session import set_store_id
from flask import Blueprint, request, g, jsonify

bp = Blueprint('session_setting', __name__, url_prefix="/session_setting")


@bp.route('/store_id', methods=['POST'])
@UserPermission()
def store_id():
    current_user = g.user
    store_id = request.form.get('store_id')
    try:
        store_id_int = int(store_id)
    except:
        return jsonify({'message': 'invalid store_id', 'error': 'param error'})
    if store_id_int:
        set_store_id(store_id_int)
    return jsonify({'message': 'change store_id ok', 'error': 'ok'})
