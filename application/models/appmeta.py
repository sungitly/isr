# -*- coding: utf-8 -*-
from flask import g
from sqlalchemy import Column, String, Integer, desc
from sqlalchemy.orm import load_only

from application.cache import cache, LONG_CACHE
from application.models.base import db, BaseMixin

DEFAULT_DOWNLOAD_WEBSITE = "http://dl.auc2.com"


class AppMeta(db.Model, BaseMixin):
    __tablename__ = 'app'

    name = Column(String(100), unique=True)
    type = Column(String(100))
    desc = Column(String(200))
    api_key = Column(String(100), unique=True)
    secret_key = Column(String(100))
    version = Column(String(50))
    version_num = Column(Integer)
    release_note = Column(String(2000))
    download_url = Column(String(500))
    download_website = Column(String(500), default=DEFAULT_DOWNLOAD_WEBSITE)

    app_columns = (
        'id', 'name', 'type', 'desc', 'version', 'version_num', 'download_url', 'release_note', 'download_website')
    auth_column = ('name', 'api_key', 'secret_key')

    def upgrade(self, version, version_num, release_note):
        self.version = version
        self.version_num = version_num
        self.release_note = release_note

        performer = None
        if hasattr(g, 'user'):
            performer = g.user.username

        release_history = ReleaseHistory(app_name=self.name, version=version, version_num=version_num,
                                         note=release_note,
                                         created_by=performer,
                                         updated_by=performer)
        release_history.save()

    @classmethod
    def find_by_id(cls, id):
        return cls.query.options(load_only(*cls.app_columns)).filter(cls.id == id).first()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.options(load_only(*cls.app_columns)).filter(cls.name == name).first()

    @classmethod
    def find_all_auth_info(cls):
        return cls.query.options(load_only(*cls.auth_column)).all()

    @classmethod
    def find_all(cls):
        return cls.query.options(load_only(*cls.app_columns)).all()

    @staticmethod
    @cache.memoize(timeout=LONG_CACHE)
    def find_all_from_cache():
        app_auth_infos = AppMeta.find_all_auth_info()

        return {auth.api_key: auth for auth in app_auth_infos}

    @staticmethod
    def find_by_api_key_from_cache(api_key):
        return AppMeta.find_all_from_cache().get(api_key, None)


class ReleaseHistory(db.Model, BaseMixin):
    __tablename__ = 'release_history'

    app_name = Column(String(100), nullable=False)
    version = Column(String(50))
    version_num = Column(Integer)
    note = Column(String(2000))

    @classmethod
    def find_all_by_app_name(cls, app_name):
        return cls.query.filter(cls.app_name == app_name).order_by(desc(cls.created_on)).all()
