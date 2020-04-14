# -*- coding: utf-8 -*-
import datetime

from flask import request

from application.api import api
from application.decorators import log_job_result
from application.handlers import notify_all_sales_of_store
from application.integration.frtinv import sync_latest_store_inventory
from application.integration.hwjd import sync_hwjd_customer_rx_by_date
from application.models.campaign import Campaign, push_msg_for_campaign_creation
from application.models.customer import Customer
from application.models.reception import Reception
from application.models.user import User, INSTORE_NO_RX_LEAD
from application.nutils.date import parse_date
from application.utils import parse_comma_seperated_args


@api.route('/jobs/daily/campaigns/notify', methods=['GET'])
@log_job_result()
def notify_today_campaigns():
    """
    Could be scheduled every morning 8:30 ~ 9:00 AM.
    Check and send notification about campaigns
    """
    store_id = request.args.get('store_id', None)
    campaigns_notify = {}

    if store_id:
        campaigns = Campaign.find_all_to_be_notified_today_by_store(store_id)
    else:
        campaigns = Campaign.find_all_to_be_notified_today()

    if campaigns:
        for campaign in campaigns:
            notify_all_sales_of_store(campaign.store_id, push_msg_for_campaign_creation(campaign), type="campaign",
                                      campaign_id=campaign.id)
            campaign.notify_sent = True

        campaigns_notify['notify_count'] = len(campaigns)

        return campaigns_notify

    return 0


@api.route('/jobs/daily/receptions/cleanup', methods=['GET'])
@log_job_result()
def cleanup_today_receptions():
    """
    Could be scheduled every morning 7:00 AM.
    Complete un-completed receptions today.
    :return:
    """
    store_id = request.args.get('store_id', None)
    process_date = parse_date(request.args.get('process_date', None), default=datetime.date.today())
    reason = 'Daily Cleanup'
    receptions_cleanup = {}

    if store_id:
        receptions = Reception.complete_all_of_date_for_store(store_id, process_date, reason, 'system')
    else:
        receptions = Reception.complete_all_of_today(process_date, reason, 'system')

    receptions_cleanup['store_id'] = store_id
    receptions_cleanup['process_date'] = process_date
    receptions_cleanup['processed_count'] = len(receptions)

    return receptions_cleanup


@api.route('/jobs/daily/receptions/invalid/cancel', methods=['GET'])
@log_job_result()
def cleanup_today_invalid_receptions():
    """
    Find id in user which username is invalid reception
    Set status is cancelled which in reception and customer
    """

    users = User.find_all_by_sales_name(INSTORE_NO_RX_LEAD)
    cancelled_rx_count = 0
    cancelled_cus_count = 0
    invalid_cancelled = {}

    if len(users) != 0:
        for invalid_user in users:
            sales_id = invalid_user.id

            cancelled_rx_count += Reception.cancel_receptions_by_sales_id(sales_id)
            cancelled_cus_count += Customer.cancel_not_filed_customers_by_sales_id(sales_id)

    invalid_cancelled['cancelled_rx_count'] = cancelled_rx_count
    invalid_cancelled['cancelled_cus_count'] = cancelled_cus_count

    return invalid_cancelled


@api.route('/jobs/daily/receptions/publish/hwjd', methods=['GET'])
@log_job_result()
def publish_rx_to_hwjd():
    result = {}

    store_ids = parse_comma_seperated_args(request.args.get('store_id', None))
    if not store_ids:
        from application.models.hwaccount import HwjdAccount
        store_ids = HwjdAccount.find_active_hwjd_store_ids()
    result['store_ids'] = store_ids

    process_date = parse_date(request.args.get('process_date'), default=datetime.date.today())
    result['process_date'] = process_date

    if not store_ids or len(store_ids) == 0:
        return

    for store_id in store_ids:
        sync_hwjd_customer_rx_by_date(store_id, process_date)

    return result


@api.route('/jobs/hourly/inventories/refresh/frt', methods=['GET'])
@log_job_result(daily=False)
def refresh_frt_inventory():
    result = []

    store_ids = parse_comma_seperated_args(request.args.get('store_id', None))

    for store_id in store_ids:
        sync_timestamp, inventories, shared_inventories = sync_latest_store_inventory(store_id)
        result.append({'store_id': store_id, 'sync_timestamp': sync_timestamp, 'inventories_count': len(inventories),
                       'shared_inventories_count': len(shared_inventories)})

    return result
