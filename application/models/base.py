# -*- coding: utf-8 -*-
from datetime import datetime

from flask.ext.sqlalchemy import SQLAlchemy, Model, _BoundDeclarativeMeta, _QueryProperty
from sqlalchemy import Column, BigInteger, DateTime, desc, String, and_, Boolean
from sqlalchemy.ext.declarative import declarative_base

from application.pagination import DEFAULT_PAGE_START, DEFAULT_PAGE_SIZE


def _customized_constructor(self, **kwargs):
    cls_ = type(self)
    for k in kwargs:
        if hasattr(cls_, k):
            try:
                setattr(self, k, kwargs[k])
            except AttributeError:
                pass


_customized_constructor.__name__ = '__init__'


class CustomizedSQLAlchemy(SQLAlchemy):
    def make_declarative_base(self, metadata=None):
        """Hack to pass customized constructor"""
        base = declarative_base(cls=Model, name='Model',
                                metaclass=_BoundDeclarativeMeta, constructor=_customized_constructor)
        base.query = _QueryProperty(self)
        return base


db = CustomizedSQLAlchemy()

Model = db.Model

MODULE_BASE = 'application.models.'


# get user id from context (flask global user object)
def get_user_id():
    try:
        from flask import g
        return g.user.id if hasattr(g, 'user') else None
    except:
        return None


def get_or_create(model, **kwargs):
    '''
    copy from ucenter
    查询或者创建数据
    '''
    instance = model.query.filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        instance = model(**kwargs)
        db.session.add(instance)
        return instance, True


class BaseMixin(object):
    id = Column(BigInteger, primary_key=True)
    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(50), default=get_user_id)
    updated_by = Column(String(50), default=get_user_id, onupdate=get_user_id)

    @classmethod
    def find(cls, oid):
        return cls.query.filter(cls.id == oid).first()

    @classmethod
    def find_or_create(cls, **kwargs):
        instance = cls.query.filter_by(**kwargs).first()
        if not instance:
            instance = cls()
            db.session.add(instance)
        return instance

    @classmethod
    def find_all(cls):
        return cls.query.order_by(desc(cls.updated_on)).all()

    @classmethod
    def delete(cls, id):
        obj = cls.find(id)

        if obj:
            db.session.delete(obj)

        return obj

    @classmethod
    def attributes_names(cls, excludes=None):
        if not excludes:
            excludes = []

        for k, v in vars(cls).iteritems():
            if not k.startswith('_') and k not in excludes and not callable(v) and not isinstance(v, classmethod):
                yield k

    def save(self):
        if self.id is None:
            db.session.add(self)
        elif self not in db.session:
            db.session.merge(self)

    def save_and_flush(self):
        self.save()
        db.session.flush()

    def save_and_commit(self):
        self.save()
        db.session.commit()

    def expunge(self):
        db.session.expunge(self)


class StoreMixin(object):
    store_id = Column(BigInteger, nullable=False, index=True)

    @classmethod
    def find_by_id_and_store(cls, oid, store_id):
        return cls.query.filter(and_(cls.id == oid, cls.store_id == store_id)).first()

    @classmethod
    def find_all_by_store(cls, store_id, page=DEFAULT_PAGE_START, per_page=DEFAULT_PAGE_SIZE):
        return cls.query.filter(cls.store_id == store_id).order_by(desc(cls.updated_on)).paginate(page, per_page)

    @classmethod
    def migrate_store(cls, from_store_id, to_store_id):
        return cls.query.filter(cls.store_id == from_store_id).update({cls.store_id: to_store_id})


class ActiveMixin(object):
    _active = Column('active', Boolean, default=True)

    @classmethod
    def filter_active(cls):
        return cls._active == True

    def deactivate(self):
        self._active = False

    def activate(self):
        self._active = True

    def is_active(self):
        return self._active


class SequenceFieldMixIn(object):
    sequence_id = Column(String(100), index=True)
