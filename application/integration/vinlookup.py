# -*- coding: utf-8 -*-

import requests
from application.cache import LONG_CACHE, cache
from application.models.base import db
from application.models.vinrecord import VinRecord
from flask import current_app

YI_FAN_VIN_SERVICE_UREL = 'http://qp.ityouyi.com/VINCodeServer/api.php'


class VinLookupService(object):
    @classmethod
    @cache.memoize(timeout=LONG_CACHE)
    def get_by_vin(cls, vin):
        # find from database
        vin_record = VinRecord.find_by_vin(vin)

        if not vin_record:
            # request from external api
            try:
                res = requests.get(YI_FAN_VIN_SERVICE_UREL, {'VIN': vin})
                if res and res.status_code == 200:
                    vin_info = cls.convert_to_dict(res.json())
                    vin_record = VinRecord()
                    vin_record.source = 'YF'
                    vin_record.vin = vin
                    vin_record.make = vin_info.get(u'品牌', None)
                    if vin_info.get(u'车型', None):
                        vin_record.model = vin_info.get(u'车型', None)
                    else:
                        vin_record.model = vin_info.get(u'车系', None)
                    vin_record.year = cls.convert_to_year(vin_info.get(u'上市年月', None))
                    vin_record.extra = vin_info
                    db.session.add(vin_record)
            except:
                current_app.logger.warning('Fail to fetch VIN info from %s for %s' % (YI_FAN_VIN_SERVICE_UREL, vin))

        return vin_record

    @staticmethod
    def convert_to_dict(list_of_dict):
        result = {}
        for item in list_of_dict:
            if isinstance(item, dict):
                for k, v in item.items():
                    result[k] = v

        return result

    @staticmethod
    def convert_to_year(date_str):
        """
        :param date_str: XXXX年X月
        :return: year int type
        """
        try:
            if date_str and len(date_str) >= 4:
                return int(date_str[:4])
        except:
            return None
