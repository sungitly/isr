# -*- coding: utf-8 -*-

from application.apns import crmrx_apns, crm_apns
from application.integration.hwjd import sync_rx_with_hwjd_oa
from application.models.reception import Reception
from application.queue import celery
from application.xgpush import xg_push
from application.xgpush.xinge import Message
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def replace_space_in_ios_token(token):
    if token and ' ' in token:
        token = token.replace(' ', '')

    return token


@celery.task(name='send_message_to_rx_client')
def send_message_to_rx_client(token, alert=None, badge=None, sound=None, content_available=None,
                              expiry=None, payload=None, **extra):
    token = replace_space_in_ios_token(token)
    crmrx_apns.send_message(token, alert, badge, sound, content_available, expiry, payload, **extra)


@celery.task(name='send_message_to_sales_client')
def send_message_to_sales_client(token, device_type, alert=None, badge=None, sound=None, content_available=None,
                                 expiry=None, payload=None, **extra):
    if device_type == 'ios':
        token = replace_space_in_ios_token(token)
        crm_apns.send_message(token, alert, badge, sound, content_available, expiry, payload, **extra)

    if device_type == 'android':
        message = Message()
        if isinstance(alert, dict):
            message.title = alert['title']
            message.content = alert['body']
        else:
            message.content = alert
        # 消息类型：1：通知 2：透传消息，必填
        message.type = 2
        message.expireTime = 86400
        message.custom = extra
        xg_push.PushSingleDevice(token, message)


@celery.task(name='sync_hwjd_customer_rx')
def sync_hwjd_customer_rx(reception_id):
    reception = Reception.find(reception_id)

    if reception:
        sync_rx_with_hwjd_oa(reception)
