# -*- coding: utf-8 -*-
import json

from application.models.base import db
from sqlalchemy import Column, Integer, Text, BigInteger
from sqlalchemy import String


class VinRecord(db.Model):
    __tablename__ = 'vin_record'

    id = Column(BigInteger, primary_key=True)
    vin = Column(String(20), index=True)
    source = Column(String(20))
    year = Column(Integer)
    make = Column(String(50))
    model = Column(String(100))
    _extra = Column('extra', Text)

    @property
    def extra(self):
        return json.loads(self._extra)

    @extra.setter
    def extra(self, extra_dict):
        self._extra = json.dumps(extra_dict)

    @classmethod
    def find_by_vin(cls, vin):
        return cls.query.filter(cls.vin == vin).first()
