# coding: utf-8

from sqlalchemy import Column
from sqlalchemy.types import String, Boolean, Integer

from application.models.base import db, BaseMixin, StoreMixin
from application.models.user import User


class Userold(db.Model, BaseMixin, StoreMixin):
    __tablename__ = 'user_old'

    username = Column(String(50))
    email = Column(String(50), unique=True)
    title = Column(String(200))
    storename = Column(String(200))
    type = Column(Integer)
    avatar = Column(String(200), default='default.png')
    _active = Column('active', Boolean)
    roles = Column(String(200))


def user_data_to_ucenter():
    db.engine.execute("ALTER TABLE %s RENAME TO %s " % (User.__tablename__, Userold.__tablename__))
    db.create_all()

    user_olds = Userold.query.all()
    for user_old in user_olds:
        user = User()
        user.id = user_old.id
        user._active = user_old._active
        user.username = user_old.username
        user.email = user_old.email
        user.title= user_old.title
        user.avatar = user_old.avatar
        user.created_on = user_old.created_on
        user.updated_on = user_old.updated_on
        user.created_by = user_old.created_by
        user.updated_by = user_old.updated_by
        db.session.add(user)

        store_id = user_old.store_id
        store_name = user_old.storename
        roles = user_old.roles
        type = user_old.type
        user.update_permission_auth(store_id, store_name, type, roles)
    db.session.commit()













