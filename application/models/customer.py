# -*- coding: utf-8 -*-
from datetime import datetime, date, timedelta

from flask.ext.babel import gettext
from flask.ext.sqlalchemy import BaseQuery
from sqlalchemy import Column, String, Boolean, BigInteger, desc, and_, DateTime, event, func, Date, ForeignKey, or_, \
    distinct, asc
from sqlalchemy import orm
from sqlalchemy.orm import relationship, joinedload
from sqlalchemy.sql import functions

from application.exceptions import InvalidMobileNumberExcetpion, DuplicatedCustomerException, \
    NoPermissionOnCustomerException
from application.forms.mixins import SortMixin
from application.models.driverecord import DriveRecord
from application.models.order import Order
from application.models.salestracker import SalesTracker
from application.models.statustracker import StatusTrackerMixin
from application.pagination import DEFAULT_PAGE_START, DEFAULT_PAGE_SIZE
from application.utils import validate_mobile, format_mobile
from .base import db, BaseMixin, StoreMixin


class Customer(db.Model, BaseMixin, StoreMixin, StatusTrackerMixin):
    __tablename__ = 'customer'

    name = Column(String(200))
    mobile = Column(String(200))
    gender = Column(Boolean, default=True)
    age_group = Column(String(50))
    intent_car_ids = Column(String(200))
    intent_car_series = Column(String(200))
    intent_car_colors = Column(String(200))
    test_drive_car_ids = Column(String(200))
    _intent_level = Column('intent_level', String(50))
    owned_car_ids = Column(String(200))

    address_line = Column(String(500))
    competing_car_ids = Column(String(200))
    remark = Column(String(500))
    channel = Column(String(50))
    # if channel is campaign, campaign_id can be selected from campaign list
    campaign_id = Column(BigInteger)
    is_refered = Column(Boolean, default=False)
    refered_info = Column(String(200))
    is_company = Column(Boolean, default=False)
    company_name = Column(String(200))
    defeated_reason = Column(String(500))
    sales_id = Column(BigInteger, ForeignKey('user.id'), nullable=False, index=True)

    last_reception_date = Column(DateTime)
    next_appointment_date = Column(DateTime)
    # used for query purpose for now
    last_id = ''

    birth_date = Column(Date)
    source = Column(String(20), default='isr')

    sales = relationship('User', cascade="all")

    tags = Column(String(1024))
    reassigned = Column(Boolean, default=False)

    plate_type = Column(String(200))
    record_info = Column(String(500))

    budget = Column(String(50))
    payment = Column(String(50))
    is_car_replace = Column(Boolean, default=False)
    license_loc = Column(String(50))

    addl_info = relationship('CustomerAddlInfo', uselist=False, backref="customer")

    default_status = 'draft'
    valid_status = ('draft', 'formal', 'enlist', 'ordered', 'defeated', 'duplicated', 'cancelled')
    """
    Status Explanations
    draft: customer is created with minimal information.
    formal: all required information had been collected.
    enlist: customer is being followed up. i.e. there are open appointments or receptions on customer.
    ordered: customer had made an order.
    defeated: sales has given up this customer.

    Status Transitions

    draft -> formal / defeated / invalid
    formal -> enlist / defeated / ordered
    enlist -> formal / defeated / ordered
    ordered -> enlist
    defeated -> enlist

    Status Transitions Handling
    Current implementation is not good. It can be optimised by using Signal
    """

    tbu_status = ('draft', 'formal', 'cancelled')
    """
    status to be updated/followed up
    """

    required_fields = ('name', 'mobile', 'gender', 'intent_car_ids', 'intent_level', 'channel', 'test_drive_car_ids')

    not_updatable_fields = ('id', 'status', 'tags', 'reassigned', 'created_on', 'updated_on', 'last_reception_date',
                            'next_appointment_date')

    @orm.reconstructor
    def init_on_load(self):
        super(Customer, self).init_on_load()
        self._last_sales_id = self.sales_id
        self._intent_car_ids = self.intent_car_ids
        self._test_drive_car_ids = self.test_drive_car_ids

    @property
    def respect_name(self):
        respect = u'先生' if self.gender else u'女士'

        if self.name and len(self.name) > 0 and respect not in self.name:
            return self.name + respect
        else:
            return self.name

    @property
    def gender_str(self):
        if self.gender:
            return u'男'
        else:
            return u'女'

    @property
    def intent_level(self):
        return self._intent_level

    @intent_level.setter
    def intent_level(self, intent_level):
        self._intent_level = intent_level
        if intent_level == '-100' and self.status != 'defeated':
            self.status = 'defeated'
        elif intent_level != '-100' and self.status == 'defeated':
            self.status = 'formal' if self.has_required_fields_filled() else 'draft'

    def mobile_display(self):
        if self.mobile and len(self.mobile) >= 4:
            return "*" * 7 + self.mobile[-4:]
        else:
            return ""

    def is_active(self):
        return not self.status or self.status in ('draft', 'formal', 'enlist')

    @classmethod
    def find_with_addl(cls, uid):
        customer = cls.query.filter(cls.id == uid).first()
        addl_info = CustomerAddlInfo.find_by_customer_id(customer.id)

        if not addl_info:
            addl_info = CustomerAddlInfo()

        for attr in CustomerAddlInfo.attributes_names(excludes=CustomerAddlInfo.excludes_attrs()):
            setattr(customer, attr, getattr(addl_info, attr))

        return customer

    @classmethod
    def exist_with_same_mobile(cls, store_id, mobile, exclude_customer_id=None):
        mobile = format_mobile(mobile)
        if exclude_customer_id:
            count = db.session.query(func.count(cls.id)).filter(
                and_(cls.store_id == store_id, cls.mobile == mobile, cls.id != exclude_customer_id,
                     cls.status != 'duplicated',
                     cls.status != 'cancelled')).scalar()
        else:
            count = db.session.query(func.count(cls.id)).filter(
                and_(cls.store_id == store_id, cls.mobile == mobile, cls.status != 'duplicated',
                     cls.status != 'cancelled')).scalar()
        return count > 0

    @classmethod
    def find_by_mobile_and_sales(cls, mobile, sales_id):
        mobile = format_mobile(mobile)
        return cls.query.filter(cls.sales_id == sales_id, cls.mobile == mobile, cls.status != 'cancelled').first()

    @classmethod
    def find_by_mobile(cls, store_id, mobile):
        mobile = format_mobile(mobile)
        return cls.query.filter(cls.store_id == store_id, cls.mobile == mobile, cls.status != 'cancelled').first()

    @classmethod
    def find_by_mobile_exclude(cls, store_id, mobile, exclude_customer_id):
        mobile = format_mobile(mobile)
        return cls.query.filter(cls.store_id == store_id, cls.mobile == mobile,
                                cls.id != exclude_customer_id,
                                cls.status != 'cancelled').first()

    @classmethod
    def reassign_all_of_sales_to_sales(cls, from_sales_id, to_sales_id, status):
        query = cls.query.filter(and_(cls.sales_id == from_sales_id, cls.status != 'cancelled'))

        if status:
            query = query.filter(cls.status.in_(status))

        customers = query.all()

        for customer in customers:
            customer.sales_id = to_sales_id
            customer.reassigned_silent = True

        return len(customers)

    @classmethod
    def find_all_by_sales_of_status(cls, sales_id, status):
        return cls.query.filter(and_(cls.sales_id == sales_id, cls.status.in_(status))).all()

    @classmethod
    def find_all_by_sales(cls, sales_id, page=DEFAULT_PAGE_START, per_page=DEFAULT_PAGE_SIZE):
        return cls.query.filter(cls.sales_id == sales_id).order_by(desc(cls.updated_on)).paginate(page, per_page)

    @classmethod
    def find_all_by_sales_before_sync_in_bulk(cls, sales_id, last_sync_date, bulk_size):
        query = cls.query.filter(cls.sales_id == sales_id)

        if last_sync_date:
            query = query.filter(cls.updated_on >= last_sync_date)

        return query.order_by(asc(cls.updated_on)).paginate(1, bulk_size)

    @classmethod
    def find_all_in_tbu_by_sales(cls, sales_id):
        return cls.query.filter(
            and_(cls.sales_id == sales_id, or_(cls.status.in_(cls.tbu_status), cls.reassigned == 1),
                 cls.last_reception_date != None, cls.status != 'cancelled')).order_by(
            desc(cls.updated_on)).all()

    @classmethod
    def find_all_by_store_in_status(cls, store_id, status=None, page=DEFAULT_PAGE_START, per_page=DEFAULT_PAGE_SIZE):
        query = cls.query.options(joinedload(cls.sales)).filter(cls.store_id == store_id)

        if status:
            query = query.filter(cls.status == status)

        return query.order_by(desc(cls.updated_on)).paginate(
            page, per_page)

    @classmethod
    def find_all_with_last_appt_by_query_params_in_store(cls, store_id, **kwargs):
        from application.models.appointment import Appointment
        relationship_query = db.session.query(func.max(Appointment.id).label('last_id'),
                                              Appointment.customer_id).filter(
            and_(Appointment.remark != None, Appointment.remark != u'', Appointment.store_id == store_id)).group_by(
            Appointment.customer_id).subquery()

        query = db.session.query(cls, Appointment.remark).options(joinedload(cls.sales)).outerjoin(
            relationship_query,
            cls.id == relationship_query.columns.customer_id).outerjoin(Appointment,
                                                                        relationship_query.columns.last_id ==
                                                                        Appointment.id).filter(
            and_(cls.store_id == store_id, cls.status != 'cancelled', cls.status != 'duplicated'))

        # hack to support paginate
        query.__class__ = BaseQuery

        if kwargs.get('intent_level'):
            query = query.filter(cls._intent_level == kwargs.get('intent_level'))

        if kwargs.get('intent_car_ids'):
            query = query.filter(
                functions.concat(',', cls.intent_car_ids).like('%,' + kwargs.get('intent_car_ids') + '%'))

        if kwargs.get('last_instore', None):
            if kwargs.get('last_instore') == 'none' or kwargs.get('last_instore') == '-1':
                query = query.filter(cls.last_reception_date == None)
            else:
                try:
                    days = int(kwargs.get('last_instore'))
                    last_instore_date = date.today() - timedelta(days=days)
                    query = query.filter(db.func.date(cls.last_reception_date) >= last_instore_date)
                except:
                    pass

        if kwargs.get('status'):
            query = query.filter(cls.status == kwargs.get('status'))

        if kwargs.get('keywords'):
            keywords = '%' + kwargs.get('keywords') + '%'
            query = query.filter(or_(cls.name.like(keywords), cls.mobile.like(keywords)))

        if kwargs.get('sales_id'):
            query = query.filter(cls.sales_id == int(kwargs.get('sales_id')))

        page = kwargs.get('page', DEFAULT_PAGE_START)
        per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

        sortable_fields = ('sales_id', 'status', '_intent_level', 'last_reception_date')
        query_order_fixed = SortMixin.add_order_query(query, cls, sortable_fields, kwargs)
        return query_order_fixed.paginate(page, per_page)

    @classmethod
    def find_by_mobile_with_sales_in_store(cls, mobile, store_id):
        mobile = format_mobile(mobile)
        return cls.query.options(joinedload(cls.sales)).filter(
            and_(cls.mobile == mobile, cls.status != 'cancelled',
                 cls.status != 'duplicated',
                 cls.store_id == store_id)).order_by(desc(cls.updated_on)).first()

    @classmethod
    def filter_not_updatable_fields(cls, data_dict):
        for field in Customer.not_updatable_fields:
            data_dict.pop(field, None)

    @classmethod
    def is_defeated(cls, data):
        if '000' == data.get('mobile', None):
            return True
        elif '-100' == data.get('intent_level'):
            return True
        else:
            return False

    @classmethod
    def count_test_drive_customers_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated', cls.test_drive_car_ids != None,
                 cls.test_drive_car_ids != '', cls.test_drive_car_ids != 'none')).scalar()

    @classmethod
    def count_test_drive_customers_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(cls.sales_id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated', cls.test_drive_car_ids != None,
                 cls.test_drive_car_ids != '', cls.last_reception_date != None,
                 cls.test_drive_car_ids != 'none')).group_by(cls.sales_id).all()

    @classmethod
    def count_ordered_test_drive_customers_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status == 'ordered', cls.test_drive_car_ids != None, cls.test_drive_car_ids != '',
                 cls.test_drive_car_ids != 'none')).scalar()

    @classmethod
    def count_all_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated')).scalar()

    @classmethod
    def count_all_formal_between_dates_in_store(cls, start, end, store_id):
        # TODO: add is_formal field
        return db.session.query(func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated', func.length(cls.mobile) >= 11)).scalar()

    @classmethod
    def count_all_ordered_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(distinct(cls.id))).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status == 'ordered')).group_by(cls.sales_id).group_by(cls.sales_id).all()

    @classmethod
    def count_all_by_sales_between_dates_in_store(cls, start, end, store_id):
        return db.session.query(cls.sales_id, func.count(cls.sales_id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated', cls.last_reception_date != None)).group_by(
            cls.sales_id).all()

    @classmethod
    def count_all_formal_by_sales_between_dates_in_store(cls, start, end, store_id):
        # TODO: add is_formal field
        return db.session.query(cls.sales_id, func.count(cls.id)).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated', cls.last_reception_date != None,
                 func.length(cls.mobile) >= 11)).group_by(cls.sales_id).all()

    @classmethod
    def count_all_new_active_by_date_in_store(cls, date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == date, cls.store_id == store_id,
                 or_(cls.status == 'formal', cls.status == 'enlist'), cls.last_reception_date != None,
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_all_new_active_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 or_(cls.status == 'formal', cls.status == 'enlist'), cls.last_reception_date != None,
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_all_imported_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) >= start, db.func.date(cls.created_on) <= end, cls.store_id == store_id,
                 cls.status != 'cancelled', cls.status != 'duplicated', cls.source == 'manual',
                 User.username != u'管理员')).scalar()

    @classmethod
    def count_all_imported_by_date_in_store(cls, p_date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.created_on) == p_date, cls.store_id == store_id, cls.status != 'cancelled',
                 cls.status != 'duplicated', cls.source == 'manual', User.username != u'管理员')).scalar()

    @classmethod
    def count_all_draft_rx_between_date_in_store(cls, start, end, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.last_reception_date) >= start, db.func.date(cls.last_reception_date) <= end,
                 cls.store_id == store_id, cls.status == 'draft', User.username != u'管理员')).scalar()

    @classmethod
    def count_all_draft_rx_by_date_in_store(cls, p_date, store_id):
        from application.models.user import User
        return db.session.query(func.count(cls.id)).join(User, cls.sales_id == User.id).filter(
            and_(db.func.date(cls.last_reception_date) == p_date, cls.store_id == store_id, cls.status == 'draft',
                 cls.source == 'isr', User.username != u'管理员')).scalar()

    @classmethod
    def cancel_not_filed_customers_by_sales_id(cls, sales_id):
        return db.session.query(Customer).filter(
            db.and_(Customer.sales_id == sales_id, Customer.status != 'cancelled',
                    func.length(Customer.mobile) < 11)).update(
            {'status': 'cancelled', '_last_status_changer': 'system', '_last_status_change_date': datetime.now()},
            synchronize_session=False)

    @classmethod
    def find_all_defeated_in_store_by_last_reception_date(cls, store_id, from_date, to_date):
        query = cls.query.filter(cls.store_id == store_id).filter(cls.status == 'defeated')
        if from_date:
            query = query.filter(db.func.date(cls.last_reception_date) >= from_date)

        if to_date:
            query = query.filter(db.func.date(cls.last_reception_date) <= to_date)

        return query.all()

    def has_required_fields_filled(self):
        for field in self.required_fields:
            value = getattr(self, field, None)
            if value is None:
                return False
            elif isinstance(value, str) or isinstance(value, unicode):
                if not value.strip():
                    return False

        return True

    # state transition methods. could be improve by use a state machine or sth else.
    def defeated(self, reason=''):
        self.status = 'defeated'
        self.intent_level = '-100'
        self.defeated_reason = reason

        # cancel all active appointments and receptions
        from application.models.appointment import Appointment
        from application.models.reception import Reception
        Appointment.cancel_all_for_sales_customer(self.sales_id, self.id, self.status + ': ' + reason)
        Reception.complete_all_for_sales_customer(self.sales_id, self.id, self.status + ': ' + reason)

    def enlist(self):
        if self.status == 'ordered':
            return

        if self.status == 'defeated':
            self.status = 'formal' if self.has_required_fields_filled() else 'draft'

        if self.has_required_fields_filled():
            self.status = 'enlist'

    def reset_status(self):
        from application.models.appointment import Appointment

        if self.status == 'defeated':
            return
        elif len(Order.find_all_by_customer_sales(self.id, self.sales_id)):
            self.status = 'ordered'
            return
        elif Appointment.exist_opened_of_sales_customer(self.sales_id, self.id):
            self.status = 'enlist'
            return
        elif self.has_required_fields_filled():
            self.status = 'formal'
            return
        else:
            self.status = 'draft'
            return

    def formal(self):
        if self.status == 'draft' and self.has_required_fields_filled():
            self.status = 'formal'

    def is_sales_changed(self):
        if hasattr(self, '_last_sales_id'):
            return str(self._last_sales_id) != str(self.sales_id)
        else:
            return self.sales_id is not None

    def is_intent_cars_changed(self):
        if hasattr(self, '_intent_car_ids'):
            return unicode(self._intent_car_ids) != unicode(self.intent_car_ids)
        else:
            return self.intent_car_ids is not None

    def is_test_drive_cars_changed(self):
        if hasattr(self, '_test_drive_car_ids'):
            return unicode(self._test_drive_car_ids) != unicode(self.test_drive_car_ids)
        else:
            return self.test_drive_car_ids is not None

    def add_tag(self, tag):
        target_tag = tag + ','
        if self.tags.count(target_tag) > 0:
            return
        self.tags += target_tag

    def reassign(self, new_sales_id):
        from application.models.appointment import Appointment
        if not new_sales_id or self.sales_id == new_sales_id:
            return

        Appointment.cancel_all_for_sales_customer(self.sales_id, self.id, u'重新分配客户')
        self.reassigned = True
        self.sales_id = new_sales_id


class CustomerAddlInfo(db.Model, BaseMixin):
    __tablename__ = 'customer_addl_info'

    customer_id = Column(BigInteger, ForeignKey('customer.id'))

    addl_contact_info = Column(String(200))
    contact_time = Column(String(100))
    industry = Column(String(100))
    hobby = Column(String(100))
    traits = Column(String(100))
    car_service_life = Column(String(50))
    car_mileage = Column(String(50))
    has_used_car_assessed = Column(Boolean)
    used_car_value = Column(String(50))

    district = Column(String(100))
    dealership = Column(String(50))
    purpose = Column(String(50))
    actual_driver = Column(String(50))
    drive_loc = Column(String(50))

    trans_type = Column(String(50))

    @classmethod
    def find_by_customer_id(cls, customer_id):
        return cls.query.filter(cls.customer_id == customer_id).first()

    @classmethod
    def excludes_attrs(cls):
        excludes = [item for item in BaseMixin.attributes_names()]
        excludes.append('customer')
        return excludes


@event.listens_for(Customer, 'before_update')
@event.listens_for(Customer, 'before_insert')
def validate(mapper, connection, target):
    if target.mobile and '000' != target.mobile:
        if not validate_mobile(target.mobile):
            raise InvalidMobileNumberExcetpion(gettext(u'invalid mobile number %(num)s', num=target.mobile))
        elif target.status != 'cancelled' and target.status != 'duplicated':
            existing_customer = Customer.find_by_mobile_exclude(target.store_id, target.mobile, target.id)
            from application.api.viewhelper import handle_no_rx_customer
            existing_customer = handle_no_rx_customer(existing_customer)
            if existing_customer:
                if target.sales_id == existing_customer.sales_id:
                    raise DuplicatedCustomerException(gettext(u'The mobile is the same as customer %(name)s',
                                                              name=existing_customer.respect_name),
                                                      existing_customer_id=existing_customer.id)
                else:
                    raise NoPermissionOnCustomerException(existing_customer,
                                                          gettext(u'The mobile belongs to other sales\' customer'))


def validate_required_fields(data_dict):
    if data_dict and data_dict.get('required_validation'):
        data_dict.pop('required_validation')

        for field in Customer.required_fields:
            value = data_dict.get(field, None)
            if value is None:
                return False
            elif isinstance(value, str) or isinstance(value, unicode):
                if not value.strip():
                    return False

    return True


@event.listens_for(Customer, 'before_update')
def track_sales_change(mapper, connection, target):
    if target.is_sales_changed():
        tracker = dict()
        tracker['from_sales_id'] = target._last_sales_id
        tracker['to_sales_id'] = target.sales_id
        tracker['customer_id'] = target.id

        now = datetime.now()
        tracker['created_on'] = now

        if not hasattr(target, 'reassigned_silent'):
            target.reassigned = True
        target.reset_status()

        connection.execute(SalesTracker.__table__.insert(), **tracker)


@event.listens_for(Customer, 'before_update')
@event.listens_for(Customer, 'before_insert')
def clean_mobile(mapper, connection, target):
    target.mobile = format_mobile(target.mobile)


@event.listens_for(Customer, 'before_update')
@event.listens_for(Customer, 'before_insert')
def update_car_series(mapper, connection, target):
    if target.is_intent_cars_changed():
        target.intent_car_series = lookup_sections_by_codes(target.store_id, target.intent_car_ids, 'intent-car')


def track_drive_record_changes(test_drive_car, customer):
    now = datetime.now()
    drive_record = dict()
    drive_record['store_id'] = customer.store_id
    drive_record['customer_id'] = customer.id
    drive_record['sales_id'] = customer.sales_id
    drive_record['start'] = now
    drive_record['end'] = now
    drive_record['duration'] = 0
    drive_record['sales_id'] = customer.sales_id
    drive_record['car_code'] = test_drive_car

    return drive_record


@event.listens_for(Customer, 'before_update')
def track_test_drive_record_on_update(mapper, connection, target):
    if target.is_test_drive_cars_changed():
        if target.test_drive_car_ids != 'none':
            if hasattr(target, '_test_drive_car_ids') and target._test_drive_car_ids:
                existing_cars = set(target._test_drive_car_ids.split(','))
            else:
                existing_cars = set()

            cars = set(target.test_drive_car_ids.split(','))
            changes = cars - existing_cars

            for change in changes:
                connection.execute(DriveRecord.__table__.insert(), **track_drive_record_changes(change, target))
        else:
            connection.execute(DriveRecord.__table__.delete().where(
                and_(DriveRecord.store_id == target.store_id, DriveRecord.customer_id == target.id,
                     DriveRecord.sales_id == target.sales_id,
                     db.func.date(DriveRecord.start) == datetime.today().date())))


@event.listens_for(Customer, 'after_insert')
def track_test_drive_record_after_insert(mapper, connection, target):
    if target.test_drive_car_ids and target.test_drive_car_ids != 'none':
        cars = set(target.test_drive_car_ids.split(','))

        for change in cars:
            connection.execute(DriveRecord.__table__.insert(), **track_drive_record_changes(change, target))


def lookup_sections_by_codes(store_id, codes, lookup_name):
    from application.models.lookup import LookupValue
    lookupvalue_dict = LookupValue.find_all_in_dict_by_lookup_name_of_store_from_cache(long(store_id), lookup_name)

    if codes and codes.strip() and lookupvalue_dict and len(lookupvalue_dict) > 0:
        codes_arr = codes.split(',')
        sections = set()

        for code in codes_arr:
            lookupvalue = lookupvalue_dict.get(code, None)
            if lookupvalue and lookupvalue.section:
                sections.add(lookupvalue.section)
        if len(sections) > 0:
            return ','.join(sections)

    return ''
