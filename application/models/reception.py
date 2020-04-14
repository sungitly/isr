# -*- coding: utf-8 -*-
from datetime import date, timedelta, datetime

from flask.ext.babel import gettext
from sqlalchemy import Column, Integer, BigInteger, ForeignKey, and_, desc, func, Date, String, asc, distinct, event
from sqlalchemy.orm import relationship

from application.forms.mixins import SortMixin
from application.models.statustracker import StatusTrackerMixin
from application.pagination import DEFAULT_PAGE_SIZE
from application.pagination import DEFAULT_PAGE_START
from application.utils import calc_duration_until_now, TIME_FORMAT_WO_SEC
from .base import db, BaseMixin, StoreMixin


class Reception(db.Model, BaseMixin, StoreMixin, StatusTrackerMixin):
    __tablename__ = 'reception'

    customer_id = Column(BigInteger, ForeignKey('customer.id'), nullable=False)
    sales_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    receptionist_id = Column(BigInteger)
    appointment_id = Column(BigInteger)
    people_count = Column(Integer, default=1, nullable=False)
    rx_type = Column(String(50), default=False)
    orig_rx_type = Column(String(50), default=False)
    order_id = Column(BigInteger)
    rx_date = Column(Date, default=date.today, index=True, nullable=False)
    # TODO: calculate duration when status is changed using property.
    # reception duration is the time duration between ongoing -> completed/cancelled
    rx_duration = Column(Integer, default=0)

    prev_rx_id = Column(BigInteger)

    customer = relationship('Customer', lazy='joined', cascade="all")
    sales = relationship('User', lazy='joined', cascade="all")

    default_status = 'assigned'
    valid_status = ('assigned', 'ongoing', 'completed', 'cancelled')
    valid_type = ('new', 'appt_new', 'appt', 'other')
    """
    new: 首次
    appt_new: 首邀
    appt: 再次
    other: 手续
    """

    @property
    def start_str(self):
        return self.created_on.strftime(TIME_FORMAT_WO_SEC)

    @property
    def end_str(self):
        if self.status != 'completed' or not self.rx_duration:
            return ''
        else:
            return (self.created_on + timedelta(seconds=self.rx_duration)).strftime(TIME_FORMAT_WO_SEC)

    def people_count_display_text(self):
        if self.people_count <= 0:
            return u''
        elif self.people_count <= 3:
            return gettext('with %(num)s people', num=self.people_count)
        elif self.people_count:
            return gettext('with multiple people')

    def complete(self):
        if self.status == 'assigned':
            self.rx_duration = 0
        elif self.status == 'ongoing':
            if self.created_on:
                self.rx_duration = calc_duration_until_now(self.created_on)
            else:
                self.rx_duration = 0

        self.reset_rx_type_by_system()

        self.status = 'completed'

    def reset_rx_type_by_system(self):
        if self.rx_type == 'new':
            from application.models.appointment import Appointment
            if Reception.has_reception_before(self.customer_id, self.created_on):
                self.rx_type = 'appt'
            elif Appointment.has_appt_created_before(self.customer_id, self.created_on):
                self.rx_type = 'appt_new'
        elif self.rx_type == 'appt_new':
            if Reception.has_reception_before(self.customer_id, self.created_on):
                self.rx_type = 'appt'

    @classmethod
    def find_all_by_query_params_in_store(cls, store_id, **kwargs):
        query = cls.query.filter(and_(cls.store_id == store_id))

        if kwargs.get('type_filter'):
            query = query.filter(cls.rx_type == kwargs.get('type_filter'))

        if kwargs.get('start_date'):
            query = query.filter(cls.rx_date >= kwargs.get('start_date'))

        if kwargs.get('end_date'):
            query = query.filter(cls.rx_date <= kwargs.get('end_date'))

        if kwargs.get('sales_filter'):
            query = query.filter(cls.sales_id == int(kwargs.get('sales_filter')))

        if kwargs.get('incomplete', False):
            query = query.filter(cls._last_status_changer == 'system')

        if kwargs.get('status', False):
            status = kwargs.get('status')
            if status == 'in-store':
                query = query.filter(and_(cls.status != 'completed', cls.status != 'cancelled'))
            elif status == 'all':
                query = query.filter(cls.status != 'cancelled')
            else:
                query = query.filter(cls.status == status)
        else:
            query = query.filter(cls.status != 'cancelled')

        page = kwargs.get('page', DEFAULT_PAGE_START)
        per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

        sortable_fields = ('rx_date', 'customer_id', 'sales_id', 'created_on', 'rx_duration')

        query_order_fixed = SortMixin.add_order_query(query, cls, sortable_fields, kwargs)
        return query_order_fixed.paginate(page, per_page)

    @classmethod
    def find_all_leads_by_query_params_in_store(cls, store_id, **kwargs):
        from application.models.user import User, INSTORE_NO_RX_LEAD
        sales = User.find_by_sales_name(INSTORE_NO_RX_LEAD, store_id)

        if not sales:
            return None
        else:
            from application.models.customer import Customer
            query = cls.query.join(Customer, Customer.id == cls.customer_id).filter(
                and_(cls.store_id == store_id, cls.sales_id == sales.id))
            if kwargs.get('start_date'):
                query = query.filter(cls.rx_date >= kwargs.get('start_date'))

            if kwargs.get('end_date'):
                query = query.filter(cls.rx_date <= kwargs.get('end_date'))

            if kwargs.get('on_file', False):
                query = query.filter(func.length(Customer.mobile) >= 11)

            page = kwargs.get('page', DEFAULT_PAGE_START)
            per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

            return query.paginate(page, per_page)

    @classmethod
    def find_all_of_today_in_store(cls, store_id):
        return cls.query.filter(
            and_(cls.store_id == store_id, cls.rx_date == date.today(), cls.status != 'cancelled')).order_by(
            asc(cls.created_on)).all()

    @classmethod
    def find_all_by_date_in_store(cls, p_date, store_id):
        return cls.query.filter(
            and_(cls.store_id == store_id, cls.rx_date == p_date, cls.status != 'cancelled')).order_by(
            desc(cls.updated_on)).all()

    @classmethod
    def exist_sales_incomplete_receptions_of_today(cls, sales_id):
        count = db.session.query(func.count(cls.id)).filter(
            and_(cls.sales_id == sales_id, cls.rx_date == date.today(), cls.status != 'completed',
                 cls.status != 'cancelled')).scalar()
        return count > 0

    @classmethod
    def find_all_of_today_of_sales_by_status(cls, sales_id, status):
        return cls.query.filter(
            and_(cls.sales_id == sales_id, cls.rx_date == date.today(), cls.status == status)).order_by(
            desc(cls.updated_on)).all()

    @classmethod
    def complete_all_for_sales_customer(cls, sales_id, customer_id, reason):
        # user orm instead of bulk update for status change tracker
        receptions = cls.find_all_incomplete_for_sales_customer(sales_id, customer_id)

        for reception in receptions:
            reception.complete()
            reception._status_change_remark = reason

        return receptions

    @classmethod
    def complete_all_of_date_for_store(cls, store_id, process_date, reason, performer=''):
        if process_date is None:
            receptions = cls.find_all_incomplete_of_today_in_store(store_id)
        else:
            receptions = cls.find_all_incomplete_by_date_in_store(store_id, process_date)

        for reception in receptions:
            reception.complete()
            reception._last_status_changer = performer
            reception._status_change_remark = reason

        return receptions

    @classmethod
    def complete_all_of_today(cls, process_date, reason, performer=''):
        if process_date is None:
            receptions = cls.find_all_incomplete_of_today()
        else:
            receptions = cls.find_all_incomplete_by_date(process_date)
        for reception in receptions:
            reception.complete()
            reception._last_status_changer = performer
            reception._status_change_remark = reason

        return receptions

    @classmethod
    def find_all_incomplete_of_today_in_store(cls, store_id):
        return cls.query.filter(
            and_(cls.store_id == store_id, cls.rx_date == date.today(), cls.status != 'completed',
                 cls.status != 'cancelled')).all()

    @classmethod
    def find_all_incomplete_by_date_in_store(cls, store_id, p_date):
        return cls.query.filter(
            and_(cls.store_id == store_id, cls.rx_date == p_date, cls.status != 'completed',
                 cls.status != 'cancelled')).all()

    @classmethod
    def find_all_incomplete_of_today(cls):
        return cls.query.filter(
            and_(cls.rx_date == date.today(), cls.status != 'completed', cls.status != 'cancelled')).all()

    @classmethod
    def find_all_incomplete_by_date(cls, p_date):
        return cls.query.filter(
            and_(cls.rx_date == p_date, cls.status != 'completed', cls.status != 'cancelled')).all()

    @classmethod
    def count_all_incomplete_of_today_by_sales(cls, store_id):
        return db.session.query(cls.sales_id, func.count(cls.id)).filter(
            and_(cls.store_id == store_id, cls.rx_date == date.today(), cls.status != 'completed',
                 cls.status != 'cancelled')).group_by(cls.sales_id).all()

    @classmethod
    def find_all_incomplete_for_sales_customer(cls, sales_id, customer_id):
        return cls.query.filter(
            and_(cls.sales_id == sales_id, cls.customer_id == customer_id, cls.status != 'completed',
                 cls.status != 'cancelled')).all()

    @classmethod
    def reset_customer_id(cls, old_customer, new_customer):
        # TODO: switch to sql update to improve performance
        receptions = cls.query.filter(
            and_(cls.customer_id == old_customer.id, cls.status != 'cancelled')).all()

        for reception in receptions:
            reception.customer_id = new_customer.id

        cls.reset_customer_last_reception_date(new_customer)

    @classmethod
    def reset_customer_last_reception_date(cls, customer):
        last_reception = cls.query.filter(and_(cls.customer_id == customer.id, cls.status != 'cancelled')).order_by(
            desc(cls.created_on)).first()

        if last_reception:
            customer.last_reception_date = last_reception.created_on

    @classmethod
    def find_all_by_customer_sales(cls, customer_id, sales_id=None):
        query = cls.query.filter(cls.customer_id == customer_id).filter(cls.status != 'cancelled')
        if sales_id:
            query = query.filter(cls.sales_id == sales_id)
        return query.order_by(desc(cls.created_on)).all()

    @classmethod
    def count_all_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id,
                 cls.status != 'cancelled')).scalar()

    @classmethod
    def has_reception_before(cls, customer_id, p_date=date.today()):
        count = db.session.query(func.count(cls.id)).filter(
            and_(cls.customer_id == customer_id, db.func.date(cls.created_on) < p_date,
                 cls.status == 'completed')).scalar()

        return count > 0

    @classmethod
    def count_all_distinct_customers_count_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(distinct(cls.customer_id))).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.rx_type != 'other')).scalar()

    @classmethod
    def count_all_distinct_customers_count_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(distinct(cls.customer_id))).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.rx_type != 'other')).group_by(cls.sales_id).all()

    @classmethod
    def get_avg_rx_duration_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.avg(cls.rx_duration)).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id,
                 db.func.date(cls.created_on) == db.func.date(cls.updated_on), cls.status != 'cancelled',
                 cls.rx_type != 'other')).group_by(cls.sales_id).all()

    @classmethod
    def get_unordered_customers_count_by_intent_level_between_dates_in_store(cls, start, end, store_id):
        from application.models.customer import Customer
        return db.session.query(func.count(distinct(cls.customer_id)),
                                Customer._intent_level).outerjoin(Customer, Customer.id == cls.customer_id).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.rx_type != 'other', Customer.status != 'cancelled', Customer.status != 'duplicated',
                 Customer.status != 'defeated', Customer.status != 'ordered', Customer._intent_level > 0)).group_by(
            Customer._intent_level).all()

    @classmethod
    def get_rx_customers_count_by_car_models_bwteeen_dates_in_stores(cls, start, end, store_id):
        from application.models.customer import Customer
        return db.session.query(func.count(distinct(cls.customer_id)), Customer.intent_car_ids).outerjoin(Customer,
                                                                                                          Customer.id == cls.customer_id).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.rx_type != 'other', Customer.status != 'cancelled', Customer.status != 'duplicated',
                 Customer.intent_car_ids != None)).group_by(Customer.intent_car_ids).all()

    @classmethod
    def count_all_refered_between_dates_in_store(cls, start, end, store_id):
        from application.models.customer import Customer
        return db.session.query(cls.id).join(Customer, Customer.id == cls.customer_id).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.rx_type != 'other', Customer.status != 'cancelled', Customer.status != 'duplicated',
                 Customer.is_refered == 1)).all()

    @classmethod
    def count_all_reorder_between_dates_in_store(cls, start, end, store_id):
        from application.models.customer import Customer
        from application.models.order import Order
        return db.session.query(cls.id).join(Customer, Customer.id == cls.customer_id).join(Order,
                                                                                            Customer.id == Order.customer_id).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.rx_type != 'other', Customer.status != 'cancelled', Customer.status != 'duplicated',
                 Order.status != 'cancelled', cls.created_on > Order.created_on)).all()

    @classmethod
    def count_all_valid_by_date_in_store(cls, date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(cls.rx_date == date, cls.store_id == store_id, cls.status != 'cancelled',
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_all_valid_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id, cls.status != 'cancelled',
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_all_completed_by_system_by_date_in_store(cls, date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(cls.rx_date == date, cls.store_id == store_id, cls.status != 'cancelled',
                 cls._last_status_changer == 'system'), User.username != u'管理员').scalar()

    @classmethod
    def count_all_completed_by_system_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(cls.rx_date >= start, cls.rx_date <= end, cls.store_id == store_id, cls.status != 'cancelled',
                 cls._last_status_changer == 'system'), User.username != u'管理员').scalar()

    @classmethod
    def cancel_receptions_by_sales_id(cls, sales_id):
        now = datetime.now()
        return db.session.query(Reception).filter(
            db.and_(Reception.sales_id == sales_id, Reception.status != 'cancelled')).update(
            {'status': 'cancelled', '_last_status_changer': 'system', '_last_status_change_date': now})

    @classmethod
    def find_last_rx_by_customer_id(cls, customer_id):
        return cls.query.filter(cls.customer_id == customer_id).order_by(desc(cls.created_on)).first()

    def calc_leave_datetime_str(self):
        if self.status != 'completed':
            return u'未点击离店'
        else:
            leave_datetime = self.created_on + timedelta(seconds=self.rx_duration)
            if isinstance(leave_datetime, datetime):
                return leave_datetime.strftime('%H:%M')
            else:
                return u''


@event.listens_for(Reception, 'before_insert')
def set_orig_rx_type(mapper, connection, target):
    target.orig_rx_type = target.rx_type


def push_msg_for_reception_creation(reception):
    msg = dict()
    title = gettext('reception created')
    msg['title'] = title if not isinstance(title, unicode) else title.encode('utf-8')
    body = gettext(u'customer reception: %(name)s (%(people_count)s)', name=reception.customer.respect_name,
                   people_count=reception.people_count_display_text())
    msg['body'] = body if not isinstance(body, unicode) else body.encode('utf-8')
    return msg


def push_msg_for_reception_cancelled(reception):
    msg = dict()
    title = gettext('reception cancelled')
    msg['title'] = title if not isinstance(title, unicode) else title.encode('utf-8')
    body = gettext(u'customer reception: %(name)s is cancelled', name=reception.customer.respect_name)
    msg['body'] = body if not isinstance(body, unicode) else body.encode('utf-8')
    return msg
