# -*- coding: utf-8 -*-
from datetime import datetime

from flask import g
from sqlalchemy import Column, String, BigInteger, Integer, event, DateTime, and_, desc
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declared_attr
from .base import db


class StatusTracker(db.Model):
    __tablename__ = 'status_tracker'

    id = Column(BigInteger, primary_key=True)
    model = Column(String(100), nullable=False)
    model_id = Column(BigInteger)
    from_status = Column(String(50), default="None", nullable=False)
    to_status = Column(String(50), default="None", nullable=False)
    remark = Column(String(100))
    parent_id = Column(BigInteger)
    # in seconds
    duration_since_last_change = Column(Integer, default=0)
    created_on = Column(DateTime)
    created_by = Column(String(50))

    @classmethod
    def find_last_tracker_by_model_id_with_to_status(cls, model_name, model_id, to_status):
        return cls.query.filter(
                and_(cls.model == model_name, cls.model_id == model_id, cls.to_status == to_status)).order_by(
                desc(cls.created_on)).first()


# noinspection PyAttributeOutsideInit
class StatusTrackerMixin(object):
    default_status = 'none'
    """
    default_status will be used as the default value of status column. subclass can override this attribute to provide
    a default value for status column
    """

    # noinspection PyMethodParameters
    @declared_attr
    def status(cls):
        event.listen(cls, 'before_insert', init_tracker_before_insert)
        event.listen(cls, 'before_update', update_tracker_before_update)
        return Column('status', String(50), default=cls.default_status, nullable=False)

    _last_tracker_id = Column('last_tracker_id', BigInteger)
    _last_status_change_date = Column('last_status_change_on', DateTime)
    _last_status_changer = Column('last_status_changer', String(50))

    @orm.reconstructor
    def init_on_load(self):
        self._last_status = self.status
        if not hasattr(self, '_status_change_remark'):
            self._status_change_remark = ''
        if not hasattr(self, '_last_status_changer'):
            self._last_status_changer = ''

    @staticmethod
    def validate_status(status):
        return True

    @staticmethod
    def validate_status_transition(from_status, to_status):
        return True

    def is_status_changed(self):
        return self.status != self._last_status


# noinspection PyTypeChecker
def init_tracker_before_insert(mapper, connection, target):
    if not isinstance(target, StatusTrackerMixin):
        return

    create_tracker(connection, target)


# noinspection PyProtectedMember,PyTypeChecker
def update_tracker_before_update(mapper, connection, target):
    if not isinstance(target, StatusTrackerMixin):
        return

    if not target.is_status_changed():
        return

    if target._last_tracker_id is None:
        return

    create_tracker(connection, target)


# noinspection PyProtectedMember
def create_tracker(connection, obj_with_status_mixin):
    # Can not track status change if obj is not StatusTrackerMixin instance or do not have an id
    if not hasattr(obj_with_status_mixin, 'id') or not isinstance(obj_with_status_mixin, StatusTrackerMixin):
        return

    tracker = dict()
    tracker['model'] = obj_with_status_mixin.__class__.__name__
    tracker['model_id'] = obj_with_status_mixin.id

    if hasattr(obj_with_status_mixin, '_last_status') and obj_with_status_mixin._last_status:
        tracker['from_status'] = obj_with_status_mixin._last_status

    if obj_with_status_mixin.status is None:
        tracker['to_status'] = obj_with_status_mixin.default_status
    else:
        tracker['to_status'] = obj_with_status_mixin.status

    if obj_with_status_mixin._last_tracker_id:
        tracker['parent_id'] = obj_with_status_mixin._last_tracker_id

    if hasattr(obj_with_status_mixin, '_status_change_remark') and obj_with_status_mixin._status_change_remark:
        tracker['remark'] = obj_with_status_mixin._status_change_remark

    now = datetime.now()
    tracker['created_on'] = now

    if hasattr(g, 'user') and g.user:
        tracker['created_by'] = g.user.id

    if obj_with_status_mixin._last_status_change_date:
        tracker['duration_since_last_change'] = (now - obj_with_status_mixin._last_status_change_date).seconds

    obj_with_status_mixin._last_status_change_date = now

    result = connection.execute(StatusTracker.__table__.insert(), **tracker)

    if len(result.inserted_primary_key) > 0:
        obj_with_status_mixin._last_tracker_id = result.inserted_primary_key[0]
