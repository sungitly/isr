# coding: utf-8
import requests
from flask import request, current_app, jsonify
from urlparse import urljoin

from application.api import api


@api.route('/proxy_radar', methods=('POST', ))
def proxy_radar():
    args = request.args
    surl = args.get('surl', None)
    store_id = args.get('store', None)
    start = args.get('start', None)
    end = args.get('end', None)
    #todo: error check
    params = dict(
        store_id=store_id,
        start=start,
        end=end
    )
    radar_data_url = current_app.config['RADAR_DATA_URL']
    url = urljoin(radar_data_url, surl)
    r = requests.post(url, data=params)
    return jsonify(r.json())
