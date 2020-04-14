# -*- coding: utf-8 -*-
import datetime

from sqlalchemy import Column, String, BigInteger, Boolean, Date, desc, and_, ForeignKey, func, distinct, or_, event, \
    Numeric
from sqlalchemy.orm import relationship, joinedload

from application.forms.mixins import SortMixin
from application.models.lookup import LookupValue
from application.models.sequence import SeqGen
from application.models.statustracker import StatusTrackerMixin
from application.models.user import User
from application.pagination import DEFAULT_PAGE_SIZE, DEFAULT_PAGE_START
from .base import db, BaseMixin, StoreMixin


class Order(db.Model, BaseMixin, StoreMixin, StatusTrackerMixin):
    __tablename__ = 'order'

    customer_id = Column(BigInteger, ForeignKey('customer.id'), nullable=False)
    sales_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    order_no = Column(String(100))
    ordered_car_id = Column(String(100), nullable=False)
    ordered_car_name = Column(String(100), nullable=False)
    ordered_car_series = Column(String(100))
    remark = Column(String(500))
    is_confirmed = Column(Boolean, default=False)
    delivered_date = Column(Date)

    customer = relationship('Customer', lazy='joined', cascade="all")
    sales = relationship('User', cascade="all")

    default_status = 'new'
    valid_status = ('new', 'delivered', 'cancelled')

    history_order = Column(Boolean, default=False)

    receipt_title = Column(String(500))
    is_mortgage = Column(Boolean, default=False)
    include_insurance = Column(Boolean, default=False)

    invoice_price = Column(Numeric(precision=12, scale=2))
    mortgage_amt = Column(Numeric(precision=12, scale=2))
    finance_fee = Column(Numeric(precision=12, scale=2))
    insurance_amt = Column(Numeric(precision=12, scale=2))
    insurance_ext_amt = Column(Numeric(precision=12, scale=2))
    service_fee = Column(Numeric(precision=12, scale=2))
    prepaid_card_amt = Column(Numeric(precision=12, scale=2))

    amount_fields = (
        'invoice_price', 'mortgage_amt', 'finance_fee', 'insurance_amt', 'insurance_ext_amt', 'service_fee',
        'prepaid_card_amt')

    @classmethod
    def excludes_attrs(cls):
        excludes = [item for item in BaseMixin.attributes_names()]
        excludes.extend(
            ['customer_id', 'sales_id', 'order_no', 'customer', 'sales', 'status', 'store_id', 'amount_fields'])
        return excludes

    @classmethod
    def has_valid_orders_by_customer(cls, customer_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(cls.customer_id == customer_id, cls.status != 'cancelled')).scalar() > 0

    @classmethod
    def find_all_by_sales(cls, sales_id):
        return cls.query.filter(cls.sales_id == sales_id).order_by(desc(cls.updated_on)).all()

    @classmethod
    def find_all_in_status_by_sales(cls, sales_id, status):
        return cls.query.filter(
            and_(cls.sales_id == sales_id, cls.status == status)).order_by(desc(cls.updated_on)).all()

    @classmethod
    def find_all_in_status_by_store(cls, store_id, status=None, confirmed=None, page=DEFAULT_PAGE_START,
                                    per_page=DEFAULT_PAGE_SIZE):
        filters = [cls.store_id == store_id]
        if status:
            filters.append(cls.status == status)

        if confirmed is not None:
            filters.append(cls.is_confirmed == confirmed)

        criteria = and_(*filters)

        return cls.query.options(joinedload(cls.sales)).filter(criteria).order_by(desc(cls.updated_on)).paginate(page,
                                                                                                                 per_page)

    @classmethod
    def reset_customer_id(cls, old_customer, new_customer):
        # TODO: switch to sql update to improve performance
        orders = cls.query.filter(
            and_(cls.customer_id == old_customer.id, cls.status != 'cancelled')).all()

        for order in orders:
            order.customer_id = new_customer.id

    @classmethod
    def find_all_by_customer_sales(cls, customer_id, sales_id=None):
        query = cls.query.filter(cls.customer_id == customer_id).filter(cls.status != 'cancelled')
        if sales_id:
            query = query.filter(cls.sales_id == sales_id)
        return query.order_by(desc(cls.created_on)).all()

    @classmethod
    def find_latest_delivered_order_by_customer(cls, customer_id):
        return cls.query.filter(cls.customer_id == customer_id).filter(cls.status == 'delivered').order_by(desc(
            cls.delivered_date)).first()

    @classmethod
    def find_all_created_today_by_store(cls, store_id):
        return cls.query.options(joinedload(cls.sales)).filter(
            and_(cls.store_id == store_id, db.func.date(cls.created_on) == datetime.date.today()),
            cls.status != 'cancelled', cls.history_order == 0).order_by(cls.created_on).all()

    @classmethod
    def find_all_by_query_params_in_store(cls, store_id, **kwargs):
        query = cls.query.options(joinedload(cls.sales)).filter(
            and_(cls.store_id == store_id, cls.status != 'cancelled'))

        if kwargs.get('status'):
            query = query.filter(cls.status == kwargs.get('status'))

        if kwargs.get('start_date'):
            if 'delivered' == kwargs.get('status'):
                query = query.filter(and_(db.func.date(cls.delivered_date) >= kwargs.get('start_date')))
            else:
                query = query.filter(and_(db.func.date(cls.created_on) >= kwargs.get('start_date')))

        if kwargs.get('end_date'):
            if 'delivered' == kwargs.get('status'):
                query = query.filter(and_(db.func.date(cls.delivered_date) <= kwargs.get('end_date')))
            else:
                query = query.filter(and_(db.func.date(cls.created_on) <= kwargs.get('end_date')))

        if kwargs.get('ordered_car_ids'):
            query = query.filter(cls.ordered_car_id == kwargs.get('ordered_car_ids'))

        if kwargs.get('sales_id'):
            query = query.filter(cls.sales_id == int(kwargs.get('sales_id')))

        if kwargs.get('keywords'):
            from application.models.customer import Customer
            keywords = '%' + kwargs.get('keywords') + '%'
            query = query.filter(
                or_(cls.order_no.like(keywords), cls.customer.has(Customer.name.like(keywords)),
                    cls.sales.has(User.username.like(keywords)),
                    cls.ordered_car_name.like(keywords), cls.receipt_title.like(keywords)))

        if not kwargs.get('history'):
            query = query.filter(cls.history_order == 0)

        page = kwargs.get('page', DEFAULT_PAGE_START)
        per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

        sortable_fields = ('created_on', 'delivered_date', 'status')
        query_order_fixed = SortMixin.add_order_query(query, cls, sortable_fields, kwargs)
        return query_order_fixed.paginate(page, per_page)

    @classmethod
    def count_orders_by_date_and_store(cls, p_date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == p_date, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.history_order == 0, User.username != u'管理员')).scalar()

    @classmethod
    def count_orders_between_date_and_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0, User.username != u'管理员')).scalar()

    @classmethod
    def count_delivered_orders_between_date_and_store(cls, store_id, start=None, end=None):
        from application.models.user import User
        query = db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(cls.store_id == store_id,
                 cls.status == 'delivered', User.username != u'管理员'))

        if start:
            query = query.filter(db.func.date(cls.delivered_date) >= start)

        if end:
            query = query.filter(db.func.date(cls.delivered_date) <= end)

        return query.scalar()

    @classmethod
    def count_no_deliver_date_orders_between_date_and_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0,
                 or_(cls.delivered_date == None, cls.delivered_date < db.func.date(cls.created_on)),
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_no_deliver_date_orders_by_date_and_store(cls, p_date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == p_date, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0,
                 or_(cls.delivered_date == None, cls.delivered_date < db.func.date(cls.created_on)),
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_overdue_orders_between_date_and_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status == 'new', cls.history_order == 0, cls.delivered_date < datetime.date.today(),
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_overdue_orders_by_date_and_store(cls, p_date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == p_date, cls.store_id == store_id,
                 cls.status == 'new', cls.history_order == 0, cls.delivered_date < datetime.date.today(),
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_all_new_orders_by_store(cls, store_id):
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(cls.store_id == store_id, cls.status == 'new', cls.history_order == 0,
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_orders_from_date_and_store(cls, p_date, store_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= p_date, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.history_order == 0)).scalar()

    @classmethod
    def find_orders_status_from_date_and_store(cls, p_date, store_id):
        return db.session.query(cls.id, cls.status).filter(
            and_(db.func.date(cls.created_on) >= p_date, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.history_order == 0)).all()

    @classmethod
    def count_all_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0)).scalar()

    @classmethod
    def count_all_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0)).group_by(cls.sales_id).all()

    @classmethod
    def count_all_delivered_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status == 'delivered', cls.history_order == 0)).group_by(cls.sales_id).all()

    @classmethod
    def count_all_by_car_models_bwteeen_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(cls.id), cls.ordered_car_id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0)).group_by(cls.ordered_car_id).all()

    @classmethod
    def count_all_within_cycle_between_dates_in_store(cls, start, end, store_id, cycle):
        from application.models.customer import Customer
        query = db.session.query(func.count(cls.id)).outerjoin(Customer, Customer.id == cls.customer_id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.history_order == 0))

        if len(cycle) == 1:
            query = query.filter(func.datediff(cls.created_on, Customer.created_on) >= cycle[0])
        elif len(cycle) > 1:
            query = query.filter(and_(func.datediff(cls.created_on, Customer.created_on) >= cycle[0],
                                      func.datediff(cls.created_on, Customer.created_on) < cycle[1]))

        return query.scalar()

    @classmethod
    def get_rx_count_within_cycle_between_dates_in_store(cls, start, end, store_id, cycle):
        from application.models.reception import Reception
        from application.models.customer import Customer
        query = db.session.query(func.count(distinct(Reception.id))).outerjoin(Customer,
                                                                               Customer.id ==
                                                                               Reception.customer_id).outerjoin(
            Order, Order.customer_id == Customer.id).filter(
            and_(db.func.date(Order.created_on) >= start, db.func.date(Order.created_on) <= end,
                 Order.store_id == store_id, Order.status != 'cancelled', Reception.status != 'cancelled',
                 Reception.rx_type != 'other'))

        if len(cycle) == 1:
            query = query.filter(func.datediff(Order.created_on, Customer.created_on) >= cycle[0])
        elif len(cycle) > 1:
            query = query.filter(and_(func.datediff(Order.created_on, Customer.created_on) >= cycle[0],
                                      func.datediff(Order.created_on, Customer.created_on) < cycle[1]))

        return query.scalar()

    @classmethod
    def get_appt_count_within_cycle_between_dates_in_store(cls, start, end, store_id, cycle):
        from application.models.appointment import Appointment
        from application.models.customer import Customer
        query = db.session.query(func.count(distinct(Appointment.id))).outerjoin(Customer,
                                                                                 Customer.id ==
                                                                                 Appointment.customer_id).outerjoin(
            Order, Order.customer_id == Customer.id).filter(
            and_(db.func.date(Order.created_on) >= start, db.func.date(Order.created_on) <= end,
                 Order.store_id == store_id, Order.status != 'cancelled',
                 or_(Appointment.type == 'instore', Appointment.type == 'followup')))

        if len(cycle) == 1:
            query = query.filter(func.datediff(Order.created_on, Customer.created_on) >= cycle[0])
        elif len(cycle) > 1:
            query = query.filter(and_(func.datediff(Order.created_on, Customer.created_on) >= cycle[0],
                                      func.datediff(Order.created_on, Customer.created_on) < cycle[1]))

        return query.scalar()

    @classmethod
    def count_all_refered_between_dates_in_store(cls, start, end, store_id):
        from application.models.customer import Customer
        return db.session.query(cls.id).join(Customer, Customer.id == cls.customer_id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end,
                 cls.store_id == store_id, cls.status != 'cancelled', cls.history_order == 0,
                 Customer.is_refered == 1)).all()

    @classmethod
    def count_all_reorder_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end,
                 cls.store_id == store_id, cls.status != 'cancelled', cls.history_order == 0)).group_by(
            cls.customer_id).having(
            func.count(cls.customer_id) > 1).all()

    def generate_order_no(self):
        self.order_no = SeqGen.generate_seq(Order.__name__, self.store_id)

    def get_status_for_display(self):
        if self.status == 'new':
            return u'未交车'
        elif self.status != 'delivered':
            return u'已交车'
        elif self.status == 'cancelled':
            return u'已取消'
        else:
            return u''


@event.listens_for(Order, 'before_insert')
def update_car_series(mapper, connection, target):
    if target.ordered_car_id:
        lookupvalue_dict = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(target.store_id),
                                                                                           'intent-car')
        lookupvalue = lookupvalue_dict.get(target.ordered_car_id)
        if lookupvalue:
            target.ordered_car_name = lookupvalue.value
            target.ordered_car_series = lookupvalue.section
