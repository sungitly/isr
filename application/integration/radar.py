# -*- coding: utf-8 -*-
import requests
from flask import current_app

details_trend_api = '/storeStatics/detailsTrend'
device_status_api = '/deviceStatus/storeDeviceStatus'
total_trend_api = '/storeStatics/totalTrend'
all_devices_status_api = '/deviceStatus/listAll'


# noinspection PyBroadException
def convert_details_trend(stats, device_status):
    if not stats:
        return []

    dates = stats.keys()
    dates.sort()

    result = []
    for date in dates:
        s = {}
        data = stats[date]
        s['date'] = date
        s['effective_count'] = data['effectiveCount']
        s['new_count'] = data['newCount']
        s['old_count'] = data['oldCount']
        s['effective_count'] = data['effectiveCount']
        s['intent_count'] = data['intentCount']
        s['device_status'] = device_status[date]
        result.append(s)
    return result


def get_details_trend(store_id, start, end):
    params = {'store_id': store_id, 'start': start, 'end': end}

    sr = requests.get(current_app.config['RADAR_SERVER_URL'] + device_status_api, params)
    r = requests.get(current_app.config['RADAR_SERVER_URL'] + details_trend_api, params)

    return convert_details_trend(get_data_from_response(r), get_data_from_response(sr))


def get_all_devices_status():
    r = requests.get(current_app.config['RADAR_SERVER_URL'] + all_devices_status_api)

    if r and r.status_code == 200:
        try:
            data = r.json()
            if data['status'] == 0:
                return data['content']['data']
        except Exception:
            pass
    return None


def get_data_from_response(response):
    if response and response.status_code == 200:
        try:
            data = response.json()
            if data['status'] == 0:
                return data['content']['dataList']
        except Exception:
            pass


def get_data_content_from_response(response):
    if response and response.status_code == 200:
        try:
            data = response.json()
            if data['status'] == 0:
                return data['content']
        except Exception:
            pass


def is_any_device_online(devices):
    if len(devices) > 0:
        for status in devices.values():
            if unicode(status) != u'off':
                return True

    return False


def get_radar_online_days(start, end, store_id):
    params = {'start': start, 'end': end, 'store_id': store_id}
    r = requests.get(current_app.config['RADAR_SERVER_URL'] + device_status_api, params)

    data = get_data_from_response(r)
    online_count = 0
    if data:
        for date, devices in data.items():
            if is_any_device_online(devices):
                online_count += 1

    return online_count


def get_radar_count(start, end, store_id):
    params = {'start': start, 'end': end, 'store_id': store_id}
    r = requests.get(current_app.config['RADAR_SERVER_URL'] + total_trend_api, params)
    effective_count = 0
    data = get_data_content_from_response(r)
    if data and data['effectiveCount']:
        effective_count = data['effectiveCount']

    return effective_count
