# -*- coding: utf-8 -*-
from flask import current_app, url_for
import os


def assets(path):
    assets_server_url = os.environ.get('ASSETS_SERVER_URL')

    if assets_server_url:
        return assets_server_url + path
    else:
        return url_for('static', filename=current_app.config['ASSETS_VERSION_PATH'] + path)
