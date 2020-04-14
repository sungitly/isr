# -*- coding: utf-8 -*-
import datetime

from application.cache import cache
from application.events import new_sales_joined, new_receptionist_joined, sales_status_changed, new_reception_created, \
    sales_logout, receptionist_logout, reception_cancelled
from application.models.reception import push_msg_for_reception_creation, push_msg_for_reception_cancelled
from application.models.user import User, SalesStatus, SalesLastRxTime
from application.models.userdevice import UserDevice


@new_sales_joined.connect
def handle_new_sales_joined(sender, **kw):
    new_sales = kw.get('sales', None)

    if new_sales:
        # invalid sales cache
        cache.delete_memoized(User.get_all_sales_by_store_from_cache, long(new_sales.store_id))
        # update sales status
        SalesStatus.set_sales_status(new_sales.store_id, new_sales.id)


@new_receptionist_joined.connect
def handle_new_receptionist_joined(sender, **kw):
    new_receptionist = kw.get('receptionist', None)

    if new_receptionist:
        cache.delete_memoized(User.get_all_receptionist_by_store_from_cache, long(new_receptionist.store_id))


@sales_status_changed.connect
def handle_sales_status_changed(sender, **kw):
    store_id = kw.get('store_id', None)

    if store_id:
        notify_receptionists(store_id)


@new_reception_created.connect
def handle_new_reception_created(sender, **kw):
    new_reception = kw.get('new_reception', None)

    SalesStatus.set_sales_status(new_reception.store_id, new_reception.sales_id, 'busy')
    SalesLastRxTime.set_sales_rxtime(new_reception.store_id, new_reception.sales_id, datetime.datetime.utcnow())
    notify_sales(new_reception.sales_id, push_msg_for_reception_creation(new_reception), type="reception",
                 reception_id=new_reception.id)


@reception_cancelled.connect
def handle_reception_cancelled(sender, **kw):
    reception = kw.get('reception', None)

    SalesStatus.update_sales_status(reception.store_id, reception.sales_id)
    notify_sales(reception.sales_id, push_msg_for_reception_cancelled(reception), type="reception")


@sales_logout.connect
def handle_sales_logout(sender, **kw):
    sales = kw.get('sales', None)

    if sales:
        cache.delete_memoized(User.get_all_sales_by_store_from_cache, long(sales.store_id))
        SalesStatus.del_sales_status(sales.store_id, sales.id)
        UserDevice.del_device_tokens_for_user(sales.id)
        notify_receptionists(sales.store_id)


@receptionist_logout.connect
def handle_receptionist_logout(sender, **kw):
    receptionist = kw.get('receptionist')

    if receptionist:
        cache.delete_memoized(User.get_all_receptionist_by_store_from_cache, long(receptionist.store_id))
        UserDevice.del_device_tokens_for_user(receptionist.id)


def notify_receptionists(store_id):
    from application.queue import async_call
    receptionists = User.get_all_receptionist_by_store_from_cache(long(store_id))

    for reception in receptionists:
        tokens = UserDevice.get_all_device_tokens_for_user(reception.id)
        if isinstance(tokens, set) and len(tokens) > 0:
            for token in tokens:
                async_call("send_message_to_rx_client", [token], {"sound": "default"})


def notify_sales(sales_id, message, **kwargs):
    from application.queue import async_call
    tokens = UserDevice.get_all_device_tokens_for_user(sales_id)

    if isinstance(tokens, set) and len(tokens) > 0:
        kwargs['badge'] = 1
        kwargs['alert'] = message
        kwargs['sound'] = "default"

        for key, value in kwargs.iteritems():
            if isinstance(value, unicode):
                kwargs[key] = value.encode('utf-8')

        for token in tokens:
            async_call("send_message_to_sales_client", [token, UserDevice.get_device_type_by_token(token)], kwargs)


def notify_all_sales_of_store(store_id, message, **kwargs):
    sales_list = User.get_all_sales_by_store_from_cache(long(store_id))

    for sales in sales_list:
        notify_sales(sales.id, message, **kwargs)
