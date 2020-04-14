# -*- coding: utf-8 -*-
from application.models.base import db, BaseMixin, StoreMixin
from sqlalchemy import Column, BigInteger, ForeignKey, Integer, DateTime, String
from sqlalchemy.orm import relationship


class DriveRecord(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'drive_record'

    customer_id = Column(BigInteger, ForeignKey('customer.id'), nullable=False)
    sales_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    car_code = Column(String(100))
    start = Column(DateTime)
    end = Column(DateTime)
    duration = Column(Integer, default=0)

    customer = relationship('Customer', lazy='joined', cascade="all")
    sales = relationship('User', lazy='joined', cascade="all")
