# -*- coding: utf-8 -*-
from datetime import datetime

from .base import db
from sqlalchemy import Column, String, BigInteger, Integer, event, DateTime, and_, desc
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import orm


class SalesTracker(db.Model):
    __tablename__ = 'sales_tracker'

    id = Column(BigInteger, primary_key=True)
    customer_id = Column(BigInteger, nullable=False)
    from_sales_id = Column(BigInteger, nullable=False)
    to_sales_id = Column(BigInteger, nullable=False)
    created_on = Column(DateTime)

    @classmethod
    def find_all_by_sales_with_start_date(cls, sales_id, start_time):
        return cls.query.filter(and_( cls.from_sales_id == sales_id, cls.created_on >= start_time)).order_by(desc(cls.created_on)).all()

    @classmethod
    def find_all_by_from_sales(cls, sales_id):
        return cls.query.filter(and_(cls.from_sales_id == sales_id)).order_by(desc(cls.created_on)).all()