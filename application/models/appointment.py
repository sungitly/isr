# -*- coding: utf-8 -*-
import datetime

from dateutil.parser import parse
from sqlalchemy import Column, String, DateTime, BigInteger, ForeignKey, Date, and_, desc, or_, func, distinct, asc
from sqlalchemy.orm import relationship

from application.forms.mixins import SortMixin
from application.models.customer import Customer
from application.models.statustracker import StatusTrackerMixin
from application.nutils.date import parse_date
from application.pagination import DEFAULT_PAGE_START, DEFAULT_PAGE_SIZE
from .base import db, StoreMixin, BaseMixin


class Appointment(db.Model, BaseMixin, StoreMixin, StatusTrackerMixin):
    __tablename__ = 'appointment'

    customer_id = Column(BigInteger, ForeignKey('customer.id'), nullable=False)
    sales_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    _appt_date = Column('appt_date', Date, index=True)
    _appt_datetime = Column('appt_datetime', DateTime, nullable=False)
    remark = Column(String(500))
    type = Column(String(50), default='followup', nullable=False)

    customer = relationship('Customer', lazy='joined', cascade="all")
    sales = relationship('User', lazy='joined', cascade="all")

    default_status = 'opened'
    valid_status = ('opened', 'closed', 'cancelled')
    valid_types = ('instore', 'followup', 'deliver', 'other', 'deliver_followup')

    all_types_mapping = (
        ('all', u'预约类型'), ('instore', u'预约到店'), ('deliver', u'预约交车'), ('other', u'预约手续'), ('followup', u'预约回访'),
        ('deliver_followup', u'交车跟进'))

    """
    instore: 预约客户来店洽谈
    followup: 预约电话回访客户
    deliver: 预约客户来店交车
    other: 预约手续
    deliver_followup: 交车回访
    """

    @property
    def appt_datetime(self):
        return self._appt_datetime

    @appt_datetime.setter
    def appt_datetime(self, appt_datetime):
        if isinstance(appt_datetime, datetime.datetime):
            self._appt_datetime = appt_datetime
        else:
            self._appt_datetime = parse(appt_datetime)

        self._appt_date = self._appt_datetime.date()
        if self.customer:
            self.customer.next_appointment_date = appt_datetime

    @property
    def appt_date(self):
        return self._appt_date

    @classmethod
    def has_appt_created_before(cls, customer_id, p_date=datetime.date.today()):
        count = db.session.query(func.count(cls.id)).filter(
            and_(cls.customer_id == customer_id, db.func.date(cls.created_on) < p_date,
                 cls.type == 'instore', cls.status != 'cancelled')).scalar()

        return count > 0

    @classmethod
    def find_all_by_query_params_in_store(cls, store_id, **kwargs):
        query = cls.query.filter(and_(cls.store_id == store_id))

        if kwargs.get('type_filter'):
            query = query.filter(cls.type == kwargs.get('type_filter'))

        if kwargs.get('start_date'):
            query = query.filter(cls._appt_date >= kwargs.get('start_date'))

        if kwargs.get('end_date'):
            query = query.filter(cls._appt_date <= kwargs.get('end_date'))

        if kwargs.get('status'):
            status = kwargs.get('status')
            if status == 'closed':
                query = query.filter(or_(and_(cls.type == 'followup', cls.status.in_((status, 'cancelled'))),
                                         and_(cls.type != 'followup', cls.status == status)))
            elif status == 'cancelled':
                query = query.filter(and_(cls.type != 'followup', cls.status == status))
            else:
                query = query.filter(cls.status == status)

        if kwargs.get('sales_filter'):
            query = query.filter(cls.sales_id == int(kwargs.get('sales_filter')))

        page = kwargs.get('page', DEFAULT_PAGE_START)
        per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

        sortable_fields = ('customer_id', '_appt_datetime', 'type', 'customer_id', 'sales_id')
        query_order_fixed = SortMixin.add_order_query(query, cls, sortable_fields, kwargs)
        return query_order_fixed.paginate(page, per_page)

    @classmethod
    def find_all_of_sales(cls, sales_id, page=DEFAULT_PAGE_START, per_page=DEFAULT_PAGE_SIZE):
        return cls.query.filter(cls.sales_id == sales_id).order_by(
            desc(cls.updated_on)).paginate(page, per_page)

    @classmethod
    def find_all_by_sales_before_sync_in_bulk(cls, sales_id, last_sync_date, bulk_size):
        query = cls.query.filter(cls.sales_id == sales_id)

        if last_sync_date:
            query = query.filter(cls.updated_on >= last_sync_date)

        bulk_size = bulk_size if bulk_size is not None else 100

        return query.order_by(asc(cls.updated_on)).paginate(1, bulk_size)

    @classmethod
    def exist_followup_between_dates_by_customer(cls, start, end, customer_id, store_id):
        count = db.session.query(func.count(cls.id)).filter(
            and_(cls.store_id == store_id, cls.customer_id == customer_id,
                 cls.type == 'followup', cls._appt_date >= start, cls._appt_date <= end)).scalar()
        return count > 0

    @classmethod
    def exist_opened_of_sales_customer(cls, sales_id, customer_id):
        count = db.session.query(func.count(cls.id)).filter(
            and_(cls.sales_id == sales_id, cls.customer_id == customer_id, cls.status == 'opened')).scalar()
        return count > 0

    @classmethod
    def find_all_opened_by_type_and_date_of_sales_customer(cls, p_type, p_date, sales_id, customer_id):
        return cls.query.filter(
            and_(cls.type == p_type, cls._appt_date <= p_date, cls.sales_id == sales_id,
                 cls.customer_id == customer_id,
                 cls.status == 'opened')).all()

    @classmethod
    def find_all_between_dates_in_store(cls, start_date, end_date, store_id):
        return cls.query.filter(
            and_(cls.store_id == store_id, cls._appt_date >= start_date, cls._appt_date <= end_date,
                 or_(cls.type == 'instore', cls.type == 'deliver', cls.type == 'other'),
                 cls.status == 'opened')).order_by(
            desc(cls.updated_on)).all()

    @classmethod
    def find_all_by_date_in_store(cls, p_date, store_id):
        return cls.query.filter(and_(cls.store_id == store_id, cls._appt_date == p_date)).order_by(
            desc(cls.updated_on)).all()

    @classmethod
    def find_all_by_q_in_store(cls, query_criteria, store_id):
        query_criteria = '%' + query_criteria + '%'
        return cls.query.join(Appointment.customer).filter(
            and_(cls.store_id == store_id, or_(cls.type == 'instore', cls.type == 'deliver'),
                 cls.status == 'opened',
                 or_(Customer.name.like(query_criteria), Customer.mobile.like(query_criteria)))).order_by(
            desc(cls.updated_on)).all()

    @classmethod
    def cancel_all_for_sales_customer(cls, sales_id, customer_id, cancel_reason):
        # user orm instead of bulk update for status change tracker
        appointments = cls.query.filter(
            and_(cls.sales_id == sales_id, cls.customer_id == customer_id, cls.status != 'closed',
                 cls.status != 'cancelled')).all()

        for appt in appointments:
            appt.status = 'cancelled'
            appt._status_change_remark = cancel_reason

    @classmethod
    def cancel_all_for_sales(cls, sales_id, cancel_reason):
        appointments = cls.query.filter(
            and_(cls.sales_id == sales_id, cls.status != 'closed', cls.status != 'cancelled')).all()

        for appt in appointments:
            appt.status = 'cancelled'
            appt._status_change_remark = cancel_reason

    @classmethod
    def reset_customer_id(cls, old_customer, new_customer):
        # TODO: switch to sql update to improve performance
        appointments = cls.query.filter(and_(cls.customer_id == old_customer.id, cls.status != 'cancelled')).all()

        for appt in appointments:
            appt.customer_id = new_customer.id

        cls.reset_customer_next_appointment_date(new_customer)

    @classmethod
    def reset_customer_next_appointment_date(cls, customer):
        next_appointment = cls.query.filter(and_(cls.customer_id == customer.id, cls.status != 'cancelled')).order_by(
            asc(cls._appt_datetime)).first()

        if next_appointment:
            customer.next_appointment_date = next_appointment.appt_datetime

    @classmethod
    def find_all_by_customer_sales(cls, customer_id, sales_id=None):
        query = cls.query.filter(cls.customer_id == customer_id)
        if sales_id:
            query = query.filter(cls.sales_id == sales_id)
        return query.order_by(desc(cls._appt_datetime)).all()

    @classmethod
    def count_instore_appts_by_customers_between_dates_in_store(cls, start, end, store_id):
        from application.models.customer import Customer
        return db.session.query(func.count(distinct(Customer.id))).filter(
            and_(cls.customer_id == Customer.id, cls.status != 'cancelled', cls.type == 'instore',
                 db.func.date(Customer.created_on) >= start,
                 db.func.date(Customer.created_on) <= end, Customer.store_id == store_id,
                 Customer.status != 'cancelled', Customer.status != 'duplicated')).scalar()

    @classmethod
    def count_instore_appts_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(distinct(cls.customer_id))).filter(
            and_(cls.store_id == store_id, cls.status != 'cancelled', cls.type == 'instore',
                 db.func.date(cls._appt_datetime) >= start), db.func.date(cls._appt_datetime) <= end).scalar()

    @classmethod
    def count_closed_instore_appts_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(distinct(cls.customer_id))).filter(
            and_(cls.store_id == store_id, cls.status == 'closed', cls.type == 'instore',
                 db.func.date(cls._appt_datetime) >= start), db.func.date(cls._appt_datetime) <= end).scalar()

    @classmethod
    def count_instore_appts_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(cls.sales_id)).filter(
            and_(cls.store_id == store_id, cls.status != 'cancelled', cls.type == 'instore',
                 db.func.date(cls._appt_datetime) >= start), db.func.date(cls._appt_datetime) <= end).group_by(
            cls.sales_id).all()

    @classmethod
    def count_closed_instore_by_sales_appts_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(cls.sales_id)).filter(
            and_(cls.store_id == store_id, cls.status == 'closed', cls.type == 'instore',
                 db.func.date(cls._appt_datetime) >= start), db.func.date(cls._appt_datetime) <= end).group_by(
            cls.sales_id).all()

    @classmethod
    def count_all_new_appt_by_date_in_store(cls, date, store_id):
        from application.models.user import User

        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == date, cls.store_id == store_id, User.username != u'管理员')).scalar()

    @classmethod
    def count_all_new_appt_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User

        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end,
                 cls.store_id == store_id,
                 User.username != u'管理员')).scalar()

    def get_type_for_display(self):
        if self.type == 'followup':
            return u'预约回访'
        elif self.type == 'instore':
            return u'预约到店'
        elif self.type == 'deliver':
            return u'预约交车'
        elif self.type == 'other':
            return u'预约手续'
        elif self.type == 'deliver_followup':
            return u'交车回访'
        else:
            return u''

    @classmethod
    def auto_make_delivered_followup_appointments(cls, order):
        delivered_date = parse_date(order.delivered_date)
        delivered_datetime = datetime.datetime.combine(delivered_date, datetime.time.min)

        appt_time_1st = delivered_datetime + datetime.timedelta(days=1, hours=9)
        appt_time_2nd = delivered_datetime + datetime.timedelta(days=6, hours=9)

        appt_1st = Appointment()
        appt_1st.customer_id = order.customer_id
        appt_1st.store_id = order.store_id
        appt_1st.sales_id = order.sales_id
        appt_1st.remark = u'交车后第一次回访'
        appt_1st.appt_datetime = appt_time_1st
        appt_1st.type = 'deliver_followup'
        appt_1st.save()

        appt_2nd = Appointment()
        appt_2nd.customer_id = order.customer_id
        appt_2nd.store_id = order.store_id
        appt_2nd.sales_id = order.sales_id
        appt_2nd.remark = u'交车后第二次回访'
        appt_2nd.appt_datetime = appt_time_2nd
        appt_2nd.type = 'deliver_followup'

        appt_2nd.save()
