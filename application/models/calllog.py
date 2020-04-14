# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, event, BigInteger, func, and_, or_
from sqlalchemy.orm import relationship

from application.forms.mixins import SortMixin
from application.models.base import db, BaseMixin, StoreMixin
from application.models.customer import Customer
from application.pagination import DEFAULT_PAGE_SIZE
from application.pagination import DEFAULT_PAGE_START
from application.utils import calc_duration


class Calllog(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'calllog'

    customer_id = Column(BigInteger, ForeignKey('customer.id'), nullable=False)
    mobile = Column(String(200))
    appointment_id = Column(BigInteger)
    duration = Column(Integer, default=0, nullable=False)
    call_start = Column(DateTime, nullable=False)
    call_end = Column(DateTime, nullable=True)
    sales_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)

    customer = relationship('Customer', lazy='joined', cascade="all")
    sales = relationship('User', lazy='joined', cascade="all")

    sequence_id = Column(String(100))

    @classmethod
    def count_all_by_date_in_store(cls, date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == date, cls.store_id == store_id, User.username != u'管理员')).scalar()

    @classmethod
    def count_all_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 User.username != u'管理员')).scalar()

    @classmethod
    def find_all_by_query_params_in_store(cls, store_id, **kwargs):
        query = cls.query.join(Calllog.customer).filter(and_(cls.store_id == store_id))

        if kwargs.get('start_date'):
            query = query.filter(db.func.date(cls.created_on) >= kwargs.get('start_date'))

        if kwargs.get('end_date'):
            query = query.filter(db.func.date(cls.created_on) <= kwargs.get('end_date'))

        if kwargs.get('sales_filter'):
            query = query.filter(cls.sales_id == int(kwargs.get('sales_filter')))

        if kwargs.get('keywords'):
            keywords = '%' + kwargs.get('keywords') + '%'
            query = query.filter(or_(cls.mobile.like(keywords), Customer.name.like(keywords)))

        page = kwargs.get('page', DEFAULT_PAGE_START)
        per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

        sortable_fields = ('call_start', 'sales_id', 'customer_id', 'call_start', 'duration')
        query_order_fixed = SortMixin.add_order_query(query, cls, sortable_fields, kwargs)

        return query_order_fixed.paginate(page, per_page)

    @classmethod
    def find_by_sequence_id(cls, sequence_id):
        return cls.query.filter(cls.sequence_id == sequence_id).first()

    @classmethod
    def find_all_by_customer_id(cls, customer_id):
        return cls.query.filter(cls.customer_id == customer_id).all()


@event.listens_for(Calllog, 'before_insert')
def calc_call_duration(mapper, connection, target):
    target.duration = calc_duration(target.call_start, target.call_end)
