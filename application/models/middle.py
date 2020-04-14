#coding: utf-8
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import BigInteger, String, Text
from sqlalchemy.orm import relationship

from .base import Model, BaseMixin, MODULE_BASE, get_or_create, db
from .store import Store
from .role import Role


# class UserStore(BaseMixin, Model):
#     '''
#     user和store关系
#     '''
#     __tablename__ = 'user_store'
#     user_id = Column(BigInteger, ForeignKey('user.id'), index=True)
#     store_id = Column(BigInteger, ForeignKey('store.id'), index=True)
#     store = relationship(MODULE_BASE+'store.Store', backref='user_assocs')
#
#
# class UserRole(BaseMixin, Model):
#     '''
#     user和role关系
#     '''
#     __tablename__ = 'user_role'
#     user_id = Column(BigInteger, ForeignKey('user.id'), index=True)
#     role_id = Column(BigInteger, ForeignKey('role.id'), index=True)
#     role = relationship(MODULE_BASE+'role.Role', backref='user_assocs')


class StoreUserRoleScope(BaseMixin, Model):
    '''
    copy from ucenter
    '''
    __tablename__ = 'store_user_role_scope'

    user_id = Column(BigInteger, ForeignKey('user.id'), index=True)
    store_id = Column(BigInteger, ForeignKey('store.id'), index=True)
    role_id = Column(BigInteger, ForeignKey('role.id'), index=True)
    scope_type = Column(String(50), nullable=False)
    user_ids = Column(Text)  #管理的用户 以,分割

    user = relationship(MODULE_BASE+'user.User', backref='store_user_role_scopes')
    store = relationship(MODULE_BASE+'store.Store', backref='store_user_role_scopes')
    role = relationship(MODULE_BASE+'role.Role', backref='store_user_role_scopes')
    '''
    scope_type: 可选项
        individual: 不可以管理
        store: 可以管理店面
        peoples: 可以管理用户, user_ids中类容
    '''
    SCORE_TYPE_INDIVIDUAL = 'individual'
    SCORE_TYPE_STORE = 'store'
    SCORE_TYPE_PEOPLES = 'peoples'

    @classmethod
    def from_auth(cls, user, store_id, store_name, role_title, scope_type):
        store = Store.from_id_name(store_id, store_name)
        role = Role.from_title(role_title)
        if store.id and role.id and user.id:
            instance, _ = get_or_create(cls, user_id=user.id, store_id=store.id, role_id=role.id)
        else:
            instance = cls()
        instance.scope_type = scope_type
        user.store_user_role_scopes.append(instance)
        store.store_user_role_scopes.append(instance)
        role.store_user_role_scopes.append(instance)
        db.session.add_all([user, store, role, instance])

    def to_json(self):
        json_store_user_role_scope = {
            'store': self.store.to_json(['id', 'sequence_id', 'name']),
            'role': self.role.to_json(),
            'scope_type': self.scope_type,
            'user_ids': self.user_ids
        }
        return json_store_user_role_scope

    @classmethod
    def drop_by_userid(cls, userid):
        '''
        根据用户id删除权限
        '''
        db.session.query(cls)\
            .filter(cls.user_id == userid) \
            .delete()

    @classmethod
    def from_json(cls, user, data):
        store_data = data['store']
        role_data = data['role']
        scope_type = data['scope_type']
        user_ids = data['user_ids']

        store = Store.from_json(store_data)
        role = Role.from_json(role_data)
        if store.id and role.id and user.id:
            instance, _ = get_or_create(cls, user_id=user.id, store_id=store.id, role_id=role.id)
        else:
            instance = cls()
        instance.user_ids = user_ids
        instance.scope_type = scope_type

        user.store_user_role_scopes.append(instance)
        store.store_user_role_scopes.append(instance)
        role.store_user_role_scopes.append(instance)

        db.session.add_all([user, store, role, instance])