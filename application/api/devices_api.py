# -*- coding: utf-8 -*-
from application.api import api
from application.models.userdevice import UserDevice
from flask import request


@api.route('/devices', methods=['PUT', 'POST'])
def create_or_update_user_devices():
    data = request.json

    user_device = UserDevice(**data)

    UserDevice.add_device(user_device)

    return user_device
