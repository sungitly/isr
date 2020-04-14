# -*- coding: utf-8 -*-
from datetime import date, timedelta

from application.exceptions import ErrorDetail, ValidationException
from application.forms.mixins import SortMixin
from application.models.base import db, BaseMixin, StoreMixin
from application.pagination import DEFAULT_PAGE_START, DEFAULT_PAGE_SIZE
from application.utils import is_valid_date
from dateutil.parser import parse
from flask.ext.babel import gettext
from sqlalchemy import Column, String, Text, Date, and_, Boolean, event, or_, asc
from wtforms.widgets import html_params


class Campaign(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'campaign'

    title = Column(String(200), nullable=False)
    content = Column(Text)
    related_cars = Column(String(200))
    start = Column(Date, nullable=False)
    end = Column(Date, nullable=False)
    _notify_date = Column('notify_date', Date, nullable=False)
    notify_sent = Column(Boolean, default=False)
    source = Column(String(20), default='isr')

    @property
    def notify_date(self):
        return self._notify_date

    @notify_date.setter
    def notify_date(self, notify_date):
        if isinstance(notify_date, date):
            self._notify_date = notify_date
        else:
            self._notify_date = parse(notify_date).date()

    def is_active(self):
        today = date.today()
        return self.start <= today <= self.end

    @classmethod
    def find_all_active_by_store(cls, store_id, page=DEFAULT_PAGE_START, per_page=DEFAULT_PAGE_SIZE):
        today = date.today()
        return cls.query.filter(and_(cls.start <= today, cls.end >= today, cls.store_id == store_id)).paginate(page,
                                                                                                               per_page)

    @classmethod
    def find_all_by_store_in_recent_days(cls, store_id, days):
        today = date.today()
        target_day = today + timedelta(days=days)

        return cls.query.filter(and_(cls.store_id == store_id, cls.start <= target_day, cls.end >= today)).all()

    @classmethod
    def find_all_by_store_in_recent_days_and_keywords(cls, store_id, **kwargs):
        today = date.today()
        filters = [cls.store_id == store_id]
        days = kwargs.get('days', None)
        if days:
            target_day = today + timedelta(days=days)
            filters.append(cls.start <= target_day)

        active = kwargs.get('active', False)
        if active:
            filters.append(cls.end >= today)

        keywords = kwargs.get('keywords', None)
        if keywords:
            filters.append(or_(cls.title.like('%' + keywords + '%'), cls.content.like('%' + keywords + '%')))

        page = kwargs.get('page', DEFAULT_PAGE_START)
        per_page = kwargs.get('per_page', DEFAULT_PAGE_SIZE)

        criteria = and_(*filters)
        query = cls.query.filter(criteria)

        sortable_fields = ('start', 'end', 'notify_date')
        query_order_fixed = SortMixin.add_order_query(query, cls, sortable_fields, kwargs)
        return query_order_fixed.paginate(page, per_page)

    @classmethod
    def find_all_to_be_notified_today_by_store(cls, store_id):
        return cls.query.filter(
            and_(cls._notify_date == date.today(), cls.store_id == store_id, cls.notify_sent == 0)).all()

    @classmethod
    def find_all_to_be_notified_today(cls):
        return cls.query.filter(and_(cls._notify_date == date.today(), cls.notify_sent == 0)).all()

    def validate(self):
        errors = []
        if not self.title:
            error = ErrorDetail(domain='title', reason='Required Field',
                                message=gettext('%(field)s is required', field='title'))
            errors.append(error)

        if not is_valid_date(self.start):
            error = ErrorDetail(domain='start', reason='Invalid Date Field',
                                message=gettext('%(field)s:%(value)s is not a valid date', field='start',
                                                value=self.start))
            errors.append(error)

        if not is_valid_date(self.end):
            error = ErrorDetail(domain='end', reason='Invalid Date Field',
                                message=gettext('%(field)s:%(value)s is not a valid date', field='end',
                                                value=self.end))
            errors.append(error)

        if len(errors):
            raise ValidationException(errors=errors)


@event.listens_for(Campaign, 'before_update')
@event.listens_for(Campaign, 'before_insert')
def validate_campaign(mapper, connection, target):
    target.validate()


def push_msg_for_campaign_creation(campaign):
    msg = dict()
    title = gettext('campaign created')
    msg['title'] = title if not isinstance(title, unicode) else title.encode('utf-8')
    msg['body'] = campaign.title if not isinstance(campaign.title, unicode) else campaign.title.encode('utf-8')
    return msg


def push_msg_for_campaign_update(campaign):
    msg = dict()
    title = gettext('campaign updated')
    msg['title'] = title if not isinstance(title, unicode) else title.encode('utf-8')
    msg['body'] = campaign.title if not isinstance(campaign.title, unicode) else campaign.title.encode('utf-8')
    return msg