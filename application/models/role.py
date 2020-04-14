#coding: utf-8
from sqlalchemy import Column
from sqlalchemy.types import String

from .base import Model, BaseMixin, get_or_create


class Role(Model, BaseMixin):
    '''
    用户角色表
    '''
    __tablename__ = 'role'
    title = Column(String(100), unique=True, index=True)

    @classmethod
    def find_by_title(cls, title):
        return cls.query.filter(cls.title == title).first()

    @classmethod
    def from_json(cls, data):
        title = data['title']
        instance, _ = get_or_create(cls, title=title)
        return instance

    @classmethod
    def from_title(cls, title):
        instance, _ = get_or_create(cls, title=title)
        return instance