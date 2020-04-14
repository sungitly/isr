# -*- coding: utf-8 -*-
import datetime
import json

import requests

from application.models.hwaccount import HwjdAccount
from application.models.hwcustomer import HwjdCustomer
from application.models.lookup import LookupValue
from application.models.reception import Reception
from config import Config

HWJD_OA_GET_INFO_API = '/WebHwStoreService/WebHwInterfaceScService.asmx/GetHwjdScrbInfo'
HWJD_OA_SYNC_CUSTOMER_API = '/WebHwStoreService/WebHwInterfaceScService.asmx/ReceiveHwjdScImportInfo'

SUCCESS = 1
FAIL = 0

API_VERSION = 'V1.0'


def update_hwjd_oa(hwjd_customer):
    account_info = HwjdAccount.find_by_store_id(hwjd_customer.store_id)

    if account_info:
        params = dict()
        params['Companycode'] = account_info.org_code
        params['Usercode'] = account_info.user_code
        params['Password'] = account_info.password
        params['Version'] = API_VERSION
        params['P_xml'] = hwjd_customer.to_xml()

        try:
            r = requests.post(Config.HWJD_OA_SERVER + HWJD_OA_SYNC_CUSTOMER_API, data=params)
            if r and r.status_code == 200 and 'OK' in r.content:
                return SUCCESS
        except:
            return FAIL

    return FAIL


def get_hwjd_scrb_info(hwjd_account_info, info_type):
    if hwjd_account_info:
        params = dict()
        params['Companycode'] = hwjd_account_info.org_code
        params['Usercode'] = hwjd_account_info.user_code
        params['Password'] = hwjd_account_info.password
        params['Version'] = API_VERSION
        params['P_lx'] = info_type

        try:
            r = requests.post(Config.HWJD_OA_SERVER + HWJD_OA_GET_INFO_API, data=params)
            if r and r.status_code == 200:
                import xml.etree.ElementTree as ElementTree
                element = ElementTree.fromstring(r.content)
                return json.loads(element.text)
        except:
            return FAIL

    return FAIL


def sync_rx_with_hwjd_oa(rx):
    hc = HwjdCustomer.convert_from_reception(rx)

    # send request to hwjd
    try:
        result = update_hwjd_oa(hc)
    except:
        result = FAIL

    hc.last_sync_date = datetime.datetime.now()
    hc.last_sync_status = result

    hc.save_and_commit()


def sync_hwjd_customer_rx_by_date(store_id, date_str):
    receptions = Reception.find_all_by_date_in_store(date_str, store_id)

    for rx in receptions:
        sync_rx_with_hwjd_oa(rx)


AVAIL_ACCOUNTS = ((u'丰田', '101009', 'sc101009', 'sc123!@#'),
                  (u'骏达', '101002', 'sc101002', 'sc123!@#'),
                  (u'骏捷', '101003', 'sc101003', 'sc123!@#'),
                  (u'远德', '101093', 'sc101093', 'sc123!@#'),
                  (u'名濠', '101031', 'sc101031', 'sc123!@#'),
                  (u'名达', '101070', 'sc101070', 'sc123!@#'),
                  (u'新濠', '101024', 'sc101024', 'sc123!@#'),
                  (u'骏濠', '101030', 'sc101030', 'sc123!@#'),
                  (u'润濠', '101035', 'sc101035', 'sc123!@#'),
                  (u'润骐', '101209', 'sc101209', 'sc123!@#'),
                  (u'君德', '101249', 'sc101249', 'sc123!@#'),
                  (u'澎众', '101215', 'sc101215', 'sc123!@#'),
                  (u'骏迈', '101084', 'sc101084', 'sc123!@#'),
                  (u'瑞泰', '101042', 'sc101042', 'sc123!@#'),
                  (u'轩泰', '101214', 'sc101214', 'sc123!@#'),
                  (u'轩德', '101086', 'sc101086', 'sc123!@#'),
                  (u'泓德', '101207', 'sc101207', 'sc123!@#'),
                  (u'浩众', '101010', 'sc101010', 'sc123!@#'),
                  (u'名宣', '101078', 'sc101078', 'sc123!@#'),
                  (u'燕兴', '101057', 'sc101057', 'sc123!@#'),
                  (u'铭德', '101079', 'sc101079', 'sc123!@#'),
                  (u'燕语', '101085', 'sc101085', 'sc123!@#'),
                  (u'尊泰', '101222', 'sc101222', 'sc123!@#'),
                  (u'浩涵', '101205', 'sc101205', 'sc123!@#'),
                  (u'高德', '101008', 'sc101008', 'sc123!@#'),
                  (u'名路翔', '101225', 'sc101225', 'sc123!@#'),
                  (u'浩之宝', '101210', 'sc101210', 'sc123!@#'))


def test_accounts(accounts):
    fail_accounts = []
    for account in accounts:
        params = dict()
        params['Companycode'] = account[1]
        params['Usercode'] = account[2]
        params['Password'] = account[3]
        params['Version'] = 'V1.0'
        params['P_lx'] = u'市场-采购类型'

        try:
            r = requests.post(Config.HWJD_OA_SERVER + HWJD_OA_GET_INFO_API, data=params)
            if not r or r.status_code != 200:
                fail_accounts.append(account)
        except:
            fail_accounts.append(account)

    print fail_accounts
