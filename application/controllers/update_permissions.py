#coding: utf-8
from flask import Blueprint, request, jsonify
from application.integration.ucenter import uc_get_user_infos, uc_save_user

bp = Blueprint('update_permissions', __name__, url_prefix="/update_permissions")


def ok_response(msg):
    return jsonify({'error': 'ok', 'message': msg})


def err_response(msg):
    return jsonify({'error': 'failed', 'message': msg})


@bp.route('/', methods=['POST'])
def index():
    user_ids = request.json
    response_user_infos = uc_get_user_infos(user_ids)
    if not response_user_infos:
        return ok_response('update users info failed')
    for user_info in response_user_infos.user_infos:
        uc_save_user(user_info)
    return ok_response('update all users info ok')
